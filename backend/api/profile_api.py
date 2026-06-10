"""
学生画像 API

端点：
- POST /api/profile/{id}/chat/stream  流式对话画像构建（SSE，前端 fetch + reader）
- GET  /api/profile/{id}              获取学生画像
- PUT  /api/profile/{id}              手动更新画像
- DELETE /api/profile/{id}/history    清空对话历史
- GET  /api/profile/{id}/history      获取对话历史
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from database import get_db
from services.profile_service import ProfileService

logger = logging.getLogger(__name__)

router = APIRouter()


# ---- 请求/响应模型 ----

class ChatStreamRequest(BaseModel):
    """流式对话请求体（前端 fetch POST）"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=4096)


class ProfileUpdateRequest(BaseModel):
    """画像更新请求体"""
    profile: dict = Field(..., description="画像数据（6维度）")
    completeness: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


# ---- 依赖注入 ----

_profile_service: Optional[ProfileService] = None


def get_profile_service() -> ProfileService:
    """获取 ProfileService 单例"""
    global _profile_service
    if _profile_service is None:
        raise HTTPException(
            status_code=503,
            detail="ProfileService 未初始化，请检查 LLM 配置（DEEPSEEK_API_KEY 或 OPENAI_API_KEY）",
        )
    return _profile_service


def init_profile_service(llm_client) -> ProfileService:
    """初始化 ProfileService 单例（app.py 启动时调用）"""
    global _profile_service
    _profile_service = ProfileService(llm_client)
    logger.info("ProfileService 已初始化")
    return _profile_service


# ---- 工具函数 ----

def _profile_to_chat_text(profile_result: dict) -> str:
    """将画像结果转为自然语言，作为降级时的助手回复文本"""
    profile = profile_result.get("profile", {})
    parts = ["根据你的描述，我初步分析了你的学习画像：\n"]

    kl = profile.get("knowledge_level", "")
    if kl:
        parts.append(f"📊 **知识水平**：{kl}\n")

    goal = profile.get("learning_goal", "")
    if goal:
        parts.append(f"🎯 **学习目标**：{goal}\n")

    style = profile.get("cognitive_style", "")
    if style and style != "未明确":
        parts.append(f"🧠 **学习风格**：{style}\n")

    weakness = profile.get("weakness", [])
    if weakness:
        parts.append(f"⚠️ **薄弱点**：{'、'.join(weakness)}\n")

    interest = profile.get("interest", [])
    if interest:
        parts.append(f"💡 **兴趣方向**：{'、'.join(interest)}\n")

    pace = profile.get("pace_preference", "")
    if pace:
        parts.append(f"⏱️ **学习节奏**：{pace}\n")

    questions = profile_result.get("next_questions", [])
    if questions:
        parts.append("\n为了更准确地了解你，我想再问问：")
        for i, q in enumerate(questions, 1):
            parts.append(f"\n{i}. {q}")

    return "\n".join(parts)


# ---- 端点 ----

