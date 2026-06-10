"""
学生画像 API
- POST /api/profile/chat  对话式画像构建（SSE流式）
- GET  /api/profile/{id}  获取学生画像
- PUT  /api/profile/{id}  更新画像
"""
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

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


# ── 端点实现 ─────────────────────────────────

@router.post("/chat")
async def profile_chat(request: ProfileChatRequest):
    """对话式画像构建，SSE 流式返回"""

    async def event_generator():
        db = SessionLocal()
        try:
            # 确保学生存在
            profile_service.get_or_create_student(db, request.student_id)

            async for event in profile_service.chat_stream(
                db=db,
                student_id=request.student_id,
                message=request.message,
                history=request.history,
                current_profile=request.current_profile,
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


@router.get("/{student_id}")
async def get_profile(student_id: str, db: Session = Depends(get_db)):
    """获取学生画像"""
    profile = profile_service.get_profile(db, student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="学生画像未找到")
    return profile


@router.put("/{student_id}")
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
        raise HTTPException(status_code=400, detail="没有提供需要更新的字段")

    # 保存画像
    profile_service.save_profile(db, student_id, update_data, increment_version=True)

    # 返回更新后的画像
    return profile_service.get_profile(db, student_id)
