"""
智能辅导 API
- POST /api/tutor/chat        智能辅导问答（SSE）
- POST /api/tutor/ask/stream  流式辅导对话（前端兼容）
- GET  /api/tutor/sessions    获取会话列表
- POST /api/tutor/sessions    创建会话
"""
from typing import List, Literal, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.response import ok, sse_done, sse_error
from database import SessionLocal
from deps import tutor_service

router = APIRouter()

TUTOR_SSE_RESPONSES = {
    200: {
        "description": "SSE stream: start/delta/data/error/done",
        "content": {
            "text/event-stream": {
                "example": (
                    'data: {"type":"start","session_id":"...","message":"开始生成辅导回复"}\n\n'
                    'data: {"type":"delta","content":"...","delta":"..."}\n\n'
                    'data: {"type":"data","data":{"answer":"...","explanation_style":"analogy",'
                    '"references":[],"diagrams":[],"session_id":"..."}}\n\n'
                    'data: {"type":"done","session_id":"..."}\n\n'
                )
            }
        },
    },
    422: {
        "description": "统一参数错误",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": True,
                    "code": "VALIDATION_ERROR",
                    "message": "Field required",
                }
            }
        },
    },
}


class TutorChatRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])
    message: str = Field(..., examples=["请解释一下二次函数的顶点式"])
    session_id: Optional[str] = None
    history: Optional[List[str]] = None
    explanation_style: Literal["auto", "analogy", "formula", "visual", "story"] = Field(
        default="auto",
        examples=["auto"],
    )
    top_k: int = Field(default=3, ge=1, le=8, examples=[3])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "student_id": "demo-student-01",
                    "message": "请用类比法解释一下二次函数顶点式",
                    "session_id": None,
                    "history": [],
                    "explanation_style": "analogy",
                    "top_k": 3,
                }
            ]
        }
    }


class TutorSessionRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])
    title: Optional[str] = None


async def _stream_tutor_response(request: TutorChatRequest):
    async def event_generator():
        db = SessionLocal()
        try:
            async for event in tutor_service.chat_stream(
                db=db,
                student_id=request.student_id,
                message=request.message,
                session_id=request.session_id,
                history=request.history,
                explanation_style=request.explanation_style,
                top_k=request.top_k,
            ):
                yield event
        except Exception:
            yield sse_error("TUTOR_CHAT_FAILED", "智能辅导失败，请稍后重试")
            yield sse_done()
        finally:
            db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat", responses=TUTOR_SSE_RESPONSES)
async def tutor_chat(request: TutorChatRequest):
    """智能辅导对话，SSE 流式返回"""
    return await _stream_tutor_response(request)


@router.post("/ask", responses=TUTOR_SSE_RESPONSES)
async def tutor_ask(request: TutorChatRequest):
    """智能辅导问答（前端兼容，非流式入口返回 SSE）"""
    return await _stream_tutor_response(request)


@router.post("/ask/stream", responses=TUTOR_SSE_RESPONSES)
async def tutor_ask_stream(request: TutorChatRequest):
    """流式辅导对话 (SSE, 前端兼容)"""
    return await _stream_tutor_response(request)


@router.get("/history/{session_id}")
async def get_tutor_history(session_id: str):
    """获取对话历史"""
    return ok({"session_id": session_id, "messages": []})


@router.get("/sessions")
async def list_tutor_sessions(student_id: str):
    """获取辅导会话列表。"""
    return ok(tutor_service.list_sessions(student_id))


@router.post("/sessions")
async def create_tutor_session(request: TutorSessionRequest):
    """创建辅导会话。"""
    return ok(tutor_service.create_session(request.student_id, request.title), "会话已创建")


@router.post("/check")
async def submit_answer():
    """提交答案供检查（前端兼容）"""
    return ok({"status": "ok", "correct": None, "feedback": "答案检查功能待 EvaluateAgent 接入。"})
