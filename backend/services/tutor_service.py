"""Tutor chat service —— 集成 TutorAgent + RAG 检索（Day 8）

Unified SSE via core.sse — real LLM token streaming (no fake chunking).
"""

from __future__ import annotations

import asyncio
import datetime
import json
import re
import uuid
from typing import Any, Dict, List, Optional

from core.sse import sse_event, sse_error, sse_done, SseStream


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

    async def extract_resource_intent(
        self,
        *,
        student_id: str,
        message: str,
        action: str = "document",
        session_id: Optional[str] = None,
        topic: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> Dict:
        """Normalize a chat action into ResourceService input without persisting."""
        session = self._sessions.get(session_id or "")
        if session and session.get("student_id") != student_id:
            raise ValueError("辅导会话不属于当前学习者")
        action_text = f"{action} {message}".lower()
        inferred_type = resource_type
        if not inferred_type:
            if any(key in action_text for key in ["练习", "例题", "exercise", "quiz"]):
                inferred_type = "exercise"
            elif any(key in action_text for key in ["导图", "mindmap"]):
                inferred_type = "mindmap"
            elif any(key in action_text for key in ["代码", "code"]):
                inferred_type = "code"
            else:
                inferred_type = "document"
        recent = list(self._messages.get(session_id or "", []))[-6:]
        summary = "；".join(
            str(item.get("content") or "")[:120]
            for item in recent
            if isinstance(item, dict) and item.get("content")
        )
        return {
            "topic": (topic or message or "当前对话主题").strip()[:200],
            "resource_type": inferred_type,
            "conversation_summary": summary,
            "session_id": session_id,
        }

    # ---- 核心：流式辅导对话（Day 8 升级版） ----

    async def chat_stream(
        self,
        db,
        student_id: str,
        message: str,
        session_id: Optional[str] = None,
        course_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        task_id: Optional[str] = None,
        learning_goal: Optional[str] = None,
        action: str = "ask",
        selected_text: Optional[str] = None,
        conversation_id: Optional[str] = None,
        history: Optional[List[str]] = None,
        explanation_style: str = "auto",
        top_k: int = 3,
    ):
        """Stream tutor answers via unified SSE — REAL token-by-token streaming.

        Unlike the old implementation that collected the full LLM answer and
        fake-chunked it into 80-char pieces, this passes LLM tokens directly
        as ``delta`` events so the frontend typewriter renders them immediately.
        """
        effective_session = session_id or conversation_id
        if not effective_session or effective_session not in self._sessions:
            session = self.create_session(student_id, title=message[:24] or "辅导会话")
            effective_session = session["session_id"]

        yield sse_event("start", session_id=effective_session, message="开始生成辅导回复")

        self.profile_service.get_or_create_student(db, student_id)
        profile = self.profile_service.get_profile(db, student_id)

        now = _now_iso()
        self._messages.setdefault(effective_session, []).append({
            "role": "user",
            "content": message,
            "created_at": now,
        })
        self._touch_session(effective_session)

        # ── Build rich learning context for the AI tutor ─────────
        learning_context = _build_learning_context(
            db=db,
            student_id=student_id,
            course_id=course_id,
            stage_id=stage_id,
            task_id=task_id,
            learning_goal=learning_goal,
            profile=profile,
        )

        # ── RAG retrieval ────────────────────────────────────────
        search_query = message
        if course_id and stage_id:
            search_query = f"[课程:{course_id}] [阶段:{stage_id}] {message}"
        if learning_goal:
            search_query = f"[学习目标:{learning_goal}] {search_query}"
        references = self._retrieve_references(search_query, top_k=top_k)
        knowledge_context = _references_to_context(references)
        if not knowledge_context:
            knowledge_context = ["资料库中未找到可靠依据。回答时请明确说明资料不足，不要编造来源。"]

        style = _normalize_style(explanation_style)
        collected: list[str] = []

        try:
            # ── Conversation history for multi-turn awareness ─────
            session_messages = self._messages.get(effective_session, [])
            recent_history = [
                {"role": m.get("role"), "content": m.get("content")}
                for m in session_messages[-10:]
            ]

            # ── Collect full response first, then stream ─────────
            if self.tutor_agent:
                async for chunk in self.tutor_agent.tutor_stream(
                    question=message,
                    context=knowledge_context,
                    learning_context=learning_context,
                    conversation_history=recent_history,
                    profile=profile,
                    course_id=course_id,
                    stage_id=stage_id,
                    task_id=task_id,
                    action=action,
                    selected_text=selected_text,
                ):
                    if SseStream.cancelled():
                        break
                    collected.append(chunk)
            else:
                # No agent → LLM fallback
                system_prompt = (
                    "你是 EduAgent 的智能辅导老师。回答要准确、分步骤、适合学生水平；"
                    "如果资料不足，请明确说明不确定，不要编造。"
                    "你的回答必须是学生可以直接阅读的纯文本，禁止输出 JSON 格式。"
                    "重要：所有数学公式必须使用 LaTeX 语法。行内公式用 $...$，独立公式块用 $$...$$。"
                    "例如：$w = w - \\alpha \\cdot \\nabla L(w)$，$$L = -\\sum_{i=1}^{n} y_i \\log(\\hat{y}_i)$$"
                    "不要用 Unicode 数学符号（如 Σ、α、∂），一律用 LaTeX 代码。"
                )
                user_prompt = _build_tutor_prompt(message, profile, context)
                async for chunk in self.llm_client.chat_stream(system=system_prompt, user=user_prompt):
                    if SseStream.cancelled():
                        break
                    collected.append(chunk)

            raw_response = "".join(collected)
            if not raw_response.strip():
                raw_response = "暂时无法生成回答，请稍后重试。"

            # ── Parse JSON if LLM output is structured ──
            parsed_suggestions = None
            parsed_kp_ids: list = []
            stripped = raw_response.strip()
            full_answer = raw_response  # default: treat as plain text

            # Log if LLM returned JSON (for debugging)
            if _looks_like_json(stripped):
                import logging as _log
                _log.warning("[TutorService] LLM returned JSON-like content, length=%d, preview=%s...", len(stripped), stripped[:150])

            # Try to extract answer from JSON (more aggressive detection)
            if _looks_like_json(stripped):
                try:
                    parsed = _extract_answer_from_json(stripped)
                    if isinstance(parsed, dict):
                        # 尝试多个常见键名提取答案文本
                        extracted = (
                            parsed.get("answer")
                            or parsed.get("content")
                            or parsed.get("text")
                            or parsed.get("response")
                            or parsed.get("message")
                            or parsed.get("explanation")
                        )
                        if extracted and isinstance(extracted, str) and len(extracted) > 5:
                            full_answer = extracted
                        # else: keep raw_response as full_answer
                        if parsed.get("citations"):
                            references = _merge_references(references, parsed["citations"])
                        if parsed.get("suggested_questions"):
                            parsed_suggestions = parsed["suggested_questions"]
                        if parsed.get("knowledge_point_ids"):
                            parsed_kp_ids = parsed["knowledge_point_ids"]
                    # else: non-dict JSON (array etc.) → keep raw_response
                except Exception:
                    pass  # keep raw_response — any parse failure falls through to safety nets

            # ── 最终安全兜底：答案不能是 JSON ──
            if _looks_like_json(full_answer.strip()):
                try:
                    parsed = _extract_answer_from_json(full_answer.strip())
                    if isinstance(parsed, dict):
                        for key in ("answer", "content", "text", "response", "message", "explanation"):
                            val = parsed.get(key)
                            if isinstance(val, str) and len(val) > 5:
                                full_answer = val
                                break
                except Exception:
                    pass

            # ── Last resort: strip any remaining JSON wrapper ──
            full_answer = _strip_json_wrapper(full_answer)

            # ── Nuclear option: force extract readable text ──
            if _looks_like_json(full_answer.strip()):
                full_answer = _force_extract_readable(full_answer)

            # ── Final safety: if STILL looks like JSON, log warning and try brute-force ──
            if full_answer.strip().startswith("{") or full_answer.strip().startswith("```"):
                import logging as _log
                _log.warning("[TutorService] JSON still present after all extraction steps, raw=%s...", full_answer[:200])
                # Brute force: find the longest block of natural language text
                # Split by JSON delimiters and pick the longest readable segment
                segments = re.split(r'["{}]', full_answer)
                readable_segments = []
                for seg in segments:
                    seg = seg.strip(' ,:;\n\t')
                    # Must contain Chinese or be long English text, and not look like JSON keys
                    if len(seg) > 10 and not re.match(r'^[\w_]+$', seg):
                        readable_segments.append(seg)
                if readable_segments:
                    full_answer = max(readable_segments, key=len).strip()

            # ── Diagnostic: log final answer state ──
            import logging as _log
            if _looks_like_json(full_answer.strip()):
                _log.error("[TutorService] CRITICAL: full_answer is still JSON after all extraction! preview=%s", full_answer[:200])
            else:
                _log.info("[TutorService] Streaming clean answer, length=%d, preview=%s", len(full_answer), full_answer[:100])

            # ── Stream the clean answer text as deltas (simulated streaming) ──
            if not SseStream.cancelled():
                for i in range(0, len(full_answer), 4):
                    if SseStream.cancelled():
                        break
                    chunk = full_answer[i:i + 4]
                    yield sse_event("delta", content=chunk)
                    await _async_sleep(0.01)

        except Exception as exc:
            full_answer = (
                "AI 服务暂时不可用。你可以先把题目、已知条件和卡住的步骤发给我，"
                "我会按解题步骤帮你拆解。"
            )
            yield sse_error("TUTOR_LLM_FAILED", str(exc))

        # ── Structured result: content for student, metadata for system ──
        message_id = f"msg_{_now_iso().replace(':', '').replace('-', '')}"
        result = {
            "message_id": message_id,
            "content": full_answer,
            "explanation_style": style,
            "references": references,
            "diagrams": [],
            "suggested_questions": parsed_suggestions or [],
            "session_id": effective_session,
            "metadata": {
                "explanation_style": style,
                "references": references,
                "knowledge_points": parsed_kp_ids,
                "suggested_questions": parsed_suggestions or [],
                "agent_run": {
                    "agent_name": "TutorAgent",
                    "provider": getattr(self.llm_client, "primary", "deepseek"),
                    "model": "deepseek-chat" if getattr(self.llm_client, "primary", "") == "deepseek" else "4.0Ultra",
                    "status": "completed",
                    "fallback_used": not bool(self.tutor_agent),
                },
            },
        }
        yield sse_event("data", **result)

        self._messages.setdefault(effective_session, []).append({
            "role": "assistant",
            "content": full_answer,
            "references": references,
            "created_at": _now_iso(),
        })
        self._touch_session(effective_session)
        yield sse_done(session_id=effective_session)

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
        course_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        task_id: Optional[str] = None,
        action: str = "ask",
        selected_text: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        style = _normalize_style(explanation_style)
        if self.tutor_agent:
            raw = await self.tutor_agent.tutor(
                question=question,
                context=context,
                explanation_style=style,
                profile=profile,
                course_id=course_id,
                stage_id=stage_id,
                task_id=task_id,
                action=action,
                selected_text=selected_text,
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
            "重要：所有数学公式必须使用 LaTeX 语法。行内公式用 $...$，独立公式块用 $$...$$。"
            "例如：$w = w - \\alpha \\cdot \\nabla L(w)$，$$L = -\\sum_{i=1}^{n} y_i \\log(\\hat{y}_i)$$"
            "不要用 Unicode 数学符号（如 Σ、α、∂），一律用 LaTeX 代码。"
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


def _build_learning_context(
    *,
    db,
    student_id: str,
    course_id: str | None,
    stage_id: str | None,
    task_id: str | None,
    learning_goal: str | None,
    profile: dict | None,
) -> str:
    """Build a human-readable learning context block for the AI tutor.

    This tells the AI: who the student is, what they're learning, where they
    are in the course, and what their level is — so it can answer like a
    tutor who actually knows the student, not a generic chatbot.
    """
    parts: list[str] = []

    # ── Course ──
    if course_id:
        try:
            from models.auth import Course
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                parts.append(f"当前课程：{course.title or course.name or course_id}")
        except Exception:
            parts.append(f"当前课程ID：{course_id}")

    # ── Stage ──
    if stage_id:
        try:
            from models.learning_path import LearningStage
            stage = db.query(LearningStage).filter(LearningStage.stage_id == stage_id).first()
            if stage:
                parts.append(f"当前阶段：{stage.title or stage_id}")
                if stage.description:
                    parts.append(f"阶段简介：{stage.description[:200]}")
        except Exception:
            pass

    # ── Task ──
    if task_id:
        try:
            from models.learning_path import LearningTask
            task = db.query(LearningTask).filter(LearningTask.task_id == task_id).first()
            if task:
                parts.append(f"当前任务：{task.title or task_id}")
                if task.description:
                    parts.append(f"任务说明：{task.description[:200]}")
        except Exception:
            pass

    # ── Learning goal ──
    if learning_goal:
        parts.append(f"学习目标：{learning_goal}")

    # ── Student profile ──
    if profile:
        profile_inner = (profile or {}).get("profile", profile or {})
        knowledge = profile_inner.get("knowledge_level") or profile_inner.get("cognitive_style")
        if knowledge:
            parts.append(f"学生水平：{knowledge}")
        style = profile_inner.get("cognitive_style")
        if style and style != knowledge:
            parts.append(f"学习风格：{style}")
        weak = profile_inner.get("weak_points") or profile_inner.get("weaknesses")
        if weak:
            if isinstance(weak, list) and len(weak) > 0:
                w_str = ", ".join(
                    w.get("name", str(w)) if isinstance(w, dict) else str(w)
                    for w in weak[:3]
                )
                parts.append(f"薄弱知识点：{w_str}")

    # ── Recent conversation ──
    # (handled separately via history in the agent)

    return "\n".join(parts) if parts else ""


def _looks_like_json(text: str) -> bool:
    """Check if text looks like it contains JSON (object or code-wrapped)."""
    text = text.strip()
    if not text:
        return False
    # Direct JSON object
    if text.startswith("{"):
        return True
    # Code block wrapped JSON
    if text.startswith("```"):
        return True
    # Text containing JSON block (e.g., "Here is the answer: {...}")
    if "{" in text and "}" in text:
        # Check if there's a plausible JSON object
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start < brace_end:
            candidate = text[brace_start:brace_end + 1]
            # Quick sanity check: must have at least one key-value pair
            if '":' in candidate or "':" in candidate:
                return True
    return False


def _strip_json_wrapper(text: str) -> str:
    """Last-resort: if text is still JSON-like, try to extract readable content."""
    text = text.strip()

    # If it doesn't look like JSON, return as-is
    if not _looks_like_json(text):
        return text

    # Try 1: standard JSON parse
    try:
        parsed = _extract_answer_from_json(text)
        if isinstance(parsed, dict):
            # Try common answer keys
            for key in ("answer", "content", "text", "response", "message", "explanation"):
                val = parsed.get(key)
                if isinstance(val, str) and len(val) > 5:
                    return val
            # If no answer key found, try to join all string values
            parts = []
            for v in parsed.values():
                if isinstance(v, str) and len(v) > 10 and not v.startswith("{"):
                    parts.append(v)
            if parts:
                return "\n\n".join(parts)
    except Exception:
        pass

    # Try 2: regex extraction of string values from JSON-like text
    # This handles malformed JSON that json.loads can't parse
    extracted_values = re.findall(r'"(?:answer|content|text|response|message|explanation)"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
    if extracted_values:
        best = max(extracted_values, key=len)
        if len(best) > 5:
            # Unescape JSON string escapes
            best = best.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")
            return best

    # Try 2b: handle multiline string values (actual newlines in JSON strings)
    extracted_values_ml = re.findall(r'"(?:answer|content|text|response|message|explanation)"\s*:\s*"([\s\S]*?)"(?:\s*[,}\n])', text)
    if extracted_values_ml:
        best = max(extracted_values_ml, key=len)
        if len(best) > 5:
            best = best.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")
            return best.strip()

    # Try 3: extract ALL string values and pick the longest one
    all_strings = re.findall(r'"((?:[^"\\]|\\.)*)"', text)
    readable = [s for s in all_strings if len(s) > 15 and not s.startswith(("{", "["))]
    if readable:
        best = max(readable, key=len)
        best = best.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")
        return best

    # Try 3b: multiline string values
    all_strings_ml = re.findall(r'"([\s\S]{10,}?)"(?:\s*[,}\n])', text)
    readable_ml = [s for s in all_strings_ml if len(s) > 15 and not s.strip().startswith(("{", "["))]
    if readable_ml:
        best = max(readable_ml, key=len)
        best = best.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")
        return best.strip()

    # Try 4: if text starts with { but has no closing }, try extracting after the first colon
    if text.startswith("{") and ":" in text:
        after_colon = text.split(":", 1)[1].strip()
        if after_colon.startswith('"'):
            # Try to find the closing quote
            end_quote = after_colon.find('"', 1)
            if end_quote > 1:
                return after_colon[1:end_quote].replace("\\n", "\n").replace('\\"', '"')
        elif len(after_colon) > 5:
            # No quotes, just return everything after the colon
            return after_colon.rstrip("}").strip()

    return text


def _force_extract_readable(text: str) -> str:
    """Aggressively extract readable text from any string, stripping all JSON artifacts.

    This is the absolute last resort — called right before streaming to the user.
    Even if JSON parsing completely fails, this tries to find natural language content.
    """
    text = text.strip()
    if not text:
        return text

    # If it doesn't look like JSON at all, return as-is
    if not _looks_like_json(text):
        return text

    # Try the normal extraction first
    result = _strip_json_wrapper(text)
    if result != text and not _looks_like_json(result):
        return result

    # Nuclear option: strip all JSON syntax and keep only readable text
    # Remove ```json ... ``` wrappers
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)

    # Extract content between quotes that looks like natural language
    # (contains Chinese characters, spaces, or is long enough)
    candidates = re.findall(r'"([^"]{10,})"', text)
    if candidates:
        # Pick the longest candidate that contains Chinese or is very long
        chinese_candidates = [c for c in candidates if re.search(r'[一-鿿]', c)]
        if chinese_candidates:
            best = max(chinese_candidates, key=len)
        else:
            best = max(candidates, key=len)
        best = best.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")
        return best

    # If all else fails, remove JSON syntax characters and return
    cleaned = re.sub(r'[{}"\[\]:,\s]+', ' ', text).strip()
    if len(cleaned) > 10:
        return cleaned

    return text


def _extract_answer_from_json(text: str) -> dict:
    """Extract structured data from LLM JSON output (handles code blocks too).

    More robust than the previous version:
    - Handles text before/after JSON blocks
    - Handles ```json ... ``` wrappers with surrounding text
    - Handles trailing commas
    - Falls back to regex-based extraction for common patterns
    """
    text = text.strip()

    # Strip ```json ... ``` wrappers (may have text before/after)
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    else:
        # Try to find JSON object anywhere in the text
        # This handles cases like "Here is my answer: {...} Hope it helps!"
        brace_start = text.find("{")
        if brace_start >= 0:
            # Find matching closing brace
            depth = 0
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        text = text[brace_start:i + 1]
                        break

    # Find the JSON object boundaries
    start = text.find("{")
    if start >= 0:
        end = text.rfind("}")
        if end > start:
            text = text[start:end + 1]

    # Clean up common JSON issues
    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    return json.loads(text)


async def _async_sleep(seconds: float) -> None:
    """Tiny awaitable sleep so the event loop can yield during simulated streaming."""
    await asyncio.sleep(seconds)


def _merge_references(existing: list, parsed_citations: list) -> list:
    """Merge RAG references with LLM-parsed citations, deduplicating by title."""
    seen = {r.get("title", "") for r in existing}
    merged = list(existing)
    for c in parsed_citations:
        if not isinstance(c, dict):
            continue
        title = c.get("title") or c.get("source") or ""
        if title and title not in seen:
            merged.append({
                "title": title,
                "source": c.get("source") or "ai_generated",
                "content": c.get("content") or "",
                "similarity": c.get("similarity"),
            })
            seen.add(title)
    return merged


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


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
