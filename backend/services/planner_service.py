"""
学习路径规划业务逻辑层 —— API 与 PlannerAgent / DB 的桥梁。

职责：
- 管理 LearningPath 的 CRUD
- 调度 PlannerAgent 进行流式/非流式路径生成
- 将 Agent 输出持久化到数据库
"""
import json
import logging
import uuid
from typing import AsyncIterator, Dict, Optional

from sqlalchemy.orm import Session

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

        # 1. 获取学生画像
        profile = self.profile_service.get_profile(db, student_id)
        if not profile:
            yield sse_error("PROFILE_NOT_FOUND", "请先完成学生画像构建")
            yield sse_done()
            return

        yield f'data: {{"type":"progress","progress":20,"message":"画像读取完成，开始生成个性化学习路径"}}\n\n'

        # 2. 调用 PlannerAgent.chat() 流式生成
        async for event in self.agent.chat(
            student_id=student_id,
            profile=profile,
            goal=goal,
            current_path=None,
        ):
            # 透传 Agent 产出的 SSE 事件
            yield event

            # 检测 data 事件以便持久化
            if '"type":"data"' in event:
                try:
                    prefix = "data: "
                    json_str = event.strip()
                    if json_str.startswith(prefix):
                        json_str = json_str[len(prefix):]
                    payload = json.loads(json_str)
                    path_data = payload.get("data", {})
                    if path_data and path_data.get("stages"):
                        self.save_path(db, student_id, path_data)
                        logger.info(f"路径已自动持久化: student={student_id}")
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"解析路径 data 事件失败: {e}")

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

        result = await self.agent.build_path(
            student_id=student_id,
            profile=profile,
            goal=goal,
            current_path=current_path,
            evaluation_feedback=evaluation_feedback,
        )
        if result and result.get("stages"):
            self.save_path(db, student_id, result)
        return result

    # ── 工具方法 ─────────────────────────────────────────────

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
