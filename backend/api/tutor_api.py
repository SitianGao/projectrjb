"""
智能辅导 API
- POST /api/tutor/chat  智能辅导问答（SSE流式）
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def tutor_chat():
    """智能辅导对话，SSE 流式返回"""
    pass
