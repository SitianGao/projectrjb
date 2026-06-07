"""
学习路径规划 API
- POST /api/planner/generate  生成学习路径（SSE流式）
- GET  /api/planner/{id}      获取当前学习路径
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate_path():
    """生成学习路径，SSE 流式返回"""
    pass


@router.get("/{student_id}")
async def get_path(student_id: str):
    """获取学生当前学习路径"""
    pass
