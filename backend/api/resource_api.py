"""
学习资源 API
- POST /api/resource/generate   生成资源（异步任务）
- GET  /api/resource/{id}      获取资源详情
- GET  /api/resource/list      资源列表
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate_resource():
    """生成学习资源，返回 task_id"""
    pass


@router.get("/{resource_id}")
async def get_resource(resource_id: str):
    """获取资源详情"""
    pass


@router.get("/list")
async def list_resources(student_id: str):
    """获取学生资源列表"""
    pass
