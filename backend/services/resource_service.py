"""Learning resource service."""

from __future__ import annotations

import datetime
import json
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from config import RAG_STRICT_MODE
from models.learning_path import LearningPath
from models.resource import Resource
from safety.content_filter import check_safety

try:
    from rag.retriever import default_retriever
except Exception:  # pragma: no cover - RAG optional in local demo
    default_retriever = None

logger = logging.getLogger(__name__)


class ResourceService:
    """Owns resource generation, persistence, and read-side formatting."""

    def __init__(self, resource_agent, profile_service):
        self.resource_agent = resource_agent
        self.profile_service = profile_service
        self.retriever = default_retriever

    async def generate_resources(
        self,
        db: Session,
        student_id: str,
        topic: str,
        types: Optional[List[str]] = None,
        difficulty: str = "中级",
        count: int = 1,
        path_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        is_review: bool = False,
        on_progress: Optional[Callable[[int, str, str], None]] = None,
    ) -> Dict:
        """Generate resources with the agent and persist the result."""
        _emit_progress(on_progress, 10, "preparing", "正在准备学生画像和生成参数")
        self.profile_service.get_or_create_student(db, student_id)
        path = self.validate_path_ownership(db, student_id, path_id)
        profile = self.profile_service.get_profile(db, student_id)
        stage_info = _build_stage_info(path, topic, stage_id=stage_id) if path else None
        knowledge_sources = self._retrieve_knowledge(topic, stage_info)

        _emit_progress(on_progress, 35, "generating", "正在调用资源生成逻辑")
        if self.resource_agent:
            raw = await self.resource_agent.generate_resources(
                topic=topic,
                resource_types=_normalize_types(types),
                difficulty=difficulty,
                profile=profile,
            )
            result = _coerce_resource_result(raw, topic, types, difficulty, count)
        else:
            result = _template_resources(topic, types, difficulty, count)
        result["knowledge_sources"] = knowledge_sources

        _emit_progress(on_progress, 75, "persisting", "正在保存学习资源")
        items = self.persist_generated_resources(
            db=db,
            student_id=student_id,
            generated=result,
            path_id=path_id,
            stage_id=stage_info.get("stage_id") if stage_info else stage_id,
            default_topic=topic,
            default_difficulty=difficulty,
            is_review=is_review,
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
            rows = self.retriever.retrieve(query, top_k=5, min_similarity=0.15)
            if RAG_STRICT_MODE and not rows:
                raise RuntimeError(f"严格模式：知识库未命中主题“{topic}”")
            logger.info(
                "资源生成知识库命中: topic=%s sources=%s",
                topic,
                [row.get("source") for row in rows],
            )
            return rows
        except Exception as exc:
            if RAG_STRICT_MODE:
                raise RuntimeError(f"严格模式：资源知识库检索失败：{exc}") from exc
            logger.warning("资源知识库检索失败，继续使用画像生成: %s", exc)
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
    ) -> List[Dict]:
        """Persist an already generated ResourceAgent result (used by the pipeline)."""
        saved = []
        source_refs = generated.get("knowledge_sources") or []
        for item in generated.get("resources", []):
            if not isinstance(item, dict):
                continue
            content = item.get("content") or ""
            output_check = check_safety(content, context="resource_output")
            if not output_check["safe"]:
                raise ValueError(output_check.get("reason") or "生成内容未通过安全检查")
            resource_id = str(uuid.uuid4())
            resource_type = item.get("type") or "document"
            title = item.get("title") or f"{default_topic} 学习资源"
            artifact_url, mime_type = _create_artifact(resource_id, resource_type, title, content)
            resource = Resource(
                id=resource_id,
                student_id=student_id,
                path_id=path_id,
                stage_id=stage_id,
                type=resource_type,
                title=title,
                content=content,
                topic=item.get("topic") or default_topic,
                difficulty=item.get("difficulty") or default_difficulty,
                is_review=is_review,
                source_refs=json.dumps(source_refs, ensure_ascii=False),
                artifact_url=artifact_url,
                mime_type=mime_type,
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
        """Generate resources and expose the result as SSE events."""
        yield f'data: {{"type":"start","message":"开始生成{topic}学习资源"}}\n\n'
        yield f'data: {{"type":"progress","progress":20,"message":"正在准备资源生成任务"}}\n\n'
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
        yield f'data: {{"type":"data","data":{_json_dumps(result)}}}\n\n'
        yield f'data: {{"type":"done"}}\n\n'

    def list_resources(
        self,
        db: Session,
        student_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> Dict:
        """Return a paginated resource list."""
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        query = db.query(Resource)
        if student_id:
            query = query.filter(Resource.student_id == student_id)
        if resource_type:
            canonical_type = "exercise" if resource_type == "quiz" else resource_type
            query = query.filter(Resource.type == canonical_type)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                (Resource.title.like(like)) |
                (Resource.topic.like(like)) |
                (Resource.content.like(like))
            )

        total = query.count()
        rows = (
            query.order_by(Resource.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = [self._resource_to_dict(row) for row in rows]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_resource(self, db: Session, resource_id: str) -> Optional[Dict]:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            return None
        return self._resource_to_dict(resource, include_content=True)

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
        content = resource.content or ""
        description = content.replace("\n", " ")[:120]
        content_payload = _safe_json_loads(content, {}) if resource.type == "interactive_classroom" else {}
        source_refs = _safe_json_loads(getattr(resource, "source_refs", None), [])
        data = {
            "id": resource.id,
            "student_id": resource.student_id,
            "path_id": resource.path_id,
            "stage_id": resource.stage_id,
            "type": resource.type,
            "title": resource.title,
            "topic": resource.topic,
            "difficulty": resource.difficulty,
            "description": description,
            "tags": [v for v in [resource.topic, resource.difficulty, resource.type] if v],
            "is_review": bool(resource.is_review),
            "classroom_id": content_payload.get("classroom_id") if isinstance(content_payload, dict) else None,
            "source_refs": source_refs if isinstance(source_refs, list) else [],
            "artifact_url": getattr(resource, "artifact_url", None),
            "mime_type": getattr(resource, "mime_type", None),
            "created_at": resource.created_at.isoformat() if resource.created_at else None,
            "createdAt": resource.created_at.isoformat() if resource.created_at else None,
        }
        if include_content:
            data["content"] = content
        return data


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
            normalized.append({
                "type": item.get("type") or "document",
                "title": item.get("title") or f"{topic} 学习资源",
                "topic": item.get("topic") or topic,
                "difficulty": item.get("difficulty") or difficulty,
                "content": item.get("content") or "",
            })
        if not normalized:
            raise ValueError("ResourceAgent resources list contains no valid objects")

        return {
            **data,
            "topic": data.get("topic", topic),
            "difficulty": data.get("difficulty", difficulty),
            "resources": normalized,
            "generated_at": data.get("generated_at") or _now_iso(),
        }
    except Exception as exc:
        logger.warning("ResourceAgent 输出解析失败，使用模板资源兜底: %s", exc)
        return _template_resources(topic, types, difficulty, count)


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


def _normalize_types(types: Optional[List[str]]) -> List[str]:
    allowed = {"document", "exercise", "code", "mindmap", "reading"}
    defaults = ["document", "exercise", "code", "mindmap", "reading"]
    normalized = [item for item in (types or defaults) if item in allowed]
    return normalized or defaults


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
) -> Dict:
    normalized_types = _normalize_types(types)

    content_by_type = {
        "document": (
            f"## {topic} 学习讲义\n\n"
            f"### 核心概念\n{topic} 是当前学习目标中的重点知识。建议先掌握定义、适用场景和常见题型。\n\n"
            "### 学习建议\n1. 先整理概念卡片。\n2. 再完成 3 道基础题。\n3. 最后用自己的话复述关键步骤。"
        ),
        "exercise": (
            f"# {topic} 练习题\n\n"
            f"1. 请解释 {topic} 的基本含义。\n\n"
            f"2. 给出一个 {topic} 的实际应用例子。\n\n"
            "参考：先写出定义，再结合题目条件逐步分析。"
        ),
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
            "  - 基本概念\n"
            "  - 核心方法\n"
            "  - 常见题型\n"
            "  - 复习计划\n"
        ),
        "reading": (
            f"# {topic} 拓展阅读\n\n"
            "- 先阅读教材对应章节。\n"
            "- 再查阅课程讲义或权威教程。\n"
            "- 阅读后整理 3 个关键问题。"
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
