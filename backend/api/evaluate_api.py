"""学习评估 API"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/start")
async def start_evaluation():
    """开始学习评估"""
    pass


@router.post("/generate")
async def generate_evaluation():
    """生成评估报告（前端兼容）"""
    pass


@router.post("/generate/stream")
async def generate_evaluation_stream():
    """流式生成评估 (SSE)"""
    pass


@router.get("/report/{student_id}")
async def get_report(student_id: str):
    """获取评估报告"""
    pass


@router.get("/{student_id}")
async def get_evaluation(student_id: str):
    """获取学生评估（前端兼容）"""
    pass


@router.get("/{student_id}/history")
async def get_evaluation_history(student_id: str):
    """获取评估历史"""
    pass


@router.get("/{student_id}/progress")
async def get_progress_stats(student_id: str):
    """获取学习进度统计"""
    pass


@router.post("/record")
async def record_learning():
    """提交学习记录"""
    pass


@router.post("/self")
async def submit_self_eval():
    """提交自评（前端兼容）"""
    pass
