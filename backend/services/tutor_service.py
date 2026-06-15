"""Tutor chat service."""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Dict, List, Optional


class TutorService:
    """Provides SSE tutor chat and lightweight in-memory sessions."""

    def __init__(self, llm_client, profile_service):
        self.llm_client = llm_client
        self.profile_service = profile_service
        self._sessions: Dict[str, Dict] = {}
        self._messages: Dict[str, List[Dict]] = {}

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

    async def chat_stream(
        self,
        db,
        student_id: str,
        message: str,
        session_id: Optional[str] = None,
        history: Optional[List[str]] = None,
    ):
        """Stream tutor answers as SSE events."""
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

        yield f'data: {{"type":"start","session_id":"{session_id}","message":"开始生成辅导回复"}}\n\n'

        system_prompt = (
            "你是 EduAgent 的智能辅导老师。回答要准确、分步骤、适合学生水平；"
            "如果资料不足，请明确说明不确定，不要编造。"
        )
        user_prompt = _build_tutor_prompt(message, profile, history)

        chunks = []
        try:
            async for chunk in self.llm_client.chat_stream(system=system_prompt, user=user_prompt):
                chunks.append(chunk)
                yield f'data: {{"type":"chat","content":{json.dumps(chunk, ensure_ascii=False)}}}\n\n'
        except Exception as exc:
            fallback = "AI 服务暂时不可用。你可以先把题目、已知条件和卡住的步骤发给我，我会按解题步骤帮你拆解。"
            chunks.append(fallback)
            yield f'data: {{"type":"error","code":"LLM_ERROR","message":{json.dumps(str(exc), ensure_ascii=False)}}}\n\n'
            yield f'data: {{"type":"chat","content":{json.dumps(fallback, ensure_ascii=False)}}}\n\n'

        answer = "".join(chunks)
        self._messages.setdefault(session_id, []).append({
            "role": "assistant",
            "content": answer,
            "created_at": _now_iso(),
        })
        self._touch_session(session_id)
        yield f'data: {{"type":"done","session_id":"{session_id}"}}\n\n'

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


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
