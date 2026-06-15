"""
智能辅导 API
- POST /api/tutor/chat        智能辅导问答（SSE）
- POST /api/tutor/ask/stream  流式辅导对话（前端兼容）
- GET  /api/tutor/sessions    获取会话列表
- POST /api/tutor/sessions    创建会话
"""
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from database import SessionLocal
from deps import tutor_service

router = APIRouter()


class TutorChatRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])
    message: str = Field(..., examples=["请解释一下二次函数的顶点式"])
    session_id: Optional[str] = None
    history: Optional[List[str]] = None


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
            ):
                yield event
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


@router.post("/chat")
async def tutor_chat(request: TutorChatRequest):
    """智能辅导对话，SSE 流式返回"""
    return await _stream_tutor_response(request)


@router.post("/ask")
async def tutor_ask(request: TutorChatRequest):
    """智能辅导问答（前端兼容，非流式入口返回 SSE）"""
    return await _stream_tutor_response(request)


@router.post("/ask/stream")
async def tutor_ask_stream(request: TutorChatRequest):
    """流式辅导对话 (SSE, 前端兼容)"""
    return await _stream_tutor_response(request)


@router.get("/history/{session_id}")
async def get_tutor_history(session_id: str):
    """获取对话历史"""
    return {"session_id": session_id, "messages": []}


@router.get("/sessions")
async def list_tutor_sessions(student_id: str):
    """获取辅导会话列表。"""
    return tutor_service.list_sessions(student_id)


@router.post("/sessions")
async def create_tutor_session(request: TutorSessionRequest):
    """创建辅导会话。"""
    return tutor_service.create_session(request.student_id, request.title)


@router.post("/check")
async def submit_answer():
    """提交答案供检查（前端兼容）"""
    return {"status": "ok", "correct": None, "feedback": "答案检查功能待 EvaluateAgent 接入。"}
