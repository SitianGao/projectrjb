"""Tutor chat service —— 集成 TutorAgent + RAG 检索（Day 8）

SSE 事件类型: start | delta | data | error | done
data 事件携带: {references: [{title, source, snippet, similarity}]}
"""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Dict, List, Optional

from backend.agents.tutor_agent import TutorAgent
from backend.rag.retriever import default_retriever


class TutorService:
    """提供 SSE tutor chat 和轻量内存会话管理。

    Day 8 升级：集成 TutorAgent 风格系统 + RAG 知识检索。
    """

    def __init__(self, llm_client, profile_service):
        self.llm_client = llm_client
        self.profile_service = profile_service
        self._sessions: Dict[str, Dict] = {}
        self._messages: Dict[str, List[Dict]] = {}

        # 创建带 LLM 的 TutorAgent（用于 tutor_with_rag）
        self._agent = TutorAgent(llm_client)

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
        history: Optional[List[str]] = None,  # noqa: ARG001 (reserved for future use)
        explanation_style: str = "auto",
    ):
        """Stream tutor answers as SSE events.

        Day 8 流程:
        1. 获取学生画像
        2. RAG 检索知识库
        3. TutorAgent 生成（含风格 + RAG 上下文）
        4. SSE 流式输出, data 事件包含 references
        """
        self.profile_service.get_or_create_student(db, student_id)
        profile = self.profile_service.get_profile(db, student_id)

        # ---- 会话初始化 ----
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

        # ---- SSE: start ----
        yield (
            f'data: {{"type":"start","session_id":"{session_id}",'
            f'"message":"正在检索知识库..."}}\n\n'
        )

        # ---- RAG 检索 ----
        rag_refs = []
        try:
            rag_results = default_retriever.retrieve(message, top_k=3, min_similarity=0.3)
            if rag_results:
                rag_refs = [
                    {
                        "title": r["title"],
                        "source": r["source"],
                        "snippet": r["content"][:200],
                        "similarity": r["similarity"],
                    }
                    for r in rag_results
                ]
                yield f'data: {{"type":"progress","progress":0.3,"message":"已检索到 {len(rag_refs)} 个相关知识点"}}\n\n'
            else:
                yield f'data: {{"type":"progress","progress":0.3,"message":"知识库中未找到直接相关的内容，将基于通用知识回答"}}\n\n'
        except Exception as e:
            yield f'data: {{"type":"progress","progress":0.3,"message":"知识库检索暂不可用: {str(e)[:80]}"}}\n\n'

        # ---- TutorAgent 生成（含 RAG 上下文 + 风格） ----
        yield f'data: {{"type":"progress","progress":0.5,"message":"正在生成回答..."}}\n\n'

        try:
            result = await self._agent.tutor_with_rag(
                question=message,
                retriever=default_retriever,
                explanation_style=explanation_style,
                profile=profile,
            )
        except Exception:
            # RAG 降级：直接调用基础 tutor
            result = json.loads(
                await self._agent.tutor(
                    question=message,
                    explanation_style=explanation_style,
                    profile=profile,
                )
            )

        answer = result.get("answer", "")
        used_style = result.get("explanation_style", explanation_style)
        references = result.get("references", rag_refs)
        diagrams = result.get("diagrams", [])

        # ---- SSE: delta (流式输出答案) ----
        # 按句子拆分模拟流式效果
        import re
        sentences = re.split(r'(?<=[。！？\n])', answer)
        for sentence in sentences:
            if sentence:
                escaped = json.dumps(sentence, ensure_ascii=False)
                yield f'data: {{"type":"delta","content":{escaped}}}\n\n'

        # ---- SSE: data (结构化结果) ----
        data_payload = json.dumps({
            "answer": answer,
            "explanation_style": used_style,
            "references": references,
            "diagrams": diagrams,
        }, ensure_ascii=False)
        yield f'data: {{"type":"data","data":{data_payload}}}\n\n'

        # ---- 保存消息 ----
        self._messages.setdefault(session_id, []).append({
            "role": "assistant",
            "content": answer,
            "references": references,
            "style": used_style,
            "created_at": _now_iso(),
        })
        self._touch_session(session_id)

        # ---- SSE: done ----
        yield f'data: {{"type":"done","session_id":"{session_id}"}}\n\n'

    # ---- 内部 ----

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


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
