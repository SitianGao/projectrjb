"""Learning resource service."""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from config import RAG_STRICT_MODE
from core.agent_context import AgentContext
from models.auth import Course, User
from models.learning_path import LearningPath, LearningStage, LearningTask
from models.resource import Resource, ResourceUserState
from safety.content_filter import check_safety

try:
    from rag.retriever import default_retriever
except Exception:  # pragma: no cover - RAG optional in local demo
    default_retriever = None

logger = logging.getLogger(__name__)

TRIGGER_SOURCES = {
    "learning_task",
    "evaluation",
    "wrong_book",
    "tutor",
    "path_adjustment",
    "manual_workspace",
    "curated_course",
    "legacy",
}


class ResourceService:
    """Owns resource generation, persistence, and read-side formatting."""

    def __init__(self, resource_agent, profile_service, retriever=None):
        self.resource_agent = resource_agent
        self.profile_service = profile_service
        self.retriever = retriever if retriever is not None else default_retriever

    async def generate_resources(
        self,
        db: Session,
        student_id: str,
        topic: str,
        types: Optional[List[str]] = None,
        difficulty: str = "中级",
        count: int = 1,
        course_id: Optional[str] = None,
        path_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        task_id: Optional[str] = None,
        trigger_source: str = "manual",
        trigger_context: Optional[Dict] = None,
        is_review: bool = False,
        on_progress: Optional[Callable[[int, str, str], None]] = None,
    ) -> Dict:
        """Generate resources with the agent and persist the result."""
        trigger_source = _normalize_trigger_source(trigger_source)
        _emit_progress(on_progress, 10, "preparing", "正在准备学生画像和生成参数")
        self.profile_service.get_or_create_student(db, student_id)
        path = self.validate_path_ownership(db, student_id, path_id)
        profile = self.profile_service.get_profile(db, student_id)
        stage_info = _build_stage_info(path, topic, stage_id=stage_id) if path else None
        knowledge_sources = self._retrieve_knowledge(topic, stage_info)

        _emit_progress(on_progress, 35, "generating", "正在调用资源生成逻辑")
        # 将检索到的知识库内容格式化为 Agent 可用的上下文字符串列表
        knowledge_context = _format_knowledge_context(knowledge_sources)
        if self.resource_agent:
            from agents.resource_agent import resource_output_to_service_dict
            agent_context = AgentContext(
                user_id=student_id,
                course_id=course_id or "default",
                stage_id=stage_id or "",
                task_id=task_id or "",
            )
            knowledge_context_str = "\n".join(knowledge_context) if knowledge_context else ""
            v2_output = await self.resource_agent.generate_resources_v2(
                context=agent_context,
                topic=topic,
                resource_types=_normalize_types(types),
                difficulty=difficulty,
                profile=profile,
                stage_info=stage_info,
                knowledge_context=knowledge_context_str or None,
            )
            result = resource_output_to_service_dict(v2_output)
        else:
            result = _template_resources(topic, types, difficulty, count)
        # 注入检索来源到结果中（持久化 + 前端展示用）
        result["knowledge_sources"] = knowledge_sources
        # 将检索来源追加到每个 resource 的 content 末尾
        _inject_source_refs(result, knowledge_sources)
        generation_meta = result.get("generation_meta") or {}
        fallback_used = bool(generation_meta.get("fallback_used"))
        generation_source = _normalize_generation_source(
            generation_meta.get("generation_source"),
            fallback_used=fallback_used,
        )
        generation_meta.update({
            "generation_source": generation_source,
            "fallback_used": fallback_used,
            "rag_used": bool(knowledge_sources),
        })
        result["generation_meta"] = generation_meta
        contextual_trigger = {
            **(trigger_context or {}),
            "rag_used": bool(knowledge_sources),
        }

        _emit_progress(on_progress, 75, "persisting", "正在保存学习资源")
        items = self.persist_generated_resources(
            db=db,
            student_id=student_id,
            generated=result,
            path_id=path_id,
            stage_id=stage_info.get("stage_id") if stage_info else stage_id,
            course_id=course_id,
            task_id=task_id,
            trigger_source=trigger_source,
            trigger_context=contextual_trigger,
            default_topic=topic,
            default_difficulty=difficulty,
            is_review=is_review,
            generation_source=generation_source,
            generation_status="degraded" if fallback_used else "ready",
            fallback_type=generation_meta.get("fallback_type"),
        )

        _emit_progress(on_progress, 90, "formatting", "正在整理资源结果")
        return {
            "student_id": student_id,
            "topic": result.get("topic", topic),
            "difficulty": result.get("difficulty", difficulty),
            "items": items,
            "resources": items,
            "total": len(items),
            "generated_at": result.get("generated_at") or _now_iso(),
            "generation_meta": result.get("generation_meta") or {},
        }

    def _retrieve_knowledge(self, topic: str, stage_info: Optional[Dict]) -> List[Dict]:
        if not self.retriever:
            return []
        query_parts = [topic]
        if stage_info:
            query_parts.extend(stage_info.get("topics") or [])
            query_parts.append(stage_info.get("title") or "")
        query = " ".join(str(value) for value in query_parts if value)
        try:
            raw_rows = self.retriever.retrieve(query, top_k=8, min_similarity=0.15)
            rows = _filter_quality_sources(raw_rows, topic)
            if RAG_STRICT_MODE and not rows:
                raise RuntimeError('strict: no knowledge hit for ' + topic)
            logger.info(
                'RAG hit: topic=%s raw=%d filtered=%d sources=%s',
                topic, len(raw_rows), len(rows),
                [row.get('source') for row in rows],
            )
            return rows
        except Exception as exc:
            if RAG_STRICT_MODE:
                raise RuntimeError('strict: RAG retrieval failed: ' + str(exc)) from exc
            logger.warning('RAG retrieval failed, continue with profile: %s', exc)
            return []

    def persist_generated_resources(
        self,
        db: Session,
        student_id: str,
        generated: Dict,
        path_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        default_topic: str = "当前关卡",
        default_difficulty: str = "中级",
        is_review: bool = False,
        course_id: Optional[str] = None,
        task_id: Optional[str] = None,
        parent_resource_id: Optional[str] = None,
        trigger_source: str = "manual",
        trigger_context: Optional[Dict] = None,
        variant_type: Optional[str] = None,
        generation_version: str = "1",
        generation_status: str = "ready",
        generation_source: str = "agent",
        fallback_type: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> List[Dict]:
        """Persist an already generated ResourceAgent result (used by the pipeline)."""
        saved = []
        source_refs = generated.get("knowledge_sources") or []
        for item in generated.get("resources", []):
            if not isinstance(item, dict):
                continue
            content_raw = item.get("content") or ""
            output_check = check_safety(str(content_raw), context="resource_output")
            if not output_check["safe"]:
                raise ValueError(output_check.get("reason") or "生成内容未通过安全检查")
            resource_id = str(uuid.uuid4())
            resource_type = item.get("type") or "document"
            title = item.get("title") or f"{default_topic} 学习资源"
            # Normalize content: always store as JSON string for dict/list, plain text otherwise
            if isinstance(content_raw, (dict, list)):
                content_normalized = json.dumps(content_raw, ensure_ascii=False)
            else:
                content_normalized = str(content_raw) if content_raw else ""
            artifact_url, mime_type = _create_artifact(resource_id, resource_type, title, content_normalized)
            resource = Resource(
                id=resource_id,
                student_id=student_id,
                course_id=course_id,
                path_id=path_id,
                stage_id=stage_id,
                task_id=task_id,
                parent_resource_id=parent_resource_id,
                type=resource_type,
                title=title,
                content=content_normalized,
                topic=item.get("topic") or default_topic,
                difficulty=item.get("difficulty") or default_difficulty,
                is_review=is_review,
                source_refs=json.dumps(source_refs, ensure_ascii=False),
                artifact_url=artifact_url,
                mime_type=mime_type,
                trigger_source=_normalize_trigger_source(trigger_source),
                trigger_context=json.dumps(trigger_context or {}, ensure_ascii=False),
                variant_type=variant_type,
                generation_version=generation_version,
                generation_status=generation_status,
                generation_source=generation_source,
                fallback_type=fallback_type,
                idempotency_key=idempotency_key,
            )
            db.add(resource)
            saved.append(resource)

        db.commit()
        for resource in saved:
            db.refresh(resource)
        return [self._resource_to_dict(resource) for resource in saved]

    async def generate_stream(
        self,
        db: Session,
        student_id: str,
        topic: str,
        types: Optional[List[str]] = None,
        difficulty: str = "中级",
        count: int = 1,
        path_id: Optional[str] = None,
        stage_id: Optional[int] = None,
    ):
        """Generate resources and expose the result as unified SSE events."""
        from core.sse import sse_event, sse_progress, sse_done

        yield sse_event("start", message=f"开始生成{topic}学习资源")
        yield sse_progress(phase="generating", percent=20, message="正在准备资源生成任务")
        result = await self.generate_resources(
            db=db,
            student_id=student_id,
            topic=topic,
            types=types,
            difficulty=difficulty,
            count=count,
            path_id=path_id,
            stage_id=stage_id,
        )
        yield sse_event("data", **result)
        yield sse_done()

    def list_resources(
        self,
        db: Session,
        student_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        resource_type: Optional[str] = None,
        course_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        task_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        generation_source: Optional[str] = None,
        trigger_source: Optional[str] = None,
        learning_status: Optional[str] = None,
        favorite: Optional[bool] = None,
        created_from: Optional[datetime.datetime] = None,
        created_to: Optional[datetime.datetime] = None,
        sort: str = "recent",
        owner_user_id: Optional[str] = None,
    ) -> Dict:
        """Return a paginated resource list."""
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        query = db.query(Resource)
        if owner_user_id:
            owned_students = db.query(Course.student_id).filter(Course.user_id == owner_user_id)
            query = query.filter(Resource.student_id.in_(owned_students))
            query = query.outerjoin(
                ResourceUserState,
                and_(
                    ResourceUserState.resource_id == Resource.id,
                    ResourceUserState.user_id == owner_user_id,
                ),
            )
        if student_id:
            query = query.filter(Resource.student_id == student_id)
        if course_id:
            query = query.filter(Resource.course_id == course_id)
        if stage_id:
            query = query.filter(Resource.stage_id == str(stage_id))
        if task_id:
            query = query.filter(Resource.task_id == task_id)
        if difficulty:
            query = query.filter(Resource.difficulty == difficulty)
        if resource_type:
            canonical_type = "exercise" if resource_type == "quiz" else resource_type
            query = query.filter(Resource.type == canonical_type)
        if generation_source:
            query = query.filter(Resource.generation_source == generation_source)
        if trigger_source:
            query = query.filter(
                Resource.trigger_source == _normalize_trigger_source(trigger_source)
            )
        if created_from:
            query = query.filter(Resource.created_at >= created_from)
        if created_to:
            query = query.filter(Resource.created_at <= created_to)
        if owner_user_id and favorite is not None:
            if favorite:
                query = query.filter(ResourceUserState.is_favorite.is_(True))
            else:
                query = query.filter(
                    or_(
                        ResourceUserState.id.is_(None),
                        ResourceUserState.is_favorite.is_(False),
                    )
                )
        if owner_user_id and learning_status:
            if learning_status == "not_started":
                query = query.filter(
                    or_(
                        ResourceUserState.id.is_(None),
                        ResourceUserState.learning_status == "not_started",
                    )
                )
            else:
                query = query.filter(
                    ResourceUserState.learning_status == learning_status
                )
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                (Resource.title.like(like)) |
                (Resource.topic.like(like)) |
                (Resource.content.like(like))
            )

        total = query.count()
        if owner_user_id and sort == "used":
            ordering = (
                ResourceUserState.last_opened_at.desc(),
                Resource.created_at.desc(),
            )
        elif owner_user_id and sort == "completed":
            ordering = (
                ResourceUserState.completed_at.desc(),
                Resource.created_at.desc(),
            )
        elif sort == "name":
            ordering = (Resource.title.asc(), Resource.created_at.desc())
        else:
            ordering = (Resource.created_at.desc(),)
        rows = (
            query.order_by(*ordering)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = [self._resource_to_dict(row) for row in rows]
        self._enrich_resource_list(
            db,
            rows=rows,
            items=items,
            owner_user_id=owner_user_id,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_resource(
        self,
        db: Session,
        resource_id: str,
        owner_user_id: Optional[str] = None,
    ) -> Optional[Dict]:
        query = db.query(Resource).filter(Resource.id == resource_id)
        if owner_user_id:
            owned_students = db.query(Course.student_id).filter(Course.user_id == owner_user_id)
            query = query.filter(Resource.student_id.in_(owned_students))
        resource = query.first()
        if not resource:
            return None
        return self._resource_to_dict(resource, include_content=True)

    def update_resource_state(
        self,
        db: Session,
        *,
        user: User,
        resource_id: str,
        is_favorite: Optional[bool] = None,
        learning_status: Optional[str] = None,
        mark_opened: bool = False,
        toggle_favorite: bool = False,
    ) -> Optional[Dict]:
        resource = self._get_owned_resource(db, user=user, resource_id=resource_id)
        if not resource:
            return None
        state = (
            db.query(ResourceUserState)
            .filter(
                ResourceUserState.user_id == user.id,
                ResourceUserState.resource_id == resource.id,
            )
            .first()
        )
        if not state:
            state = ResourceUserState(
                id=str(uuid.uuid4()),
                user_id=user.id,
                resource_id=resource.id,
            )
            db.add(state)
        now = datetime.datetime.utcnow()
        if toggle_favorite:
            state.is_favorite = not bool(state.is_favorite)
        elif is_favorite is not None:
            state.is_favorite = bool(is_favorite)
        if learning_status is not None:
            if learning_status not in {"not_started", "in_progress", "completed"}:
                raise ValueError("不支持的学习状态")
            state.learning_status = learning_status
            state.completed_at = now if learning_status == "completed" else None
        if mark_opened:
            state.last_opened_at = now
            state.opened_count = int(state.opened_count or 0) + 1
            if state.learning_status == "not_started":
                state.learning_status = "in_progress"
        db.commit()
        db.refresh(state)
        return self._resource_state_to_dict(state)

    def get_resource_detail(
        self,
        db: Session,
        *,
        user: User,
        resource_id: str,
    ) -> Optional[Dict]:
        resource = self._get_owned_resource(db, user=user, resource_id=resource_id)
        if not resource:
            return None
        state = self.update_resource_state(
            db,
            user=user,
            resource_id=resource.id,
            mark_opened=True,
        )
        payload = self._resource_to_dict(resource, include_content=True)
        payload["user_state"] = state
        course = (
            db.query(Course)
            .filter(Course.id == resource.course_id, Course.user_id == user.id)
            .first()
        ) or (
            db.query(Course)
            .filter(Course.student_id == resource.student_id, Course.user_id == user.id)
            .first()
        )
        payload["course_id"] = course.id if course else resource.course_id
        payload["course_title"] = course.title if course else None

        if resource.task_id and course:
            try:
                context = self.get_task_resource_context(
                    db,
                    user=user,
                    course_id=course.id,
                    task_id=resource.task_id,
                    preferred_resource_id=resource.id,
                )
                payload["stage_title"] = context["context"]["stage"]["title"]
                payload["task_title"] = context["context"]["task"]["title"]
                payload["next_task"] = context.get("next_task")
                payload["related_resources"] = [
                    item for item in context.get("related_resources", [])
                    if item["id"] != resource.id
                ]
            except (ValueError, KeyError, TypeError):
                # Task belongs to a superseded path or context is incomplete;
                # still return the resource, just without stage/task enrichments.
                payload["stage_title"] = None
                payload["task_title"] = None
                payload["next_task"] = None
                payload["related_resources"] = []
        else:
            payload["next_task"] = None
            payload["related_resources"] = []
        return payload

    @staticmethod
    def _get_owned_resource(
        db: Session,
        *,
        user: User,
        resource_id: str,
    ) -> Optional[Resource]:
        return (
            db.query(Resource)
            .join(Course, Course.student_id == Resource.student_id)
            .filter(Resource.id == resource_id, Course.user_id == user.id)
            .first()
        )

    def _enrich_resource_list(
        self,
        db: Session,
        *,
        rows: List[Resource],
        items: List[Dict],
        owner_user_id: Optional[str],
    ) -> None:
        if not rows:
            return
        course_ids = {row.course_id for row in rows if row.course_id}
        courses = {
            row.id: row
            for row in db.query(Course).filter(Course.id.in_(course_ids)).all()
        } if course_ids else {}
        path_ids = {row.path_id for row in rows if row.path_id}
        stage_keys = {(row.path_id, row.stage_id) for row in rows if row.path_id and row.stage_id}
        task_keys = {(row.path_id, row.task_id) for row in rows if row.path_id and row.task_id}
        stages = {}
        tasks = {}
        if path_ids:
            stages = {
                (row.path_id, row.stage_id): row
                for row in db.query(LearningStage)
                .filter(LearningStage.path_id.in_(path_ids))
                .all()
                if (row.path_id, row.stage_id) in stage_keys
            }
            tasks = {
                (row.path_id, row.task_id): row
                for row in db.query(LearningTask)
                .filter(LearningTask.path_id.in_(path_ids))
                .all()
                if (row.path_id, row.task_id) in task_keys
            }
        states = {}
        if owner_user_id:
            resource_ids = [row.id for row in rows]
            states = {
                row.resource_id: row
                for row in db.query(ResourceUserState)
                .filter(
                    ResourceUserState.user_id == owner_user_id,
                    ResourceUserState.resource_id.in_(resource_ids),
                )
                .all()
            }
        for row, item in zip(rows, items):
            course = courses.get(row.course_id)
            stage = stages.get((row.path_id, row.stage_id))
            task = tasks.get((row.path_id, row.task_id))
            item["course_title"] = course.title if course else None
            item["stage_title"] = stage.title if stage else None
            item["task_title"] = task.title if task else None
            item["user_state"] = self._resource_state_to_dict(
                states.get(row.id)
            )

    @staticmethod
    def _resource_state_to_dict(
        state: Optional[ResourceUserState],
    ) -> Dict:
        if not state:
            return {
                "is_favorite": False,
                "learning_status": "not_started",
                "opened_count": 0,
                "last_opened_at": None,
                "completed_at": None,
            }
        return {
            "is_favorite": bool(state.is_favorite),
            "learning_status": state.learning_status or "not_started",
            "opened_count": int(state.opened_count or 0),
            "last_opened_at": (
                state.last_opened_at.isoformat() if state.last_opened_at else None
            ),
            "completed_at": (
                state.completed_at.isoformat() if state.completed_at else None
            ),
        }

    def get_task_resource_context(
        self,
        db: Session,
        *,
        user: User,
        course_id: str,
        task_id: str,
        resource_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        preferred_resource_id: Optional[str] = None,
    ) -> Dict:
        course, path, stage, task = self._require_task_context(
            db,
            user=user,
            course_id=course_id,
            task_id=task_id,
        )
        query = db.query(Resource).filter(
            Resource.student_id == course.student_id,
            Resource.task_id == task.task_id,
        )
        if resource_type:
            query = query.filter(Resource.type == _normalize_contextual_type(resource_type))
        if difficulty:
            query = query.filter(Resource.difficulty == difficulty)
        resources = query.order_by(Resource.created_at.desc()).all()

        selected = next(
            (
                item for item in resources
                if item.id == preferred_resource_id and item.generation_status == "ready"
            ),
            None,
        )
        if not selected:
            selected = next(
                (
                    item for item in resources
                    if item.generation_status == "ready" and not item.parent_resource_id
                ),
                None,
            )
        # degraded fallback: 可以展示，但不能阻止重新生成
        if not selected:
            selected = next(
                (
                    item for item in resources
                    if item.generation_status == "degraded" and not item.parent_resource_id
                ),
                None,
            )
        if not selected and resources:
            selected = next(
                (item for item in resources if item.generation_status == "ready"),
                next(
                    (item for item in resources if item.generation_status == "degraded"),
                    resources[0],
                ),
            )

        # Backfill the legacy one-way task.resource_id relation once it is safely scoped.
        if not selected and task.resource_id:
            legacy = (
                db.query(Resource)
                .filter(
                    Resource.id == task.resource_id,
                    Resource.student_id == course.student_id,
                )
                .first()
            )
            if legacy:
                legacy.course_id = course.id
                legacy.path_id = path.id
                legacy.stage_id = stage.stage_id
                legacy.task_id = task.task_id
                legacy.trigger_source = legacy.trigger_source or "legacy_task_binding"
                legacy.generation_status = legacy.generation_status or "ready"
                db.commit()
                db.refresh(legacy)
                selected = legacy
                resources = [legacy]

        return self._task_context_payload(
            db,
            course=course,
            path=path,
            stage=stage,
            task=task,
            resource=selected,
            related=[item for item in resources if item.generation_status in {"ready", "degraded"}],
            reused=False,
        )

    async def generate_contextual_resource(
        self,
        db: Session,
        *,
        user: User,
        course_id: str,
        resource_type: Optional[str],
        topic: Optional[str],
        trigger_source: str,
        trigger_context: Optional[Dict],
        task_id: str,
        stage_id: Optional[str] = None,
        parent_resource_id: Optional[str] = None,
        generation_options: Optional[Dict] = None,
        on_progress: Optional[Callable[[int, str, str], None]] = None,
    ) -> Dict:
        """Generate or reuse the single resource required by a learning task."""
        trigger_source = _normalize_trigger_source(trigger_source)
        _emit_progress(on_progress, 10, "analyzing", "正在分析当前学习任务")
        course, path, stage, task = self._require_task_context(
            db,
            user=user,
            course_id=course_id,
            task_id=task_id,
        )
        if stage_id is not None and str(stage.stage_id) != str(stage_id):
            raise ValueError("任务不属于指定学习阶段")

        options = generation_options or {}
        resolved_type = _normalize_contextual_type(resource_type or task.task_type)
        resolved_difficulty = str(options.get("difficulty") or task.difficulty or "初级")
        generation_version = str(options.get("generation_version") or "1")
        force_regenerate = bool(options.get("force_regenerate"))
        variant_type = options.get("variant_type")
        resolved_topic = (topic or "").strip() or _derive_task_topic(task, stage)
        idempotency_key = _contextual_idempotency_key(
            user.id,
            task.task_id,
            resolved_type,
            resolved_difficulty,
            generation_version,
        )

        existing = (
            db.query(Resource)
            .filter(
                Resource.student_id == course.student_id,
                Resource.task_id == task.task_id,
                Resource.type == resolved_type,
                Resource.difficulty == resolved_difficulty,
                Resource.generation_version == generation_version,
                Resource.parent_resource_id.is_(None),
                Resource.generation_status.in_(["ready"]),
            )
            .order_by(Resource.created_at.desc())
            .first()
        )
        # degraded 资源不阻止重新生成，只作为 fallback 展示
        if not existing and not force_regenerate:
            existing_degraded = (
                db.query(Resource)
                .filter(
                    Resource.student_id == course.student_id,
                    Resource.task_id == task.task_id,
                    Resource.type == resolved_type,
                    Resource.difficulty == resolved_difficulty,
                    Resource.parent_resource_id.is_(None),
                    Resource.generation_status == "degraded",
                )
                .order_by(Resource.created_at.desc())
                .first()
            )
            if existing_degraded:
                logger.info("任务存在 degraded 资源，不自动复用，将尝试重新生成: %s", existing_degraded.id)

        if existing and not _resource_is_usable(existing):
            logger.warning(
                "忽略不可执行的旧资源并重新生成: resource=%s type=%s",
                existing.id,
                existing.type,
            )
            existing.generation_status = "failed"
            db.commit()
            existing = None
        if existing and not force_regenerate and not parent_resource_id:
            payload = self.get_task_resource_context(
                db,
                user=user,
                course_id=course.id,
                task_id=task.task_id,
                preferred_resource_id=existing.id,
            )
            payload["reused"] = True
            payload["resource"]["reused"] = True
            _emit_progress(on_progress, 100, "ready", "已复用现有学习资源")
            return payload

        parent = None
        if parent_resource_id:
            parent = (
                db.query(Resource)
                .filter(
                    Resource.id == parent_resource_id,
                    Resource.student_id == course.student_id,
                    Resource.task_id == task.task_id,
                )
                .first()
            )
            if not parent:
                raise ValueError("父资源不存在或不属于当前任务")
        elif force_regenerate:
            parent = existing

        stage_info = {
            "course_id": course.id,
            "stage_id": stage.stage_id,
            "stage_index": stage.order,
            "title": stage.title,
            "description": stage.description or "",
            "objectives": _safe_json_loads(stage.learning_objectives, []),
            "topics": _safe_json_loads(stage.topics, []),
            "tasks": [{
                "task": task.title,
                "resource_type": resolved_type,
                "estimated_minutes": task.estimated_minutes,
            }],
        }
        self.profile_service.get_or_create_student(db, course.student_id)
        profile = self.profile_service.get_profile(db, course.student_id)
        _emit_progress(on_progress, 30, "retrieving", "正在检索课程知识库")
        try:
            knowledge_sources = self._retrieve_knowledge(resolved_topic, stage_info)
        except Exception as exc:
            logger.warning("任务资源知识库检索失败，进入提纲降级: %s", exc)
            knowledge_sources = []

        try:
            _emit_progress(on_progress, 55, "generating", "正在结合你的学习情况生成内容")
            if self.resource_agent is not None:
                # ── v2 主路径：Pydantic 结构化输出 + 自动修复 ──
                from agents.resource_agent import resource_output_to_service_dict
                agent_context = AgentContext(
                    user_id=str(user.id),
                    course_id=str(course.id),
                    stage_id=str(stage.stage_id),
                    task_id=str(task.task_id),
                )
                knowledge_context_str = "\n".join(_format_knowledge_context(knowledge_sources)) if knowledge_sources else ""
                v2_output = await self.resource_agent.generate_resources_v2(
                    context=agent_context,
                    topic=resolved_topic,
                    resource_types=[resolved_type],
                    difficulty=resolved_difficulty,
                    profile=profile,
                    stage_info=stage_info,
                    knowledge_context=knowledge_context_str or None,
                )
                result = resource_output_to_service_dict(v2_output)
            else:
                result = _template_resources(
                    resolved_topic,
                    [resolved_type],
                    resolved_difficulty,
                    1,
                )
                result["generation_meta"] = {
                    "generation_source": "template",
                    "fallback_used": True,
                    "fallback_type": "outline",
                    "fallback_reason_code": "LLM_NOT_CONFIGURED",
                    "fallback_reason": "resource_agent is None",
                }
        except Exception as exc:
            logger.warning("任务资源 Agent 生成失败，使用可用上下文降级: %s", exc)
            fallback_code = "UNKNOWN_GENERATION_ERROR"
            if "未配置" in str(exc) or "缺少" in str(exc) or "API Key" in str(exc):
                fallback_code = "LLM_NOT_CONFIGURED"
            elif "timeout" in str(exc).lower() or "超时" in str(exc):
                fallback_code = "LLM_TIMEOUT"
            elif "json" in str(exc).lower() or "parse" in str(exc).lower():
                fallback_code = "LLM_OUTPUT_INVALID_JSON"
            result = _template_resources(
                resolved_topic,
                [resolved_type],
                resolved_difficulty,
                1,
            )
            result["generation_meta"] = {
                "generation_source": "knowledge_base" if knowledge_sources else "outline",
                "fallback_used": True,
                "fallback_type": "knowledge_base_basic" if knowledge_sources else "outline",
                "fallback_reason_code": fallback_code,
                "fallback_reason": str(exc)[:200],
            }

        result["knowledge_sources"] = knowledge_sources
        _inject_source_refs(result, knowledge_sources)
        _emit_progress(on_progress, 80, "validating", "正在检查内容质量")
        generation_meta = result.get("generation_meta") or {}
        if not generation_meta:
            generation_meta = {
                "generation_source": "knowledge_base" if knowledge_sources else "outline",
                "fallback_used": True,
                "fallback_type": "knowledge_base_basic" if knowledge_sources else "outline",
            }
        generation_meta["generation_source"] = _normalize_generation_source(
            generation_meta.get("generation_source"),
            fallback_used=bool(generation_meta.get("fallback_used")),
        )
        generation_meta["rag_used"] = bool(knowledge_sources)
        trigger_context = {
            **(trigger_context or {}),
            "rag_used": bool(knowledge_sources),
            "fallback_reason_code": generation_meta.get("fallback_reason_code"),
        }

        saved = self.persist_generated_resources(
            db=db,
            student_id=course.student_id,
            generated=result,
            path_id=path.id,
            stage_id=stage.stage_id,
            default_topic=resolved_topic,
            default_difficulty=resolved_difficulty,
            course_id=course.id,
            task_id=task.task_id,
            parent_resource_id=parent.id if parent else None,
            trigger_source=trigger_source or "learning_task",
            trigger_context=trigger_context or {},
            variant_type=variant_type or ("regenerate" if force_regenerate else None),
            generation_version=generation_version,
            generation_source=generation_meta.get("generation_source") or "agent",
            generation_status="degraded" if generation_meta.get("fallback_used") else "ready",
            fallback_type=generation_meta.get("fallback_type"),
            idempotency_key=(
                f"{idempotency_key}:{uuid.uuid4().hex[:8]}"
                if parent or force_regenerate
                else idempotency_key
            ),
        )
        if not saved:
            logger.warning("persist_generated_resources 返回空列表，使用模板降级")
            fallback_result = _template_resources(resolved_topic, [resolved_type], resolved_difficulty, 1)
            fallback_result["generation_meta"] = {
                "generation_source": "template_after_empty",
                "fallback_used": True,
                "fallback_type": "empty_persist",
            }
            fallback_result["knowledge_sources"] = knowledge_sources
            saved = self.persist_generated_resources(
                db=db,
                student_id=course.student_id,
                generated=fallback_result,
                path_id=path.id,
                stage_id=stage.stage_id,
                default_topic=resolved_topic,
                default_difficulty=resolved_difficulty,
                course_id=course.id,
                task_id=task.task_id,
                trigger_source=trigger_source or "learning_task",
                trigger_context=trigger_context or {},
                generation_version=generation_version,
                generation_source="template",
                generation_status="degraded",
            )
        resource_id = saved[0]["id"]
        if not parent and not task.resource_id:
            task.resource_id = resource_id
            db.commit()

        payload = self.get_task_resource_context(
            db,
            user=user,
            course_id=course.id,
            task_id=task.task_id,
            preferred_resource_id=resource_id,
        )
        payload["fallback_used"] = bool(generation_meta.get("fallback_used"))
        payload["fallback_type"] = generation_meta.get("fallback_type")
        payload["message"] = _fallback_message(generation_meta.get("fallback_type"))
        _emit_progress(on_progress, 100, "ready", payload["message"] or "学习内容已准备")
        return payload

    def _require_task_context(
        self,
        db: Session,
        *,
        user: User,
        course_id: str,
        task_id: str,
    ) -> tuple[Course, LearningPath, LearningStage, LearningTask]:
        course = (
            db.query(Course)
            .filter(Course.id == course_id, Course.user_id == user.id)
            .first()
        )
        if not course:
            raise ValueError("课程不存在或不属于当前登录用户")
        path = (
            db.query(LearningPath)
            .filter(
                LearningPath.course_id == course.id,
                LearningPath.student_id == course.student_id,
                LearningPath.user_id == user.id,
                LearningPath.status != "archived",
            )
            .order_by(
                (LearningPath.status == "active").desc(),
                LearningPath.version.desc(),
            )
            .first()
        )
        if not path:
            raise ValueError("当前课程还没有学习路径")
        task = (
            db.query(LearningTask)
            .filter(LearningTask.path_id == path.id, LearningTask.task_id == task_id)
            .first()
        )
        if not task:
            raise ValueError("学习任务不存在或不属于当前课程")
        stage = (
            db.query(LearningStage)
            .filter(
                LearningStage.path_id == path.id,
                LearningStage.stage_id == task.stage_id,
            )
            .first()
        )
        if not stage:
            raise ValueError("学习任务所属阶段不存在")
        return course, path, stage, task

    def _task_context_payload(
        self,
        db: Session,
        *,
        course: Course,
        path: LearningPath,
        stage: LearningStage,
        task: LearningTask,
        resource: Optional[Resource],
        related: List[Resource],
        reused: bool,
    ) -> Dict:
        all_tasks = (
            db.query(LearningTask)
            .join(LearningStage, LearningStage.id == LearningTask.stage_row_id)
            .filter(LearningTask.path_id == path.id)
            .order_by(LearningStage.order.asc(), LearningTask.order.asc())
            .all()
        )
        current_index = next(
            (index for index, item in enumerate(all_tasks) if item.id == task.id),
            -1,
        )
        next_task = all_tasks[current_index + 1] if 0 <= current_index < len(all_tasks) - 1 else None
        resource_payload = self._resource_to_dict(resource) if resource else None
        if resource_payload:
            resource_payload["reused"] = reused
        return {
            "status": resource.generation_status if resource else "missing",
            "reused": reused,
            "fallback_used": bool(resource and resource.fallback_type),
            "fallback_type": resource.fallback_type if resource else None,
            "message": _fallback_message(resource.fallback_type if resource else None),
            "resource": resource_payload,
            "related_resources": [self._resource_to_dict(item, include_content=False) for item in related],
            "next_task": (
                {
                    "task_id": next_task.task_id,
                    "title": next_task.title,
                    "route": f"/course/{course.id}/learn/{next_task.task_id}",
                }
                if next_task else None
            ),
            "context": {
                "course": {"id": course.id, "title": course.title},
                "path": {"id": path.id, "goal": path.goal or ""},
                "stage": {
                    "id": stage.stage_id,
                    "title": stage.title,
                    "order": stage.order,
                    "objectives": _safe_json_loads(stage.learning_objectives, []),
                    "topics": _safe_json_loads(stage.topics, []),
                },
                "task": {
                    "id": task.task_id,
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description or "",
                    "task_type": task.task_type,
                    "difficulty": task.difficulty or "初级",
                    "estimated_minutes": max(5, int(task.estimated_minutes or 20)),
                    "status": task.status or "not_started",
                },
            },
        }

    @staticmethod
    def validate_path_ownership(
        db: Session,
        student_id: str,
        path_id: Optional[str],
    ) -> Optional[LearningPath]:
        """Reject cross-student or unknown path associations."""
        if not path_id:
            return None
        path = (
            db.query(LearningPath)
            .filter(
                LearningPath.id == path_id,
                LearningPath.student_id == student_id,
            )
            .first()
        )
        if not path:
            raise ValueError("学习路径不存在或不属于当前学生")
        return path

    @staticmethod
    def _resource_to_dict(resource: Resource, include_content: bool = True) -> Dict:
        content_raw = resource.content or ""
        content_parsed = _safe_json_loads(content_raw, None)

        # Summary
        if isinstance(content_parsed, dict) and content_parsed.get("summary"):
            description = str(content_parsed["summary"])[:120]
        else:
            description = content_raw.replace("\n", " ")[:120] if isinstance(content_raw, str) else ""

        source_refs = _safe_json_loads(getattr(resource, "source_refs", None), [])

        # Preview stats from content
        preview = _build_preview(resource.type, content_parsed)

        # Source provenance from generation metadata
        provenance = _build_provenance(source_refs)

        data = {
            # Unified envelope fields
            "resource_id": resource.id,
            "id": resource.id,  # compat
            "user_id": resource.student_id,
            "student_id": resource.student_id,  # compat
            "course_id": resource.course_id,
            "path_id": resource.path_id,
            "stage_id": resource.stage_id,
            "stage_title": None,
            "task_id": resource.task_id,
            "parent_resource_id": resource.parent_resource_id,
            "resource_type": resource.type,
            "type": resource.type,  # compat
            "schema_version": 1,
            "status": resource.generation_status or "ready",
            "title": resource.title,
            "summary": description,
            "topic": resource.topic,
            "difficulty": resource.difficulty,
            "preview": preview,
            "artifacts": {"artifact_url": getattr(resource, "artifact_url", None), "mime_type": getattr(resource, "mime_type", None)},
            "source_provenance": provenance,
            "generation_meta": {
                "generation_source": resource.generation_source or "legacy",
                "fallback_used": bool(resource.fallback_type),
                "fallback_type": resource.fallback_type,
                "generation_version": resource.generation_version or "1",
                "trigger_source": resource.trigger_source or "manual",
                "variant_type": resource.variant_type,
            },
            "trigger_source": resource.trigger_source or "manual",
            "trigger_context": _safe_json_loads(resource.trigger_context, {}),
            "variant_type": resource.variant_type,
            "generation_version": resource.generation_version or "1",
            "reused": False,
            "tags": [v for v in [resource.topic, resource.difficulty, resource.type] if v],
            "is_review": bool(resource.is_review),
            "classroom_id": content_parsed.get("classroom_id") if isinstance(content_parsed, dict) else None,
            "source_refs": source_refs if isinstance(source_refs, list) else [],
            "artifact_url": getattr(resource, "artifact_url", None),
            "mime_type": getattr(resource, "mime_type", None),
            "created_at": resource.created_at.isoformat() if resource.created_at else None,
            "createdAt": resource.created_at.isoformat() if resource.created_at else None,
        }
        if include_content:
            data["content"] = content_parsed if content_parsed is not None else content_raw
        return data


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_trigger_source(value: Optional[str]) -> str:
    aliases = {
        "manual": "manual_workspace",
        "ai_workspace": "manual_workspace",
        "legacy_task_binding": "legacy",
    }
    normalized = aliases.get(str(value or "").strip(), str(value or "").strip())
    return normalized if normalized in TRIGGER_SOURCES else "legacy"


def _normalize_generation_source(
    value: Optional[str],
    *,
    fallback_used: bool = False,
) -> str:
    normalized = str(value or "").strip()
    aliases = {
        "agent": "llm_generated",
        "llm": "llm_generated",
        "knowledge_base": "template_generated",
        "outline": "template_generated",
        "template": "template_generated",
        "legacy": "legacy_unknown",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized in {
        "curated_seed",
        "llm_generated",
        "template_generated",
        "legacy_unknown",
    }:
        return normalized
    return "template_generated" if fallback_used else "llm_generated"


def _json_dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _emit_progress(
    callback: Optional[Callable[[int, str, str], None]],
    progress: int,
    phase: str,
    message: str,
) -> None:
    if callback:
        callback(progress, phase, message)


def _create_artifact(resource_id: str, resource_type: str, title: str, content: str):
    try:
        from services.artifact_service import artifact_service

        return artifact_service.create(resource_id, resource_type, title, content)
    except Exception:
        return None, "text/markdown"


def _coerce_resource_result(
    raw: Any,
    topic: str,
    types: Optional[List[str]],
    difficulty: str,
    count: int,
) -> Dict:
    """Normalize ResourceAgent output and fall back when its JSON is invalid."""
    try:
        data = _parse_agent_json(raw)
        resources = data.get("resources")
        if not isinstance(resources, list) or not resources:
            raise ValueError("ResourceAgent output missing non-empty resources list")

        normalized = []
        for item in resources:
            if not isinstance(item, dict):
                continue
            resource_type = item.get("type") or item.get("resource_type") or "document"
            content = item.get("content") or ""
            if resource_type == "exercise" and (
                not isinstance(content, dict) or not content.get("questions")
            ):
                raise ValueError("exercise content must contain structured questions")
            normalized.append({
                "type": resource_type,
                "title": item.get("title") or f"{topic} 学习资源",
                "topic": item.get("topic") or topic,
                "difficulty": item.get("difficulty") or difficulty,
                "content": content,
            })
        if not normalized:
            raise ValueError("ResourceAgent resources list contains no valid objects")

        return {
            **data,
            "topic": data.get("topic", topic),
            "difficulty": data.get("difficulty", difficulty),
            "resources": normalized,
            "generated_at": data.get("generated_at") or _now_iso(),
            "generation_meta": data.get("generation_meta") or {
                "generation_source": "llm_generated",
                "fallback_used": False,
                "fallback_type": None,
            },
        }
    except Exception as exc:
        logger.warning("ResourceAgent 输出解析失败，使用模板资源兜底: %s", exc)
        result = _template_resources(topic, types, difficulty, count)
        result["generation_meta"] = {
            "generation_source": "template_generated",
            "fallback_used": True,
            "fallback_type": "template",
        }
        return result


def _parse_agent_json(raw: Any) -> Dict:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise ValueError(f"unsupported ResourceAgent output type: {type(raw).__name__}")

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
    if start != -1 and end != -1 and end >= start:
        text = text[start:end + 1]

    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("ResourceAgent JSON root must be an object")
    return data


# ── 检索质量过滤常量 ──
MIN_RETRIEVAL_SIMILARITY = 0.40       # 绝对阈值：低于此值的结果直接丢弃
MIN_RELEVANCE_SIMILARITY = 0.55       # 无关主题阈值：无关键词匹配 + 低于此值 → 丢弃
TOPIC_KEYWORD_BOOST = 0.10            # 主题关键词匹配加分
MAX_SOURCES_DISPLAY = 5               # 最多展示几个来源

def _filter_quality_sources(sources: List[Dict], topic: str = "") -> List[Dict]:
    """对检索结果进行质量过滤。

    规则（按优先级）：
    1. 相似度 < MIN_RETRIEVAL_SIMILARITY → 丢弃
    2. 无主题关键词匹配 + 相似度 < MIN_RELEVANCE_SIMILARITY → 丢弃（过滤无关来源）
    3. 源文件/标题完全重复 → 去重
    4. 内容高度重叠 → 去重
    5. 主题关键词匹配 → 提升排序
    6. 不凑数：有多少合格就返回多少，最多 MAX_SOURCES_DISPLAY

    Returns:
        过滤后的结果列表（按质量分降序排列）
    """
    if not sources:
        return []

    import re
    topic_keywords = set()
    if topic:
        topic_keywords = set(re.findall(r'[一-鿿]{2,4}', topic))
        topic_keywords.update(w.lower() for w in re.findall(r'[a-zA-Z]{3,}', topic))

    filtered = []
    seen_titles = set()
    seen_content_signatures = set()

    for s in sources:
        sim = s.get("similarity", 0)
        title = s.get("title", "")
        src = s.get("source", "unknown")
        content = s.get("content", "")[:200]

        # 规则1：绝对阈值
        if sim < MIN_RETRIEVAL_SIMILARITY:
            continue

        # 规则2：主题相关性过滤 —— 无关键词匹配且相似度不够高 → 丢弃
        if topic_keywords:
            text_to_match = f"{title} {content}".lower()
            keyword_hits = sum(1 for kw in topic_keywords if kw and kw.lower() in text_to_match)
            if keyword_hits == 0 and sim < MIN_RELEVANCE_SIMILARITY:
                continue

        # 规则3：标题+来源去重
        dedup_key = f"{title}|{src}"
        if dedup_key in seen_titles:
            continue
        seen_titles.add(dedup_key)

        # 规则4：内容签名去重
        sig = content.strip().lower()
        if sig and sig in seen_content_signatures:
            continue
        if sig:
            seen_content_signatures.add(sig)

        # 规则5：主题关键词匹配加分
        quality_score = sim
        has_topic_match = False
        if topic_keywords:
            keyword_hits = sum(1 for kw in topic_keywords if kw and kw.lower() in text_to_match)
            if keyword_hits > 0:
                quality_score += TOPIC_KEYWORD_BOOST * min(keyword_hits, 3)
                has_topic_match = True

        filtered.append({
            **s,
            "quality_score": round(quality_score, 4),
            "topic_match": has_topic_match,
        })

    filtered.sort(key=lambda x: x["quality_score"], reverse=True)
    return filtered[:MAX_SOURCES_DISPLAY]


def _format_knowledge_context(sources: List[Dict]) -> List[str]:
    """将检索结果格式化为 ResourceAgent 可用的知识库上下文字符串列表。

    第6轮改造：质量过滤 + 不显示相似度等技术信息给 Agent。
    """
    if not sources:
        return []
    lines = ["## 参考知识点（来自知识库 RAG 检索）\n"]
    for i, s in enumerate(sources, 1):
        title = s.get("title", "")
        content = (s.get("content") or "")[:500]
        lines.append(f"### 参考 {i}：{title}")
        lines.append(f"{content}")
        lines.append("")
    return lines


def _format_student_sources(sources: List[Dict]) -> List[Dict]:
    """格式化学生端可见的检索来源（隐藏技术字段）。

    只返回：标题、章节路径、简短说明。
    不返回：相似度、chunk_id、collection_name、content_hash。
    """
    seen = set()
    result = []
    for s in sources:
        title = s.get("title", "")
        src = s.get("source", "unknown")
        dedup_key = f"{title}|{src}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # 从 source 路径提取章节
        parts = src.replace("\\", "/").split("/")
        chapter = parts[0] if len(parts) > 0 else ""
        filename = parts[-1] if len(parts) > 1 else src

        # 简短说明
        description = f"来自课程知识库「{chapter}」"
        if len(parts) > 2:
            description = f"来自「{chapter}」章节的「{parts[1] if len(parts) > 1 else filename}」"

        result.append({
            "title": title,
            "file": filename,
            "chapter": chapter,
            "description": description,
        })

    return result


def _inject_source_refs(result: Dict, sources: List[Dict]) -> None:
    """将检索来源注入生成资源。

    第6轮改造：
    - 学生端只显示标题+章节+说明
    - 隐藏相似度、chunk_id、collection_name 等技术字段
    - 不凑满5个：有多少合格来源就显示多少
    """
    if not sources:
        return

    student_sources = _format_student_sources(sources)
    if not student_sources:
        return

    count = len(student_sources)
    source_lines = [
        f"\n\n---\n\n## 📚 参考课程资料 {count} 项\n",
    ]
    for s in student_sources:
        source_lines.append(f"- **{s['title']}** — {s['description']}")
    source_text = "\n".join(source_lines)

    for resource in result.get("resources", []):
        if not isinstance(resource, dict):
            continue
        content = resource.get("content")
        if isinstance(content, str):
            resource["content"] = content + source_text
        elif isinstance(content, dict):
            content["source_refs"] = student_sources


def _normalize_types(types: Optional[List[str]]) -> List[str]:
    allowed = {
        "document",
        "exercise",
        "code",
        "mindmap",
        "reading",
        "ppt",
        "interactive_classroom",
    }
    defaults = ["document", "exercise", "code", "mindmap", "reading"]
    normalized = [item for item in (types or defaults) if item in allowed]
    return normalized or defaults


def _normalize_contextual_type(value: Optional[str]) -> str:
    aliases = {
        "objective": "document",
        "goal": "document",
        "lecture": "document",
        "study": "document",
        "diagram": "mindmap",
        "quiz": "exercise",
        "assessment": "exercise",
        "exam": "exercise",
        "classroom": "interactive_classroom",
        "openmaic": "interactive_classroom",
    }
    normalized = str(value or "document").strip().lower()
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in {
        "document",
        "exercise",
        "code",
        "mindmap",
        "reading",
        "ppt",
        "interactive_classroom",
    } else "document"


def _derive_task_topic(task: LearningTask, stage: LearningStage) -> str:
    topics = _safe_json_loads(stage.topics, [])
    generic_titles = {"学习目标", "核心讲义", "概念图解", "知识检查", "阶段测评"}
    if task.title and task.title not in generic_titles:
        return task.title
    if topics:
        return str(topics[0])
    return task.description or stage.title or "当前学习任务"


def _contextual_idempotency_key(
    user_id: str,
    task_id: str,
    resource_type: str,
    difficulty: str,
    generation_version: str,
) -> str:
    raw = "|".join([
        str(user_id),
        str(task_id),
        str(resource_type),
        str(difficulty),
        str(generation_version),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _fallback_message(fallback_type: Optional[str]) -> Optional[str]:
    if fallback_type == "knowledge_base_basic":
        return "AI 生成暂时不可用，已根据课程知识库准备基础版本。"
    if fallback_type == "outline":
        return "暂时无法生成完整内容，已为你创建学习提纲。"
    return None


def _build_stage_info(
    path: LearningPath,
    topic: str,
    stage_id: Optional[str] = None,
) -> Optional[Dict]:
    stages = _safe_json_loads(path.stages, [])
    if not isinstance(stages, list) or not stages:
        return None

    normalized_topic = (topic or "").strip().lower()

    def topic_matches(stage: Dict) -> bool:
        for value in stage.get("topics") or []:
            candidate = str(value).strip().lower()
            if candidate and (candidate in normalized_topic or normalized_topic in candidate):
                return True
        return False

    stage_index = None
    if stage_id is not None:
        stage_index = next(
            (
                index
                for index, stage in enumerate(stages)
                if isinstance(stage, dict)
                and str(stage.get("stage_id")) == str(stage_id)
            ),
            None,
        )
        if stage_index is None:
            raise ValueError(f"学习路径中不存在阶段 {stage_id}")
    if stage_index is None:
        stage_index = next(
            (
                index
                for index, stage in enumerate(stages)
                if isinstance(stage, dict) and topic_matches(stage)
            ),
            None,
        )
    if stage_index is None:
        stage_index = next(
            (
                index
                for index, stage in enumerate(stages)
                if isinstance(stage, dict)
                and str(stage.get("stage_id")) == str(path.current_stage or 1)
            ),
            0,
        )

    stage = stages[stage_index] if isinstance(stages[stage_index], dict) else {}
    previous_stage = stages[stage_index - 1] if stage_index > 0 else {}
    next_stage = stages[stage_index + 1] if stage_index + 1 < len(stages) else {}
    return {
        "stage_id": stage.get("stage_id", stage_index + 1),
        "stage_index": stage_index + 1,
        "title": stage.get("title", f"阶段 {stage_index + 1}"),
        "description": stage.get("description", ""),
        "objectives": _normalize_list(stage.get("objectives")),
        "topics": _normalize_list(stage.get("topics")),
        "tasks": stage.get("tasks") if isinstance(stage.get("tasks"), list) else [],
        "difficulty": stage.get("difficulty", "中级"),
        "previous_stage_title": previous_stage.get("title", "") if isinstance(previous_stage, dict) else "",
        "next_stage_title": next_stage.get("title", "") if isinstance(next_stage, dict) else "",
    }


def _safe_json_loads(value: Any, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError):
        return default


def _normalize_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _template_resources(
    topic: str,
    types: Optional[List[str]],
    difficulty: str,
    count: int,
    has_rag: bool = False,
    has_llm: bool = False,
) -> Dict:
    normalized_types = _normalize_types(types)

    if not has_llm and has_rag:
        degrade_note = "> AI 生成暂时不可用，已根据课程知识库准备基础版本。\n\n"
    elif not has_llm and not has_rag:
        degrade_note = "> 暂时无法生成完整内容，已为你创建学习提纲。\n\n"
    else:
        degrade_note = ""

    content_by_type = {
        "document": (
            f"# {topic}\n\n"
            f"{degrade_note}"
            f"## 本任务要解决什么\n\n"
            f"掌握 {topic} 的核心概念和基本应用。\n\n"
            f"## 核心知识点\n\n"
            f"- {topic} 的定义与基本原理\n"
            f"- {topic} 的典型应用场景\n"
            f"- {topic} 中的注意事项\n\n"
            f"## 推荐学习顺序\n\n"
            f"1. 阅读课程知识库中关于 {topic} 的章节\n"
            f"2. 完成配套练习题\n"
            f"3. 用自己的话复述关键概念\n\n"
            f"## 关键课程资料\n\n"
            f"- 知识库中「{topic}」相关章节\n"
            f"- 课程配套练习\n\n"
            f"## 简短总结\n\n"
            f"{topic} 是当前学习任务的核心知识点。建议先理解定义和适用场景，再通过练习巩固。\n"
        ),
        "exercise": {
            "instructions": f"请完成以下关于「{topic}」的练习。" if not degrade_note else f"{degrade_note}请完成以下关于「{topic}」的练习。",
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "stem": f"关于 {topic}，以下说法正确的是？",
                    "options": [
                        {"key": "A", "text": f"{topic} 是当前阶段需要掌握的核心知识"},
                        {"key": "B", "text": f"{topic} 与实际应用完全无关"},
                        {"key": "C", "text": f"学习 {topic} 不需要理解任何前置概念"},
                        {"key": "D", "text": "以上说法都正确"},
                    ],
                    "correct_answer": ["A"],
                    "explanation": f"{topic} 是当前学习任务的核心内容，需要结合定义、原理和应用理解。",
                    "difficulty": "easy" if difficulty == "初级" else "medium",
                    "knowledge_point_ids": [topic],
                }
            ],
        },
        "code": (
            f"```python\n"
            f"# {topic} 示例代码\n"
            "def explain():\n"
            f"    return \"正在学习: {topic}\"\n\n"
            "print(explain())\n"
            "```"
        ),
        "mindmap": (
            f"- {topic}\n"
            "  - 概念定义\n"
            "  - 核心原理\n"
            "  - 应用场景\n"
            "  - 常见问题\n"
        ),
        "reading": (
            f"# {topic} 拓展阅读\n\n"
            "- 先阅读教材对应章节。\n"
            "- 再查阅课程讲义或权威教程。\n"
            "- 阅读后整理 3 个关键问题。"
        ),
        "ppt": (
            f"# {topic}\n\n"
            "1. 学习目标\n2. 核心概念\n3. 示例演示\n4. 注意事项\n5. 课后练习"
        ),
        "interactive_classroom": (
            f"# {topic} 互动课堂提纲\n\n"
            "按概念导入、过程演示、即时问答和知识检查四个环节完成本次学习。"
        ),
    }

    resources = []
    for res_type in normalized_types:
        for index in range(max(count, 1)):
            suffix = f" {index + 1}" if count > 1 else ""
            resources.append({
                "type": res_type,
                "title": f"{topic}{suffix} - {res_type}",
                "topic": topic,
                "difficulty": difficulty,
                "content": content_by_type[res_type],
            })

    return {
        "topic": topic,
        "difficulty": difficulty,
        "resources": resources,
        "generated_at": _now_iso(),
    }


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Preview / Provenance helpers ────────────────────────────────────

def _build_preview(resource_type: str, content_parsed) -> dict:
    """Generate deterministic preview stats from parsed content."""
    preview = {"schema_version": 1}
    if not isinstance(content_parsed, dict):
        return preview
    if resource_type == "document":
        preview["estimated_minutes"] = max(5, sum(len(s.get("paragraphs", [])) for s in (content_parsed.get("sections") or [])) * 3)
    elif resource_type == "exercise":
        preview["question_count"] = len(content_parsed.get("questions") or [])
    elif resource_type == "mindmap":
        root = content_parsed.get("root")
        nodes = _count_nodes(root)
        preview["branch_count"] = nodes - 1 if nodes > 0 else 0
        preview["node_count"] = nodes
    elif resource_type == "ppt":
        preview["slide_count"] = len(content_parsed.get("slides") or [])
    elif resource_type == "interactive_classroom":
        scenes = content_parsed.get("scenes") or []
        preview["scene_count"] = len(scenes)
        preview["interaction_count"] = sum(1 for s in scenes if s.get("scene_type") in ("simulation", "quiz", "discussion"))
    elif resource_type == "code":
        preview["file_count"] = 1 if (content_parsed.get("code") or content_parsed.get("snippet")) else 0
        preview["test_count"] = len(content_parsed.get("test_cases") or [])
    return preview


def _count_nodes(node) -> int:
    if not node or not isinstance(node, dict):
        return 0
    count = 1
    for child in (node.get("children") or []):
        count += _count_nodes(child)
    return count


def _resource_is_usable(resource: Resource) -> bool:
    content = _safe_json_loads(resource.content, None)
    if resource.type == "exercise":
        return isinstance(content, dict) and bool(content.get("questions"))
    if resource.type == "mindmap":
        return (
            isinstance(content, dict)
            and isinstance(content.get("root"), dict)
            and bool(content["root"].get("label"))
        )
    if resource.type == "document" and isinstance(content, dict):
        return bool(content.get("sections") or content.get("summary"))
    return bool(resource.content)


def _build_provenance(source_refs) -> dict:
    """Build source_provenance from source_refs, marking legacy orphans."""
    if not source_refs or not isinstance(source_refs, list) or len(source_refs) == 0:
        return {"grounded": False, "provenance_status": "no_sources", "retrieved_documents": [], "fallback_used": True}

    # Check if any source_path exists in the knowledge directory
    import os as _os
    knowledge_root = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "data", "knowledge")
    grounded = False
    docs = []
    for ref in source_refs:
        source = ref.get("source", "")
        full_path = _os.path.join(knowledge_root, source) if source else ""
        exists = _os.path.exists(full_path) if full_path else False
        docs.append({
            "document_id": ref.get("id", ""),
            "title": ref.get("title", ""),
            "source_path": source,
            "similarity_score": ref.get("similarity", 0),
            "path_exists": exists,
        })
        if exists:
            grounded = True

    return {
        "grounded": grounded,
        "provenance_status": "current_validated" if grounded else "legacy_orphan",
        "retrieved_documents": docs,
        "fallback_used": not grounded,
        "fallback_reason": None if grounded else "source_paths_not_found_in_knowledge_dir",
    }
