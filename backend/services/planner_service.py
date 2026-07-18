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
import time
import uuid
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional

from sqlalchemy.orm import Session

from api.response import sse_done, sse_error
from config import LLM_STRICT_MODE, PROFILE_READY_THRESHOLD, RAG_STRICT_MODE, SPARK_MODEL
from core.agent_context import AgentContext
from models.auth import Course
from models.learning_path import AgentRun, LearningPath, LearningStage, LearningTask
from models.student import StudentProfile

logger = logging.getLogger(__name__)


class PlannerService:
    """学习路径规划业务服务"""

    def __init__(self, planner_agent, db_session_factory, profile_service, retriever=None):
        """
        Args:
            planner_agent: PlannerAgent 实例
            db_session_factory: get_db 生成器工厂（用于 FastAPI Depends）
            profile_service: ProfileService 实例（用于获取学生画像）
        """
        self.agent = planner_agent
        self.db_session_factory = db_session_factory
        self.profile_service = profile_service
        self.retriever = retriever
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

    def get_current_path_for_course(
        self,
        db: Session,
        *,
        user_id: str,
        course_id: str,
    ) -> Optional[Dict]:
        """按登录用户和课程双重限定读取路径。"""
        path = (
            db.query(LearningPath)
            .filter(
                LearningPath.user_id == user_id,
                LearningPath.course_id == course_id,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.version.desc())
            .first()
        )
        if not path:
            return None
        self.ensure_normalized_entities(db, path)
        return self._path_to_dict(path)

    def get_path_history(self, db: Session, student_id: str) -> list:
        """获取学生学习路径历史版本列表。"""
        paths = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == student_id,
                LearningPath.status != "archived",
            )
            .order_by(LearningPath.version.asc())
            .all()
        )
        return [self._path_to_dict(p) for p in paths]

    def get_path_by_id(
        self,
        db: Session,
        student_id: str,
        path_id: str,
    ) -> Optional[Dict]:
        """读取属于当前课程的指定路径版本。"""
        path = (
            db.query(LearningPath)
            .filter(
                LearningPath.id == path_id,
                LearningPath.student_id == student_id,
                LearningPath.status != "archived",
            )
            .first()
        )
        return self._path_to_dict(path) if path else None

    def archive_path(self, db: Session, student_id: str, path_id: str) -> bool:
        """安全归档路径；不物理删除其资源、记录和评估证据。"""
        path = (
            db.query(LearningPath)
            .filter(
                LearningPath.id == path_id,
                LearningPath.student_id == student_id,
                LearningPath.status != "archived",
            )
            .first()
        )
        if not path:
            return False

        was_active = path.status == "active"
        path.status = "archived"
        if was_active:
            previous = (
                db.query(LearningPath)
                .filter(
                    LearningPath.student_id == student_id,
                    LearningPath.id != path_id,
                    LearningPath.status == "superseded",
                )
                .order_by(LearningPath.version.desc())
                .first()
            )
            if previous:
                previous.status = "active"
        db.commit()
        logger.info("学习路径已安全归档: student=%s path=%s", student_id, path_id)
        return True

    def save_path(
        self,
        db: Session,
        student_id: str,
        path_data: Dict,
        *,
        user_id: Optional[str] = None,
        course_id: Optional[str] = None,
        generation_metadata: Optional[Dict] = None,
    ) -> LearningPath:
        """事务化保存路径、阶段和任务；旧 active 路径标记为 superseded。"""
        metadata = {
            "generation_source": "legacy",
            "generated_by": None,
            "provider": None,
            "model": None,
            "agent_run_id": None,
            "profile_version": None,
            "fallback_used": False,
            "fallback_type": None,
            **(generation_metadata or {}),
        }
        course = self._resolve_course(db, student_id, user_id=user_id, course_id=course_id)
        if course:
            user_id = course.user_id
            course_id = course.id

        stages = _normalized_stage_snapshot(path_data.get("stages", []))
        if not stages:
            raise ValueError("学习路径至少需要一个有效阶段")
        current_order, current_stage_id = _resolve_current_stage(stages, path_data)

        try:
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

            latest = (
                db.query(LearningPath)
                .filter(LearningPath.student_id == student_id)
                .order_by(LearningPath.version.desc())
                .first()
            )
            new_version = (latest.version + 1) if latest else 1
            estimated_days = _as_positive_int(
                path_data.get("estimated_days"),
                sum(_as_positive_int(stage.get("estimated_days"), 1) for stage in stages),
            )

            record = LearningPath(
                id=str(uuid.uuid4()),
                student_id=student_id,
                user_id=user_id,
                course_id=course_id,
                version=new_version,
                goal=path_data.get("goal", ""),
                stages=json.dumps(stages, ensure_ascii=False),
                current_stage=current_order,
                current_stage_id=current_stage_id,
                estimated_days=estimated_days,
                status="active",
                generation_source=metadata["generation_source"],
                generated_by=metadata["generated_by"],
                provider=metadata["provider"],
                model=metadata["model"],
                agent_run_id=metadata["agent_run_id"],
                profile_version=metadata["profile_version"],
                fallback_used=bool(metadata["fallback_used"]),
                fallback_type=metadata["fallback_type"],
                generated_at=metadata.get("generated_at") or datetime.utcnow(),
            )
            db.add(record)
            db.flush()
            self._persist_entities(db, record, stages)
            db.commit()
            db.refresh(record)
            logger.info(
                "学习路径已事务化保存: user=%s course=%s student=%s v%s source=%s",
                user_id,
                course_id,
                student_id,
                new_version,
                record.generation_source,
            )
            return record
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def _resolve_course(
        db: Session,
        student_id: str,
        *,
        user_id: Optional[str] = None,
        course_id: Optional[str] = None,
    ) -> Optional[Course]:
        query = db.query(Course).filter(Course.student_id == student_id)
        if user_id:
            query = query.filter(Course.user_id == user_id)
        if course_id:
            query = query.filter(Course.id == course_id)
        return query.first()

    @staticmethod
    def _persist_entities(
        db: Session,
        path: LearningPath,
        stages: list[Dict],
    ) -> None:
        """把兼容快照展开为可独立查询和更新的 Stage/Task 行。"""
        for stage_index, stage in enumerate(stages, 1):
            stage_id = str(stage.get("stage_id") or f"stage-{stage_index}")
            normalized_stage_status = _normalize_stage_status(
                stage.get("status"),
                stage_index == path.current_stage,
            )
            stage_row = LearningStage(
                id=str(uuid.uuid4()),
                path_id=path.id,
                stage_id=stage_id,
                title=str(stage.get("title") or f"阶段 {stage_index}"),
                description=str(stage.get("description") or ""),
                order=_as_positive_int(stage.get("order"), stage_index),
                status=normalized_stage_status,
                learning_objectives=json.dumps(
                    _as_string_list(stage.get("learning_objectives") or stage.get("objectives")),
                    ensure_ascii=False,
                ),
                knowledge_point_ids=json.dumps(
                    _as_string_list(stage.get("knowledge_point_ids")),
                    ensure_ascii=False,
                ),
                topics=json.dumps(_as_string_list(stage.get("topics")), ensure_ascii=False),
                unlock_conditions=json.dumps(
                    _as_string_list(stage.get("unlock_conditions")),
                    ensure_ascii=False,
                ),
                resource_blueprint=json.dumps(
                    stage.get("resource_blueprint") if isinstance(stage.get("resource_blueprint"), list) else [],
                    ensure_ascii=False,
                ),
                estimated_days=_as_positive_int(stage.get("estimated_days"), 1),
            )
            db.add(stage_row)
            db.flush()

            for task_index, task in enumerate(stage.get("tasks") or [], 1):
                if not isinstance(task, dict):
                    continue
                task_id = str(task.get("task_id") or task.get("id") or f"{stage_id}-task-{task_index}")
                task_type = str(
                    task.get("task_type")
                    or task.get("type")
                    or task.get("resource_type")
                    or "document"
                )
                title = str(task.get("title") or task.get("task") or task.get("description") or "学习任务")
                normalized_task_status = (
                    "completed"
                    if normalized_stage_status == "completed"
                    else _normalize_task_status(task.get("status"))
                )
                db.add(LearningTask(
                    id=str(uuid.uuid4()),
                    path_id=path.id,
                    stage_row_id=stage_row.id,
                    stage_id=stage_id,
                    task_id=task_id,
                    task_type=task_type,
                    title=title,
                    description=str(task.get("description") or ""),
                    content=_task_content(task),
                    order=_as_positive_int(task.get("order"), task_index),
                    estimated_minutes=_task_minutes(task),
                    difficulty=str(task.get("difficulty") or "初级"),
                    status=normalized_task_status,
                    prerequisite_task_ids=json.dumps(
                        _as_string_list(
                            task.get("prerequisite_task_ids")
                            or task.get("prerequisites")
                        ),
                        ensure_ascii=False,
                    ),
                    resource_id=task.get("resource_id"),
                    completed_at=datetime.utcnow()
                    if normalized_task_status == "completed"
                    else None,
                ))

    def ensure_normalized_entities(self, db: Session, path: LearningPath) -> None:
        """为历史 JSON 路径幂等补齐标准化 Stage/Task 行和课程归属。"""
        existing_stages = (
            db.query(LearningStage)
            .filter(LearningStage.path_id == path.id)
            .count()
        )
        existing_tasks = (
            db.query(LearningTask)
            .filter(LearningTask.path_id == path.id)
            .count()
        )
        changed = False
        if not path.course_id or not path.user_id:
            course = self._resolve_course(db, path.student_id)
            if course:
                path.course_id = course.id
                path.user_id = course.user_id
                changed = True
        if not existing_stages or not existing_tasks:
            if existing_tasks:
                db.query(LearningTask).filter(LearningTask.path_id == path.id).delete(
                    synchronize_session=False
                )
            if existing_stages:
                db.query(LearningStage).filter(LearningStage.path_id == path.id).delete(
                    synchronize_session=False
                )
            stages = _normalized_stage_snapshot(_safe_json_loads(path.stages, []))
            if stages:
                current_order, current_stage_id = _resolve_current_stage(
                    stages,
                    {
                        "current_stage": path.current_stage,
                        "current_stage_id": path.current_stage_id,
                    },
                )
                path.current_stage = current_order
                path.current_stage_id = current_stage_id
                self._persist_entities(db, path, stages)
                changed = True
        if changed:
            db.commit()

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
        yield _sse_event("workflow_started", message="开始检查课程画像和学习目标")

        if not self._claim_generation(student_id):
            yield sse_error("CONFLICT", "该学生的学习路径正在生成，请勿重复提交")
            yield sse_done()
            return

        run: Optional[AgentRun] = None
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

            course = self._resolve_course(db, student_id)
            if not course:
                raise ValueError("学生不属于任何有效课程，无法生成课程学习路径")
            context = AgentContext(
                user_id=course.user_id,
                course_id=course.id,
                session_id=f"planner-{uuid.uuid4().hex[:12]}",
            )
            run = self._start_agent_run(db, context, "PlannerAgent")
            yield _sse_event(
                "agent_started",
                step="planner",
                agent="PlannerAgent",
                run_id=run.id,
                message="PlannerAgent 正在基于课程画像生成学习路径",
            )

            raw = await self._generate_with_agent(
                context=context,
                profile=profile,
                goal=resolved_goal,
            )
            path_data = _normalize_path_result(raw, resolved_goal)
            knowledge_sources = self._retrieve_course_knowledge(resolved_goal, profile)
            self._attach_stage_knowledge_sources(path_data, knowledge_sources)
            metadata = self._generation_metadata(profile, run.id)
            self._complete_agent_run(
                db,
                run,
                status="completed",
                metadata=metadata,
                knowledge_hit_count=sum(
                    len(stage.get("knowledge_sources") or [])
                    for stage in path_data.get("stages", [])
                ),
            )
            yield _sse_event(
                "agent_completed",
                step="planner",
                agent="PlannerAgent",
                run_id=run.id,
                provider=metadata.get("provider"),
                model=metadata.get("model"),
                fallback_used=metadata.get("fallback_used", False),
                duration_ms=run.duration_ms,
                message="PlannerAgent 已生成并校验学习路径",
            )

            record = self.save_path(
                db,
                student_id,
                path_data,
                user_id=course.user_id,
                course_id=course.id,
                generation_metadata=metadata,
            )
            saved = self._path_to_dict(record)
            yield _sse_event(
                "path_saved",
                step="planner",
                path_id=record.id,
                version=record.version,
                generation_source=record.generation_source,
                message="学习路径、阶段和任务已事务化保存",
            )
            yield _sse_event("data", data=saved)
            yield _sse_event("workflow_completed", step="done", message="学习路径生成完成")
            yield sse_done()
            logger.info("路径已自动持久化: student=%s path=%s", student_id, record.id)
        except Exception as exc:
            db.rollback()
            if run:
                self._complete_agent_run(
                    db,
                    run,
                    status="failed",
                    metadata=self._generation_metadata(profile if "profile" in locals() else {}, run.id),
                    error_code=exc.__class__.__name__,
                    fallback_reason=str(exc),
                )
            yield _sse_event(
                "agent_failed",
                step="planner",
                agent="PlannerAgent",
                run_id=run.id if run else None,
                message=str(exc) or "学习路径生成失败",
            )
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

        course = self._resolve_course(db, student_id)
        if not course:
            raise ValueError("学生不属于任何有效课程")
        context = AgentContext(
            user_id=course.user_id,
            course_id=course.id,
            session_id=f"planner-{uuid.uuid4().hex[:12]}",
        )
        run = self._start_agent_run(db, context, "PlannerAgent")
        started = time.monotonic()
        try:
            raw = await self._generate_with_agent(
                context=context,
                profile=profile,
                goal=resolved_goal,
            )
        except Exception as exc:
            self._complete_agent_run(
                db,
                run,
                status="failed",
                metadata=self._generation_metadata(profile, run.id),
                error_code=exc.__class__.__name__,
                fallback_reason=str(exc),
                duration_ms=int((time.monotonic() - started) * 1000),
            )
            raise
        result = _normalize_path_result(raw, resolved_goal)
        knowledge_sources = self._retrieve_course_knowledge(resolved_goal, profile)
        self._attach_stage_knowledge_sources(result, knowledge_sources)
        metadata = self._generation_metadata(profile, run.id)
        self._complete_agent_run(
            db,
            run,
            status="completed",
            metadata=metadata,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        record = self.save_path(
            db,
            student_id,
            result,
            user_id=course.user_id,
            course_id=course.id,
            generation_metadata=metadata,
        )
        return self._path_to_dict(record)

    # ── 工具方法 ─────────────────────────────────────────────

    async def _generate_with_agent(
        self,
        *,
        context: AgentContext,
        profile: Dict,
        goal: str,
    ) -> Any:
        """主演示链路只调用 PlannerAgent v2；旧方法仅保留给旧接口内部兼容。"""
        if not self.agent:
            raise RuntimeError("PlannerAgent 未配置")
        if hasattr(self.agent, "generate_plan_v2"):
            enriched_profile = {
                **profile,
                "learning_goal": goal,
            }
            return await self.agent.generate_plan_v2(
                context=context,
                profile=enriched_profile,
                course_outline=[],
            )
        if not LLM_STRICT_MODE and hasattr(self.agent, "generate_plan"):
            return await self.agent.generate_plan(
                profile=profile,
                goal_override=goal,
            )
        raise RuntimeError("PlannerAgent 缺少 generate_plan_v2 方法")

    @staticmethod
    def _start_agent_run(
        db: Session,
        context: AgentContext,
        agent_name: str,
    ) -> AgentRun:
        run = AgentRun(
            id=f"run_{uuid.uuid4().hex}",
            agent_name=agent_name,
            user_id=context.user_id,
            course_id=context.course_id,
            stage_id=context.stage_id,
            task_id=context.task_id,
            request_id=context.session_id,
            status="started",
            started_at=datetime.utcnow(),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def _complete_agent_run(
        db: Session,
        run: AgentRun,
        *,
        status: str,
        metadata: Dict,
        knowledge_hit_count: int = 0,
        error_code: Optional[str] = None,
        fallback_reason: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        completed_at = datetime.utcnow()
        run.status = status
        run.provider = metadata.get("provider")
        run.model = metadata.get("model")
        run.fallback_used = bool(metadata.get("fallback_used"))
        run.fallback_type = metadata.get("fallback_type")
        run.fallback_reason = fallback_reason
        run.knowledge_hit_count = max(0, int(knowledge_hit_count or 0))
        run.error_code = error_code
        run.completed_at = completed_at
        run.duration_ms = duration_ms if duration_ms is not None else max(
            0,
            int((completed_at - (run.started_at or completed_at)).total_seconds() * 1000),
        )
        db.add(run)
        db.commit()

    def _generation_metadata(self, profile: Dict, run_id: str) -> Dict:
        agent_meta = getattr(self.agent, "last_generation_metadata", {}) or {}
        usage = getattr(getattr(self.agent, "llm", None), "last_usage", None)
        fallback_used = bool(agent_meta.get("fallback_used"))
        provider = agent_meta.get("provider") or getattr(usage, "provider", None)
        model = agent_meta.get("model") or getattr(usage, "model", None)
        if provider == "spark" and not model:
            model = SPARK_MODEL
        return {
            "generation_source": "rule_fallback" if fallback_used else "agent",
            "generated_by": "PlannerAgent",
            "provider": provider,
            "model": model,
            "agent_run_id": run_id,
            "profile_version": _as_positive_int(profile.get("version"), 1),
            "fallback_used": fallback_used,
            "fallback_type": agent_meta.get("fallback_type"),
        }

    def _retrieve_course_knowledge(self, goal: str, profile: Dict) -> list[Dict]:
        if not self.retriever:
            return []
        query = " ".join(
            str(value)
            for value in [
                goal,
                profile.get("knowledge_level"),
                " ".join(profile.get("weakness") or []),
                " ".join(profile.get("interest") or []),
            ]
            if value
        )
        try:
            rows = self.retriever.retrieve(query, top_k=8, min_similarity=0.15)
            if RAG_STRICT_MODE and not rows:
                raise RuntimeError(f"严格模式：知识库未命中学习目标“{goal}”")
            logger.info(
                "路径规划知识库命中: goal=%s sources=%s",
                goal,
                [row.get("source") for row in rows],
            )
            return rows
        except Exception as exc:
            if RAG_STRICT_MODE:
                raise RuntimeError(f"严格模式：路径知识库检索失败：{exc}") from exc
            logger.warning("路径知识库检索失败，继续使用画像规划: %s", exc)
            return []

    def _attach_stage_knowledge_sources(
        self,
        path_data: Dict,
        course_rows: list[Dict],
    ) -> None:
        """为每个阶段单独检索 Markdown 依据，避免所有阶段复用同一组宽泛来源。"""
        if not self.retriever:
            _attach_knowledge_sources(path_data, course_rows)
            return

        for stage in path_data.get("stages", []):
            query = " ".join(
                str(value)
                for value in [
                    stage.get("title"),
                    " ".join(stage.get("topics") or []),
                    " ".join(stage.get("objectives") or []),
                ]
                if value
            )
            try:
                rows = self.retriever.retrieve(query, top_k=4, min_similarity=0.15)
            except Exception as exc:
                if RAG_STRICT_MODE:
                    raise RuntimeError(
                        f"严格模式：阶段“{stage.get('title') or stage.get('stage_id')}”知识库检索失败：{exc}"
                    ) from exc
                rows = []
            if RAG_STRICT_MODE and not rows:
                raise RuntimeError(
                    f"严格模式：阶段“{stage.get('title') or stage.get('stage_id')}”未命中知识库"
                )
            selected = rows or course_rows[:4]
            stage["knowledge_sources"] = [
                {key: row.get(key) for key in ("title", "source", "similarity")}
                for row in selected
            ]

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
            "current_stage_id": path.current_stage_id,
            "status": path.status,
            "estimated_days": path.estimated_days or total_days or None,
            "total_estimated_days": total_days or None,
            "generation_source": path.generation_source or "legacy",
            "generated_by": path.generated_by,
            "provider": path.provider,
            "model": path.model,
            "agent_run_id": path.agent_run_id,
            "profile_version": path.profile_version,
            "fallback_used": bool(path.fallback_used),
            "fallback_type": path.fallback_type,
            "generated_at": path.generated_at.isoformat() if path.generated_at else None,
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
    if hasattr(raw, "model_dump"):
        raw = raw.model_dump()
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
        learning_objectives = _as_string_list(
            item.get("learning_objectives") or item.get("objectives")
        )
        stages.append({
            **item,
            "stage_id": str(item.get("stage_id") or f"stage-{index}"),
            "order": _as_positive_int(item.get("order"), index),
            "title": title,
            "learning_objectives": learning_objectives or [f"完成 {title} 的核心学习任务"],
            "objectives": learning_objectives or [f"完成 {title} 的核心学习任务"],
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


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [
        str(item).strip()
        for item in values
        if item is not None and str(item).strip()
    ]


def _normalized_stage_snapshot(raw_stages: Any) -> list[Dict]:
    if not isinstance(raw_stages, list):
        return []
    result: list[Dict] = []
    seen_stage_ids: set[str] = set()
    seen_task_ids: set[str] = set()
    for stage_index, raw_stage in enumerate(raw_stages, 1):
        if not isinstance(raw_stage, dict):
            continue
        stage_id = str(raw_stage.get("stage_id") or f"stage-{stage_index}")
        if stage_id in seen_stage_ids:
            continue
        seen_stage_ids.add(stage_id)
        objectives = _as_string_list(
            raw_stage.get("learning_objectives") or raw_stage.get("objectives")
        )
        tasks = []
        for task_index, raw_task in enumerate(raw_stage.get("tasks") or [], 1):
            if not isinstance(raw_task, dict):
                continue
            task_id = str(
                raw_task.get("task_id")
                or raw_task.get("id")
                or f"{stage_id}-task-{task_index}"
            )
            if task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)
            task_type = str(
                raw_task.get("task_type")
                or raw_task.get("type")
                or raw_task.get("resource_type")
                or "document"
            )
            tasks.append({
                **raw_task,
                "task_id": task_id,
                "task_type": task_type,
                "type": task_type,
                "title": str(
                    raw_task.get("title")
                    or raw_task.get("task")
                    or raw_task.get("description")
                    or "学习任务"
                ),
                "order": _as_positive_int(raw_task.get("order"), task_index),
                "estimated_minutes": _task_minutes(raw_task),
                "status": _normalize_task_status(raw_task.get("status")),
                "prerequisite_task_ids": _as_string_list(
                    raw_task.get("prerequisite_task_ids")
                    or raw_task.get("prerequisites")
                ),
            })
        result.append({
            **raw_stage,
            "stage_id": stage_id,
            "order": _as_positive_int(raw_stage.get("order"), stage_index),
            "title": str(raw_stage.get("title") or f"阶段 {stage_index}"),
            "description": str(raw_stage.get("description") or ""),
            "learning_objectives": objectives,
            "objectives": objectives,
            "knowledge_point_ids": _as_string_list(raw_stage.get("knowledge_point_ids")),
            "topics": _as_string_list(raw_stage.get("topics")),
            "unlock_conditions": _as_string_list(raw_stage.get("unlock_conditions")),
            "estimated_days": _as_positive_int(raw_stage.get("estimated_days"), 1),
            "status": str(raw_stage.get("status") or "locked"),
            "tasks": sorted(tasks, key=lambda task: task["order"]),
        })
    return sorted(result, key=lambda stage: stage["order"])


def _resolve_current_stage(stages: list[Dict], path_data: Dict) -> tuple[int, str]:
    requested_id = path_data.get("current_stage_id")
    requested_order = path_data.get("current_stage")
    for stage in stages:
        if requested_id and str(stage["stage_id"]) == str(requested_id):
            return stage["order"], stage["stage_id"]
    for stage in stages:
        if str(stage["stage_id"]) == str(requested_order):
            return stage["order"], stage["stage_id"]
        if stage["order"] == _safe_int(requested_order, -1):
            return stage["order"], stage["stage_id"]
    active = next(
        (stage for stage in stages if str(stage.get("status")).lower() in {"active", "in_progress"}),
        stages[0],
    )
    return active["order"], active["stage_id"]


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_stage_status(value: Any, is_current: bool = False) -> str:
    status = str(value or "").strip().lower()
    if status in {"completed", "complete", "done", "finished"}:
        return "completed"
    if is_current or status in {"active", "current", "in_progress"}:
        return "active"
    return "locked" if status == "locked" else "not_started"


def _normalize_task_status(value: Any) -> str:
    status = str(value or "").strip().lower()
    if status in {"completed", "complete", "done", "finished"}:
        return "completed"
    if status in {"active", "current", "in_progress"}:
        return "active"
    if status == "locked":
        return "locked"
    return "not_started"


def _task_minutes(task: Dict) -> int:
    minutes = _safe_int(task.get("estimated_minutes") or task.get("estimatedMinutes"), 0)
    if minutes <= 0:
        try:
            minutes = round(float(task.get("estimated_hours") or 0) * 60)
        except (TypeError, ValueError):
            minutes = 0
    return max(5, min(480, minutes or 20))


def _task_content(task: Dict) -> str:
    content = task.get("content")
    if isinstance(content, str):
        return content
    if content is not None:
        return json.dumps(content, ensure_ascii=False)
    return ""


def _sse_event(event_type: str, **payload) -> str:
    data = {"type": event_type, **payload}
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
