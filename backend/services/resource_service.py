"""Learning resource service."""

from __future__ import annotations

import datetime
import json
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from models.resource import Resource

logger = logging.getLogger(__name__)


class ResourceService:
    """Owns resource generation, persistence, and read-side formatting."""

    def __init__(self, resource_agent, profile_service):
        self.resource_agent = resource_agent
        self.profile_service = profile_service

    async def generate_resources(
        self,
        db: Session,
        student_id: str,
        topic: str,
        types: Optional[List[str]] = None,
        difficulty: str = "中级",
        count: int = 1,
        path_id: Optional[str] = None,
        on_progress: Optional[Callable[[int, str, str], None]] = None,
    ) -> Dict:
        """Generate resources with the agent and persist the result."""
        _emit_progress(on_progress, 10, "preparing", "正在准备学生画像和生成参数")
        self.profile_service.get_or_create_student(db, student_id)
        profile = self.profile_service.get_profile(db, student_id)

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

        _emit_progress(on_progress, 75, "persisting", "正在保存学习资源")
        saved = []
        for item in result.get("resources", []):
            resource = Resource(
                id=str(uuid.uuid4()),
                student_id=student_id,
                path_id=path_id,
                type=item.get("type") or "document",
                title=item.get("title") or f"{topic} 学习资源",
                content=item.get("content") or "",
                topic=item.get("topic") or topic,
                difficulty=item.get("difficulty") or difficulty,
                is_review=False,
            )
            db.add(resource)
            saved.append(resource)

        db.commit()
        for resource in saved:
            db.refresh(resource)

        _emit_progress(on_progress, 90, "formatting", "正在整理资源结果")
        items = [self._resource_to_dict(resource) for resource in saved]
        return {
            "student_id": student_id,
            "topic": result.get("topic", topic),
            "difficulty": result.get("difficulty", difficulty),
            "items": items,
            "resources": items,
            "total": len(items),
            "generated_at": result.get("generated_at") or _now_iso(),
        }

    async def generate_stream(
        self,
        db: Session,
        student_id: str,
        topic: str,
        types: Optional[List[str]] = None,
        difficulty: str = "中级",
        count: int = 1,
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
    def _resource_to_dict(resource: Resource, include_content: bool = True) -> Dict:
        content = resource.content or ""
        description = content.replace("\n", " ")[:120]
        data = {
            "id": resource.id,
            "student_id": resource.student_id,
            "path_id": resource.path_id,
            "type": resource.type,
            "title": resource.title,
            "topic": resource.topic,
            "difficulty": resource.difficulty,
            "description": description,
            "tags": [v for v in [resource.topic, resource.difficulty, resource.type] if v],
            "is_review": bool(resource.is_review),
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
    normalized = [item for item in (types or ["document", "exercise", "code"]) if item in allowed]
    return normalized or ["document", "exercise", "code"]


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
