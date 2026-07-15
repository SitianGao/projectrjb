"""
学习路径规划业务逻辑层 —— API 与 PlannerAgent / DB 的桥梁。

职责：
- 管理 LearningPath 的 CRUD
- 调度 PlannerAgent 进行流式/非流式路径生成
- 将 Agent 输出持久化到数据库
"""
import json
import logging
import threading
import uuid
from typing import Any, AsyncIterator, Dict, Optional

from sqlalchemy.orm import Session

from config import PROFILE_READY_THRESHOLD
from api.response import sse_done, sse_error
from models.learning_path import LearningPath

logger = logging.getLogger(__name__)


class PlannerService:
    """学习路径规划业务服务"""

    def __init__(self, planner_agent, db_session_factory, profile_service):
        """
        Args:
            planner_agent: PlannerAgent 实例
            db_session_factory: get_db 生成器工厂（用于 FastAPI Depends）
            profile_service: ProfileService 实例（用于获取学生画像）
        """
        self.agent = planner_agent
        self.db_session_factory = db_session_factory
        self.profile_service = profile_service
        self._generation_lock = threading.Lock()
        self._generating_students: set[str] = set()

    # ── LearningPath CRUD ──────────────────────────────────────

    def get_current_path(self, db: Session, student_id: str) -> Optional[Dict]:
        """获取学生当前激活的学习路径（返回 dict 供前端展示）。"""
        path = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == student_id,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.version.desc())
            .first()
        )
        if not path:
            return None
        return self._path_to_dict(path)

    def get_path_history(self, db: Session, student_id: str) -> list:
        """获取学生学习路径历史版本列表。"""
        paths = (
            db.query(LearningPath)
            .filter(LearningPath.student_id == student_id)
            .order_by(LearningPath.version.asc())
            .all()
        )
        return [self._path_to_dict(p) for p in paths]

    def save_path(
        self,
        db: Session,
        student_id: str,
        path_data: Dict,
    ) -> LearningPath:
        """保存新的学习路径版本。旧 active 路径标记为 superseded。"""
        # 将旧 active 路径标记为 superseded
        old_active = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == student_id,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.version.desc())
            .all()
        )
        for old in old_active:
            old.status = "superseded"

        # 确定新版本号
        latest = (
            db.query(LearningPath)
            .filter(LearningPath.student_id == student_id)
            .order_by(LearningPath.version.desc())
            .first()
        )
        new_version = (latest.version + 1) if latest else 1

        record = LearningPath(
            id=str(uuid.uuid4()),
            student_id=student_id,
            version=new_version,
            goal=path_data.get("goal", ""),
            stages=json.dumps(path_data.get("stages", []), ensure_ascii=False),
            current_stage=path_data.get("current_stage", 1),
            status="active",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(f"学习路径已保存: student={student_id} v{new_version}")
        return record

    # ── SSE 流式路径生成 ───────────────────────────────────────

    async def generate_stream(
        self,
        db: Session,
        student_id: str,
        goal: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        流式生成学习路径 —— 获取画像 → 调用 PlannerAgent.chat() → 持久化。

        产出 SSE 事件流：
            data: {"type":"start","message":"..."}
            data: {"type":"delta","content":"..."}
            data: {"type":"data","data":{...}}
            data: {"type":"error","code":"...","message":"..."}
            data: {"type":"done"}
        """
        yield f'data: {{"type":"start","message":"开始检查学生画像和学习目标"}}\n\n'

        if not self._claim_generation(student_id):
            yield sse_error("CONFLICT", "该学生的学习路径正在生成，请勿重复提交")
            yield sse_done()
            return

        try:
            # 1. Always use the latest persisted profile. Path generation is a
            # user-confirmed next step and is never started by profile chat.
            profile = self.profile_service.get_profile(db, student_id)
            if not profile:
                yield sse_error("PROFILE_NOT_FOUND", "请先完成学生画像构建")
                yield sse_done()
                return

            completeness = _as_float(profile.get("completeness"), 0.0)
            if completeness < PROFILE_READY_THRESHOLD:
                yield sse_error(
                    "PLANNER_GENERATE_FAILED",
                    f"学生画像完整度为 {completeness:.0%}，达到 "
                    f"{PROFILE_READY_THRESHOLD:.0%} 后才能生成学习路径",
                )
                yield sse_done()
                return

            resolved_goal = _resolve_goal(profile, goal)
            if not resolved_goal:
                yield sse_error(
                    "PLANNER_GENERATE_FAILED",
                    "学生画像缺少学习目标，请先补充 learning_goal",
                )
                yield sse_done()
                return

            yield f'data: {{"type":"progress","progress":20,"message":"画像读取完成，开始生成个性化学习路径"}}\n\n'

            raw = await self._generate_with_agent(profile, resolved_goal)
            if isinstance(raw, str) and raw.strip():
                yield _sse_event("delta", content=raw)

            path_data = _normalize_path_result(raw, resolved_goal)
            record = self.save_path(db, student_id, path_data)
            saved = self._path_to_dict(record)
            yield _sse_event("progress", progress=90, message="学习路径已保存")
            yield _sse_event("data", data=saved)
            yield sse_done()
            logger.info("路径已自动持久化: student=%s path=%s", student_id, record.id)
        except Exception as exc:
            db.rollback()
            logger.exception("学习路径生成失败: student=%s", student_id)
            yield sse_error("PLANNER_GENERATE_FAILED", str(exc) or "学习路径生成失败")
            yield sse_done()
        finally:
            self._release_generation(student_id)

    # ── 非流式路径生成（供编排器使用） ───────────────────────────

    async def build_path(
        self,
        db: Session,
        student_id: str,
        goal: Optional[str] = None,
        current_path: Optional[Dict] = None,
        evaluation_feedback: Optional[Dict] = None,
    ) -> Dict:
        """非流式路径生成，返回完整 dict 并持久化。"""
        profile = self.profile_service.get_profile(db, student_id)
        if not profile:
            raise ValueError("请先完成学生画像构建")

        completeness = _as_float(profile.get("completeness"), 0.0)
        if completeness < PROFILE_READY_THRESHOLD:
            raise ValueError(
                f"学生画像完整度不足 {PROFILE_READY_THRESHOLD:.0%}，不能生成学习路径"
            )

        resolved_goal = _resolve_goal(profile, goal)
        if not resolved_goal:
            raise ValueError("学生画像缺少学习目标")

        raw = await self._generate_with_agent(profile, resolved_goal)
        result = _normalize_path_result(raw, resolved_goal)
        record = self.save_path(db, student_id, result)
        return self._path_to_dict(record)

    # ── 工具方法 ─────────────────────────────────────────────

    async def _generate_with_agent(self, profile: Dict, goal: str) -> Any:
        """Adapt the service to the frozen PlannerAgent contract."""
        if not self.agent:
            raise RuntimeError("PlannerAgent 未配置")
        if hasattr(self.agent, "generate_plan"):
            return await self.agent.generate_plan(
                profile=profile,
                goal_override=goal,
            )
        if hasattr(self.agent, "build_path"):
            return await self.agent.build_path(
                student_id=profile.get("student_id", ""),
                profile=profile,
                goal=goal,
                current_path=None,
                evaluation_feedback=None,
            )
        raise RuntimeError("PlannerAgent 缺少 generate_plan/build_path 方法")

    def _claim_generation(self, student_id: str) -> bool:
        with self._generation_lock:
            if student_id in self._generating_students:
                return False
            self._generating_students.add(student_id)
            return True

    def _release_generation(self, student_id: str) -> None:
        with self._generation_lock:
            self._generating_students.discard(student_id)

    @staticmethod
    def _path_to_dict(path: LearningPath) -> Dict:
        """将 ORM 对象转为前端友好的 dict。"""
        stages = _safe_json_loads(path.stages, [])
        total_days = sum(s.get("estimated_days", 0) for s in stages)
        return {
            "id": path.id,
            "student_id": path.student_id,
            "version": path.version,
            "goal": path.goal,
            "stages": stages,
            "current_stage": path.current_stage,
            "status": path.status,
            "estimated_days": total_days or None,
            "total_estimated_days": total_days or None,
            "created_at": path.created_at.isoformat() if path.created_at else None,
            "updated_at": path.updated_at.isoformat() if path.updated_at else None,
        }


def _safe_json_loads(value, default):
    """安全解析 JSON 字段，失败返回默认值。"""
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def _resolve_goal(profile: Dict, requested_goal: Optional[str]) -> str:
    if requested_goal and requested_goal.strip():
        return requested_goal.strip()
    value = profile.get("learning_goal")
    return value.strip() if isinstance(value, str) else ""


def _parse_agent_json(raw: Any) -> Dict:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise ValueError("PlannerAgent 输出必须是 JSON 对象或字符串")

    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.startswith("json"):
            text = text[4:].strip()

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end >= start:
        text = text[start:end + 1]
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("PlannerAgent JSON 根节点必须是对象")
    return data


def _normalize_path_result(raw: Any, resolved_goal: str) -> Dict:
    data = _parse_agent_json(raw)
    raw_stages = data.get("stages")
    if not isinstance(raw_stages, list) or not raw_stages:
        raise ValueError("PlannerAgent 输出缺少非空 stages")

    stages = []
    for index, item in enumerate(raw_stages, 1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or f"阶段 {index}").strip()
        topics = item.get("topics")
        if not isinstance(topics, list):
            topics = [topics] if topics else []
        topics = [str(topic).strip() for topic in topics if str(topic).strip()]
        tasks = item.get("tasks") if isinstance(item.get("tasks"), list) else []
        stages.append({
            **item,
            "stage_id": str(item.get("stage_id") or f"stage-{index}"),
            "title": title,
            "objectives": item.get("objectives") or f"完成 {title} 的核心学习任务",
            "topics": topics or [title],
            "tasks": tasks,
        })

    if not stages:
        raise ValueError("PlannerAgent stages 中没有有效阶段")

    estimated_days = max(
        len(stages),
        _as_positive_int(data.get("estimated_days"), len(stages) * 3),
    )
    quotient, remainder = divmod(estimated_days, len(stages))
    for index, stage in enumerate(stages):
        stage["estimated_days"] = _as_positive_int(
            stage.get("estimated_days"),
            quotient + (1 if index < remainder else 0),
        )

    return {
        # The goal is authoritative business input from the request/latest
        # profile. Do not allow a model fallback to replace it with a generic
        # hard-coded learning goal.
        "goal": resolved_goal,
        "stages": stages,
        "current_stage": min(
            len(stages),
            max(1, _as_positive_int(data.get("current_stage"), 1)),
        ),
        "estimated_days": sum(stage["estimated_days"] for stage in stages),
    }


def _as_positive_int(value, default: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return max(1, int(default))


def _as_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _sse_event(event_type: str, **payload) -> str:
    data = {"type": event_type, **payload}
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
