"""
学生画像 API
- POST /api/profile/chat  对话式画像构建（SSE流式）
- GET  /api/profile/{id}  获取学生画像
- PUT  /api/profile/{id}  更新画像
"""
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.openapi_examples import json_responses, sse_responses
from api.response import ApiError, ok, sse_done, sse_error
from database import SessionLocal, get_db
from deps import profile_service

router = APIRouter()


# ── Pydantic 请求模型 ───────────────────────

class ProfileChatRequest(BaseModel):
    student_id: str
    message: str
    history: Optional[List[str]] = None
    current_profile: Optional[Dict] = None


class ProfileUpdateRequest(BaseModel):
    knowledge_level: Optional[str] = None
    learning_goal: Optional[str] = None
    cognitive_style: Optional[str] = None
    weakness: Optional[List[str]] = None
    interest: Optional[List[str]] = None
    pace_preference: Optional[str] = None


class ProfileMessageRequest(BaseModel):
    message: str
    history: Optional[List[str]] = None
    current_profile: Optional[Dict] = None


# ── 端点实现 ─────────────────────────────────

@router.post("/chat", responses=sse_responses("PROFILE_CHAT_FAILED"))
async def profile_chat(request: ProfileChatRequest):
    """对话式画像构建，SSE 流式返回"""

    async def event_generator():
        db = SessionLocal()
        try:
            async for event in profile_service.chat_stream(
                db=db,
                student_id=request.student_id,
                message=request.message,
                history=request.history,
                current_profile=request.current_profile,
            ):
                yield event
        except Exception:
            yield sse_error("PROFILE_CHAT_FAILED", "画像对话失败，请稍后重试")
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


@router.post("/{student_id}/chat/stream", responses=sse_responses("PROFILE_CHAT_FAILED"))
async def profile_chat_stream_by_student(
    student_id: str,
    request: ProfileMessageRequest,
):
    """SSE profile chat endpoint used by the React ProfilePage."""

    async def event_generator():
        db = SessionLocal()
        try:
            async for event in profile_service.chat_stream(
                db=db,
                student_id=student_id,
                message=request.message,
                history=request.history,
                current_profile=request.current_profile,
            ):
                yield event
        except Exception:
            yield sse_error("PROFILE_CHAT_FAILED", "画像对话失败，请稍后重试")
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


@router.post("/{student_id}/chat", responses=sse_responses("PROFILE_CHAT_FAILED"))
async def profile_chat_by_student(
    student_id: str,
    request: ProfileMessageRequest,
):
    """Compatibility endpoint for clients that pass student_id in the URL."""
    return await profile_chat(
        ProfileChatRequest(
            student_id=student_id,
            message=request.message,
            history=request.history,
            current_profile=request.current_profile,
        )
    )


@router.get("/{student_id}", responses=json_responses("PROFILE_NOT_FOUND"))
async def get_profile(student_id: str, db: Session = Depends(get_db)):
    """获取学生画像"""
    profile = profile_service.get_profile(db, student_id)
    if not profile:
        raise ApiError("PROFILE_NOT_FOUND")
    return ok(profile)


@router.put("/{student_id}", responses=json_responses("PROFILE_UPDATE_EMPTY"))
async def update_profile(
    student_id: str,
    request: ProfileUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新学生画像"""
    # 确保学生存在
    profile_service.get_or_create_student(db, student_id)

    # 只更新提供的字段
    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        raise ApiError("PROFILE_UPDATE_EMPTY")

    # 保存画像
    profile_service.save_profile(db, student_id, update_data, increment_version=True)

    # 返回更新后的画像
    return ok(profile_service.get_profile(db, student_id))
