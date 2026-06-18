"""Tutor chat service —— 集成 TutorAgent + RAG 检索（Day 8）

SSE 事件类型: start | delta | data | error | done
data 事件携带: {references: [{title, source, content, similarity}]}
"""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Any, Dict, List, Optional


class TutorService:
    """提供 SSE tutor chat 和轻量内存会话管理。

    Day 8 升级：集成 TutorAgent 风格系统 + RAG 知识检索。
    依赖通过 deps.py 注入，不在 service 内部直接 import agent 或 rag。
    """

    def __init__(self, llm_client, profile_service, tutor_agent=None, retriever=None):
        self.llm_client = llm_client
        self.profile_service = profile_service
        self.tutor_agent = tutor_agent
        self.retriever = retriever
        self._sessions: Dict[str, Dict] = {}
        self._messages: Dict[str, List[Dict]] = {}

    # ---- 会话管理 ----

    def list_sessions(self, student_id: str) -> Dict:
        sessions = [
            session for session in self._sessions.values()
            if session["student_id"] == student_id
        ]
        sessions.sort(key=lambda item: item["updated_at"], reverse=True)
        return {"sessions": sessions, "total": len(sessions)}

    def create_session(self, student_id: str, title: Optional[str] = None) -> Dict:
        session_id = str(uuid.uuid4())
        now = _now_iso()
        session = {
            "id": session_id,
            "session_id": session_id,
            "student_id": student_id,
            "title": title or "新的辅导会话",
            "message_count": 0,
            "messageCount": 0,
            "created_at": now,
            "updated_at": now,
            "updatedAt": now,
        }
        self._sessions[session_id] = session
        self._messages[session_id] = []
        return session

    # ---- 核心：流式辅导对话（Day 8 升级版） ----

    async def chat_stream(
        self,
        db,
        student_id: str,
        message: str,
        session_id: Optional[str] = None,
        history: Optional[List[str]] = None,
        explanation_style: str = "auto",
        top_k: int = 3,
    ):
        """Stream tutor answers as unified SSE events with RAG references."""
        self.profile_service.get_or_create_student(db, student_id)
        profile = self.profile_service.get_profile(db, student_id)

        if not session_id or session_id not in self._sessions:
            session = self.create_session(student_id, title=message[:24] or "辅导会话")
            session_id = session["session_id"]

        now = _now_iso()
        self._messages.setdefault(session_id, []).append({
            "role": "user",
            "content": message,
            "created_at": now,
        })
        self._touch_session(session_id)

        yield _sse_event("start", session_id=session_id, message="开始生成辅导回复")

        references = self._retrieve_references(message, top_k=top_k)
        context = _references_to_context(references)
        if not context:
            context = ["资料库中未找到可靠依据。回答时请明确说明资料不足，不要编造来源。"]

        try:
            result = await self._build_tutor_result(
                question=message,
                profile=profile,
                context=context,
                explanation_style=explanation_style,
                references=references,
            )
        except Exception as exc:
            fallback = "AI 服务暂时不可用。你可以先把题目、已知条件和卡住的步骤发给我，我会按解题步骤帮你拆解。"
            yield _sse_event("error", code="LLM_ERROR", message=str(exc))
            result = {
                "answer": fallback,
                "explanation_style": _normalize_style(explanation_style),
                "references": references,
                "diagrams": [],
                "session_id": session_id,
            }

        answer = result.get("answer") or ""
        for chunk in _chunk_text(answer):
            yield _sse_event("delta", content=chunk, delta=chunk)

        result["session_id"] = session_id
        yield _sse_event("data", data=result)

        self._messages.setdefault(session_id, []).append({
            "role": "assistant",
            "content": answer,
            "references": references,
            "created_at": _now_iso(),
        })
        self._touch_session(session_id)
        yield _sse_event("done", session_id=session_id)

    def _retrieve_references(self, message: str, top_k: int = 3) -> List[Dict]:
        if not self.retriever:
            return []
        try:
            rows = self.retriever.retrieve(
                query=message,
                top_k=max(1, min(top_k or 3, 8)),
                min_similarity=0.3,
            )
        except Exception:
            return []

        references = []
        for row in rows:
            references.append({
                "title": row.get("title") or row.get("source") or "参考资料",
                "source": row.get("source") or "unknown",
                "content": (row.get("content") or "")[:500],
                "similarity": row.get("similarity"),
            })
        return references

    async def _build_tutor_result(
        self,
        question: str,
        profile: Optional[Dict],
        context: List[str],
        explanation_style: str,
        references: List[Dict],
    ) -> Dict:
        style = _normalize_style(explanation_style)
        if self.tutor_agent:
            raw = await self.tutor_agent.tutor(
                question=question,
                context=context,
                explanation_style=style,
                profile=profile,
            )
            result = _parse_agent_result(raw)
        else:
            result = await self._llm_fallback(question, profile, context)

        result["answer"] = result.get("answer") or "暂时无法生成回答，请稍后重试。"
        result["explanation_style"] = _normalize_style(result.get("explanation_style") or style)
        result["references"] = references or _normalize_reference_list(result.get("references"))
        result["diagrams"] = _normalize_list(result.get("diagrams"))
        return result

    async def _llm_fallback(
        self,
        question: str,
        profile: Optional[Dict],
        context: List[str],
    ) -> Dict:
        system_prompt = (
            "你是 EduAgent 的智能辅导老师。回答要准确、分步骤、适合学生水平；"
            "如果资料不足，请明确说明不确定，不要编造。"
        )
        user_prompt = _build_tutor_prompt(question, profile, context)
        chunks = []
        async for chunk in self.llm_client.chat_stream(system=system_prompt, user=user_prompt):
            chunks.append(chunk)
        return {
            "answer": "".join(chunks),
            "explanation_style": "auto",
            "references": [],
            "diagrams": [],
        }

    def _touch_session(self, session_id: str):
        session = self._sessions.get(session_id)
        if not session:
            return
        count = len(self._messages.get(session_id, []))
        now = _now_iso()
        session["message_count"] = count
        session["messageCount"] = count
        session["updated_at"] = now
        session["updatedAt"] = now


