"""学习资源 API"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate_resource():
    """生成学习资源"""
    pass


@router.post("/generate/stream")
async def generate_resource_stream():
    """流式生成学习资源 (SSE)"""
    pass


@router.get("/{resource_id}")
async def get_resource(resource_id: str):
    """获取资源详情"""
    pass


@router.get("/list")
async def list_resources(student_id: str = ""):
    """获取资源列表"""
    pass


@router.get("/types")
async def get_resource_types():
    """获取支持的资源类型"""
    pass


@router.post("/{resource_id}/bookmark")
async def bookmark_resource(resource_id: str):
    """收藏资源"""
    pass
