"""智能辅导 API"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def tutor_chat():
    """智能辅导对话（SSE 流式）"""
    pass


@router.post("/ask")
async def tutor_ask():
    """智能辅导问答（前端兼容）"""
    pass


@router.post("/ask/stream")
async def tutor_ask_stream():
    """流式辅导对话 (SSE)"""
    pass


@router.get("/history/{session_id}")
async def get_tutor_history(session_id: str):
    """获取对话历史"""
    pass


@router.get("/sessions")
async def get_tutor_sessions(student_id: str = ""):
    """获取会话列表"""
    pass


@router.post("/sessions")
async def create_tutor_session():
    """创建新会话"""
    pass


@router.post("/check")
async def submit_answer():
    """提交答案供检查"""
    pass
