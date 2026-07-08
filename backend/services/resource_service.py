"""Learning resource service."""

from __future__ import annotations

import datetime
import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from models.resource import Resource


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
    ) -> Dict:
        """Generate resources with the agent and persist the result."""
        self.profile_service.get_or_create_student(db, student_id)
        profile = self.profile_service.get_profile(db, student_id)

        if self.resource_agent:
            result = await self.resource_agent.generate(
                topic=topic,
                types=types,
                difficulty=difficulty,
                student_profile=profile,
                count=count,
            )
        else:
            result = _template_resources(topic, types, difficulty, count)

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
        """Proxy the resource agent SSE stream."""
        self.profile_service.get_or_create_student(db, student_id)
        profile = self.profile_service.get_profile(db, student_id)
        if self.resource_agent:
            async for event in self.resource_agent.generate_stream(
                topic=topic,
                types=types,
                difficulty=difficulty,
                student_profile=profile,
                count=count,
            ):
                yield event
            return

        yield f'data: {{"type":"start","message":"开始生成{topic}学习资源"}}\n\n'
        result = _template_resources(topic, types, difficulty, count)
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
    import json

    return json.dumps(value, ensure_ascii=False)


def _template_resources(
    topic: str,
    types: Optional[List[str]],
    difficulty: str,
    count: int,
) -> Dict:
    allowed = {"document", "exercise", "code", "mindmap", "reading"}
    normalized_types = [item for item in (types or ["document", "exercise", "code"]) if item in allowed]
    if not normalized_types:
        normalized_types = ["document", "exercise", "code"]

    content_by_type = {
        "document": (
            f"## {topic} 学习讲义\n\n"
            f"### 核心概念\n{topic} 是当前学习目标中的重点知识。建议先掌握定义、适用场景和常见题型。\n\n"
            "### 学习建议\n1. 先整理概念卡片。\n2. 再完成 3 道基础题。\n3. 最后用自己的话复述关键步骤。"
        ),
        "exercise": (
            f"# {topic} 练习题\n\n"
            f"### 题目 1\n\n请解释 {topic} 的基本含义。\n\n"
            f"> **📝 参考答案：** 先写出定义，再结合具体条件逐步分析。\n\n"
            f"---\n\n"
            f"### 题目 2\n\n给出一个 {topic} 的实际应用例子。\n\n"
            f"> **📝 参考答案：** 结合实际场景，描述输入、处理过程和输出结果。\n\n"
            f"---\n\n"
            f"### 题目 3\n\n{ topic } 的核心步骤有哪些？请列出并简要说明每一步的作用。\n\n"
            f"> **📝 参考答案：** 围绕核心流程展开，说明各步骤的输入输出和关键注意事项。\n"
        ),
        "code": (
            f"# {topic} 代码示例\n\n"
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
