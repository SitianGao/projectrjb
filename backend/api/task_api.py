"""
异步任务 API
- GET /api/task/{task_id}/status  查询异步任务进度
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/{task_id}/status")
async def get_task_status(task_id: str):
    """查询异步任务状态（轮询用）"""
    pass
