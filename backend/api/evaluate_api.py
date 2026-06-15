"""
学习评估 API
- POST /api/evaluate/start         开始评估
- GET  /api/evaluate/report/{id}  获取评估报告
- POST /api/evaluate/record       提交学习记录
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/start")
async def start_evaluation():
    """开始学习评估"""
    pass


@router.get("/report/{student_id}")
async def get_report(student_id: str):
    """获取评估报告"""
    pass


@router.post("/record")
async def record_learning():
    """提交学习记录"""
    pass