@router.post("/{student_id}/chat/stream")
async def profile_chat_stream(
    student_id: str,
    req: ChatStreamRequest,
    db: Session = Depends(get_db),
    service: ProfileService = Depends(get_profile_service),
):
    """
    流式对话画像构建 —— SSE 格式，前端 useChat hook 直接消费。

    每行格式: data: {"content":"...text chunk..."}\\n\\n

    前端用法（在 useChat.js 中已实现）:
        const response = await fetch(`/api/profile/${studentId}/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });
    """
    logger.info("POST /api/profile/%s/chat/stream", student_id)

    async def event_generator():
        try:
            history = service.get_history(student_id)
            current_profile = service.get_profile(db, student_id)

            raw_response = []
            profile_result = None
            error_handled = False

            # 直接用 ProfileAgent 做流式 chat
            async for chunk in service.agent.chat(
                student_id=student_id,
                message=req.message,
                history=history,
                current_profile=current_profile,
            ):
                if chunk.startswith("data: "):
                    sse_data_str = chunk[len("data: "):].strip()
                    try:
                        sse_data = json.loads(sse_data_str)
                        tt = sse_data.get("type")

                        if error_handled:
                            # 降级后跳过 Agent 后续的 profile_update / done 事件
                            continue

                        if tt == "chat":
                            content = sse_data.get("content", "")
                            if content:
                                raw_response.append(content)
                                yield {
                                    "event": "message",
                                    "data": json.dumps({"content": content}, ensure_ascii=False),
                                }

                        elif tt == "profile_update":
                            profile_result = sse_data.get("profile", {})
                            profile_json = json.dumps(sse_data, ensure_ascii=False)
                            yield {"event": "profile_update", "data": profile_json}

                        elif tt == "error":
                            error_handled = True
                            # LLM 调用失败，生成自然语言降级总结
                            fallback = service.agent._keyword_fallback(
                                student_id, req.message, history
                            )
                            profile_result = fallback
                            summary = _profile_to_chat_text(fallback)
                            yield {
                                "event": "message",
                                "data": json.dumps({"content": summary}, ensure_ascii=False),
                            }
                            profile_json = json.dumps(
                                {"type": "profile_update", "profile": fallback},
                                ensure_ascii=False,
                            )
                            yield {"event": "profile_update", "data": profile_json}

                        elif tt == "done":
                            pass  # handled below

                    except json.JSONDecodeError:
                        if chunk.strip():
                            yield {
                                "event": "message",
                                "data": json.dumps({"content": chunk}, ensure_ascii=False),
                            }

            # 持久化
            service._append_to_history(student_id, req.message)
            if profile_result:
                service._save_profile(db, profile_result)
            elif raw_response:
                parsed = service.agent._parse_llm_json("".join(raw_response))
                if parsed:
                    result = {
                        "student_id": student_id,
                        "profile": parsed.get("profile", {}),
                        "completeness": parsed.get("completeness", 0.3),
                        "confidence": parsed.get("confidence", 0.5),
                        "sources": parsed.get("sources", ["dialogue"]),
                        "next_questions": parsed.get("next_questions", []),
                    }
                    if "learning_history" not in result["profile"]:
                        result["profile"]["learning_history"] = history
                    service._save_profile(db, result)

            yield {"event": "done", "data": '{"done":true}'}

        except Exception as e:
            logger.error("SSE 对话异常 student=%s: %s", student_id, e)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False),
            }
        finally:
            db.close()

    return EventSourceResponse(event_generator())


# ---- 测试用例端点（必须在 /{student_id} 之前注册，避免路由冲突）----

@router.get("/test/cases")
async def get_test_cases():
    """
    返回 profile_cases.py 中三个画像案例的最终画像 JSON。

    用于前端演示和调试。
    """
    import os

    cases_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "test", "profiles_output.json"
    )
    try:
        with open(cases_path, "r", encoding="utf-8") as f:
            cases = json.load(f)
        return {"success": True, "data": cases, "count": len(cases)}
    except FileNotFoundError:
        # 文件不存在时动态生成
        return {"success": False, "data": [], "message": "请先运行 test/profile_cases.py 生成测试数据"}


# ---- 学生画像 CRUD ----

@router.get("/{student_id}")
async def get_profile(
    student_id: str,
    db: Session = Depends(get_db),
    service: ProfileService = Depends(get_profile_service),
):
    """获取学生画像"""
    logger.info("GET /api/profile/%s", student_id)
    result = service.get_profile(db, student_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"学生 {student_id} 的画像不存在")
    return result


@router.put("/{student_id}")
async def update_profile(
    student_id: str,
    body: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    service: ProfileService = Depends(get_profile_service),
):
    """手动更新学生画像"""
    logger.info("PUT /api/profile/%s", student_id)
    update_data = {"profile": body.profile}
    if body.completeness is not None:
        update_data["completeness"] = body.completeness
    if body.confidence is not None:
        update_data["confidence"] = body.confidence
    result = service.update_profile(db, student_id, update_data)
    return result


@router.delete("/{student_id}/history")
async def clear_history(
    student_id: str,
    service: ProfileService = Depends(get_profile_service),
):
    """清空学生对话历史"""
    logger.info("DELETE /api/profile/%s/history", student_id)
    service.clear_history(student_id)
    return {"status": "ok", "message": f"已清空 {student_id} 的对话历史"}


@router.get("/{student_id}/history")
async def get_history(
    student_id: str,
    service: ProfileService = Depends(get_profile_service),
):
    """获取学生对话历史"""
    history = service.get_history(student_id)
    return {"student_id": student_id, "history": history, "count": len(history)}
