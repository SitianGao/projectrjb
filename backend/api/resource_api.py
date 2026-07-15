"""
学习资源 API
- POST /api/resource/generate          生成资源（异步任务）
- POST /api/resource/generate/stream   生成资源（SSE）
- GET  /api/resource/list              资源列表
- GET  /api/resource/types             资源类型
- GET  /api/resource/{resource_id}     获取资源详情
"""
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.openapi_examples import TASK_SUCCESS_EXAMPLE, json_responses, sse_responses
from api.response import ApiError, ok, sse_done, sse_error
from database import SessionLocal, get_db
from deps import resource_service, task_service

router = APIRouter()


class ResourceGenerateRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])
    topic: str = Field(..., examples=["机器学习入门"])
    types: Optional[List[str]] = Field(default=None, examples=[["document", "exercise", "code"]])
    difficulty: str = Field(default="中级", examples=["初级"])
    count: int = Field(default=1, ge=1, le=5)
    path_id: Optional[str] = None


@router.post(
    "/generate",
    responses=json_responses(
        "RESOURCE_GENERATE_FAILED",
        "PATH_NOT_FOUND",
        success_example=TASK_SUCCESS_EXAMPLE,
    ),
)
async def generate_resource(
    request: ResourceGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """生成学习资源，返回 task_id；前端轮询 /api/task/{task_id}/status。"""
    try:
        resource_service.validate_path_ownership(
            db,
            request.student_id,
            request.path_id,
        )
    except ValueError as exc:
        raise ApiError("PATH_NOT_FOUND", str(exc)) from exc

    task = task_service.create("资源生成任务已创建")

    async def run_task():
        db = SessionLocal()
        try:
            def update_progress(progress: int, phase: str, message: str):
                task_service.update(
                    task["task_id"],
                    status="running",
                    progress=progress,
                    phase=phase,
                    message=message,
                )

            update_progress(5, "started", "资源生成任务已开始")
            result = await resource_service.generate_resources(
                db=db,
                student_id=request.student_id,
                topic=request.topic,
                types=request.types,
                difficulty=request.difficulty,
                count=request.count,
                path_id=request.path_id,
                on_progress=update_progress,
            )
            task_service.update(
                task["task_id"],
                status="done",
                progress=100,
                phase="completed",
                message="资源生成完成",
                result=result,
            )
        except Exception as exc:
            task_service.update(
                task["task_id"],
                status="failed",
                progress=100,
                phase="failed",
                message="资源生成失败",
                error={"code": "RESOURCE_GENERATE_FAILED", "message": str(exc)},
            )
        finally:
            db.close()

    background_tasks.add_task(run_task)
    return ok(task, "资源生成任务已创建")


@router.post("/generate/stream", responses=sse_responses("RESOURCE_GENERATE_FAILED"))
async def generate_resource_stream(request: ResourceGenerateRequest):
    """生成学习资源，SSE 流式返回。"""

    async def event_generator():
        db = SessionLocal()
        try:
            async for event in resource_service.generate_stream(
                db=db,
                student_id=request.student_id,
                topic=request.topic,
                types=request.types,
                difficulty=request.difficulty,
                count=request.count,
                path_id=request.path_id,
            ):
                yield event
        except Exception:
            yield sse_error("RESOURCE_GENERATE_FAILED", "资源生成失败，请稍后重试")
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


@router.get("/list", responses=json_responses())
async def list_resources(
    student_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取学生资源列表"""
    return ok(
        resource_service.list_resources(
            db=db,
            student_id=student_id,
            page=page,
            page_size=page_size,
            keyword=keyword,
            resource_type=type,
        )
    )


@router.get("/types", responses=json_responses())
async def get_resource_types():
    """获取支持的资源类型"""
    return ok({
        "items": [
            {"value": "document", "label": "文档"},
            {"value": "exercise", "label": "练习题"},
            {"value": "code", "label": "代码案例"},
            {"value": "mindmap", "label": "思维导图"},
            {"value": "reading", "label": "拓展阅读"},
        ]
    })


@router.post("/{resource_id}/bookmark", responses=json_responses("RESOURCE_NOT_FOUND"))
async def bookmark_resource(resource_id: str, db: Session = Depends(get_db)):
    """收藏资源（前端兼容）"""
    resource = resource_service.get_resource(db, resource_id)
    if not resource:
        raise ApiError("RESOURCE_NOT_FOUND")
    return ok({"resource_id": resource_id, "bookmarked": True})


@router.get("/{resource_id}", responses=json_responses("RESOURCE_NOT_FOUND"))
async def get_resource(resource_id: str, db: Session = Depends(get_db)):
    """获取资源详情"""
    resource = resource_service.get_resource(db, resource_id)
    if not resource:
        raise ApiError("RESOURCE_NOT_FOUND")
    return ok(resource)