def _build_tutor_prompt(message: str, profile: Optional[Dict], history: Optional[List[str]]) -> str:
    parts = ["## 学生问题", message]
    if profile:
        parts.append("\n## 学生画像")
        parts.append(json.dumps(profile, ensure_ascii=False, indent=2))
    if history:
        parts.append("\n## 最近对话")
        parts.extend(history[-10:])
    parts.append("\n请用中文回答，先给结论，再分步骤解释，最后给一个可执行的练习建议。")
    return "\n".join(parts)


def _parse_agent_result(raw: Any) -> Dict:
    if isinstance(raw, dict):
        return dict(raw)
    if not isinstance(raw, str):
        return {"answer": str(raw)}
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {"answer": text}
    except json.JSONDecodeError:
        return {"answer": raw}


def _references_to_context(references: List[Dict]) -> List[str]:
    context = []
    for item in references:
        title = item.get("title") or "参考资料"
        source = item.get("source") or "unknown"
        content = item.get("content") or ""
        if content:
            context.append(f"[{title} | {source}]\n{content}")
    return context


def _normalize_reference_list(value: Any) -> List[Dict]:
    if not value:
        return []
    items = value if isinstance(value, list) else [value]
    references = []
    for item in items:
        if isinstance(item, dict):
            references.append({
                "title": item.get("title") or item.get("source") or "参考资料",
                "source": item.get("source") or "unknown",
                "content": item.get("content") or item.get("text") or "",
                "similarity": item.get("similarity"),
            })
        else:
            references.append({
                "title": str(item),
                "source": "agent",
                "content": "",
                "similarity": None,
            })
    return references


def _normalize_list(value: Any) -> List:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _normalize_style(value: Optional[str]) -> str:
    allowed = {"auto", "analogy", "formula", "visual", "story"}
    return value if value in allowed else "auto"


def _chunk_text(text: str, size: int = 80) -> List[str]:
    if not text:
        return []
    return [text[index:index + size] for index in range(0, len(text), size)]


def _sse_event(event_type: str, **payload) -> str:
    data = {"type": event_type, **payload}
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
