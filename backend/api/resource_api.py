"""
学习资源 API
- POST /api/resource/generate          生成资源（异步任务）
- POST /api/resource/generate/stream   生成资源（SSE）
- GET  /api/resource/list              资源列表
- GET  /api/resource/types             资源类型
- GET  /api/resource/{resource_id}     获取资源详情
"""
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

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


@router.post("/generate")
async def generate_resource(
    request: ResourceGenerateRequest,
    background_tasks: BackgroundTasks,
):
    """生成学习资源，返回 task_id；前端轮询 /api/task/{task_id}/status。"""
    task = task_service.create("资源生成任务已创建")

    async def run_task():
        db = SessionLocal()
        try:
            task_service.update(task["task_id"], status="running", progress=20, message="正在生成学习资源")
            result = await resource_service.generate_resources(
                db=db,
                student_id=request.student_id,
                topic=request.topic,
                types=request.types,
                difficulty=request.difficulty,
                count=request.count,
                path_id=request.path_id,
            )
            task_service.update(
                task["task_id"],
                status="done",
                progress=100,
                message="资源生成完成",
                result=result,
            )
        except Exception as exc:
            task_service.update(
                task["task_id"],
                status="failed",
                progress=100,
                message="资源生成失败",
                error={"code": "RESOURCE_GENERATE_FAILED", "message": str(exc)},
            )
        finally:
            db.close()

    background_tasks.add_task(run_task)
    return task


@router.post("/generate/stream")
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
            ):
                yield event
        except Exception as exc:
            yield f'data: {{"type":"error","code":"RESOURCE_GENERATE_FAILED","message":"资源生成失败: {str(exc)}"}}\n\n'
            yield f'data: {{"type":"done"}}\n\n'
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


@router.get("/list")
async def list_resources(
    student_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取学生资源列表"""
    return resource_service.list_resources(
        db=db,
        student_id=student_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        resource_type=type,
    )


@router.get("/types")
async def get_resource_types():
    """获取支持的资源类型"""
    return {
        "items": [
            {"value": "document", "label": "文档"},
            {"value": "exercise", "label": "练习题"},
            {"value": "code", "label": "代码案例"},
            {"value": "mindmap", "label": "思维导图"},
            {"value": "reading", "label": "拓展阅读"},
        ]
    }


@router.post("/{resource_id}/bookmark")
async def bookmark_resource(resource_id: str, db: Session = Depends(get_db)):
    """收藏资源（前端兼容）"""
    resource = resource_service.get_resource(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="学习资源不存在")
    return {"resource_id": resource_id, "bookmarked": True}


@router.get("/{resource_id}")
async def get_resource(resource_id: str, db: Session = Depends(get_db)):
    """获取资源详情"""
    resource = resource_service.get_resource(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="学习资源不存在")
    return resource
