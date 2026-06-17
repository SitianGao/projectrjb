"""
学习路径规划 API
- POST /api/planner/generate  生成学习路径（SSE 流式）
- GET  /api/planner/{student_id}  获取当前学习路径
"""
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.response import ApiError, ok, sse_done, sse_error
from database import SessionLocal, get_db
from deps import planner_service, profile_service

router = APIRouter()


# ── Pydantic 请求模型 ───────────────────────

class GeneratePathRequest(BaseModel):
    student_id: str
    goal: Optional[str] = None


# ── 端点实现 ─────────────────────────────────

@router.post("/generate")
async def generate_path(request: GeneratePathRequest):
    """生成学习路径，SSE 流式返回"""

    async def event_generator():
        db = SessionLocal()
        try:
            # 确保学生存在
            profile_service.get_or_create_student(db, request.student_id)

            async for event in planner_service.generate_stream(
                db=db,
                student_id=request.student_id,
                goal=request.goal,
            ):
                yield event
        except Exception:
            yield sse_error("PLANNER_GENERATE_FAILED", "学习路径生成失败，请稍后重试")
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


@router.get("/{student_id}")
async def get_path(student_id: str, db: Session = Depends(get_db)):
    """获取学生当前学习路径"""
    path = planner_service.get_current_path(db, student_id)
    if not path:
        raise ApiError("PATH_NOT_FOUND", "学习路径未找到，请先生成路径", 404)
    return ok(path)
