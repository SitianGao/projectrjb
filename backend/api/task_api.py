"""
异步任务 API
- GET /api/task/{task_id}/status  查询异步任务进度
"""
from fastapi import APIRouter

from api.response import ApiError, ok
from deps import task_service

router = APIRouter()


@router.get("/{task_id}/status")
async def get_task_status(task_id: str):
    """查询异步任务状态（轮询用）"""
    task = task_service.get(task_id)
    if not task:
        raise ApiError("TASK_NOT_FOUND", "任务不存在", 404)
    return ok(task)
