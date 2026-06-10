"""
学生画像 API
- POST /api/profile/chat  对话式画像构建（SSE流式）
- GET  /api/profile/{id}  获取学生画像
- PUT  /api/profile/{id}  更新画像
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def profile_chat():
    """对话式画像构建，SSE 流式返回"""
    pass


@router.get("/{student_id}")
async def get_profile(student_id: str):
    """获取学生画像"""
    pass


@router.put("/{student_id}")
async def update_profile(student_id: str):
    """更新学生画像"""
    pass
