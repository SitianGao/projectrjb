"""
学习评估 API
- POST /api/evaluate/start                  开始评估
- POST /api/evaluate/generate               生成评估报告（兼容前端旧调用）
- POST /api/evaluate/generate/stream        流式生成评估（SSE）
- GET  /api/evaluate/report/{student_id}    获取评估报告
- GET  /api/evaluate/progress/{student_id}  获取学习进度统计
- POST /api/evaluate/record                 提交学习记录
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.response import ok
from database import SessionLocal, get_db
from deps import evaluate_service

router = APIRouter()


def _sse_event(event_type: str, **payload) -> str:
    """构建 SSE 事件字符串"""
    data = {"type": event_type, **payload}
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


class EvaluationStartRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])


class LearningRecordRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])
    action: str = Field(..., examples=["complete"])
    resource_id: Optional[str] = None
    topic: Optional[str] = Field(default=None, examples=["二次函数"])
    score: Optional[float] = Field(default=None, ge=0, le=100)
    time_spent: Optional[int] = Field(default=None, ge=0)


@router.post("/start")
async def start_evaluation(
    request: EvaluationStartRequest,
    db: Session = Depends(get_db),
):
    """开始学习评估"""
    return ok(evaluate_service.start_evaluation(db, request.student_id))


@router.post("/generate")
async def generate_evaluation(
    request: EvaluationStartRequest,
    db: Session = Depends(get_db),
):
    """生成评估报告（前端兼容）"""
    return ok(evaluate_service.start_evaluation(db, request.student_id))


@router.post("/generate/stream")
async def generate_evaluation_stream(request: EvaluationStartRequest):
    """流式生成评估 (SSE) —— Day 9 升级：异步 AI 增强评估"""

    async def event_generator():
        db = SessionLocal()
        try:
            yield _sse_event("start", message="开始生成学习评估")

            # Day 9: 异步 AI 增强评估
            report = await evaluate_service.start_evaluation_async(db, request.student_id)

            # 逐维度发送 delta（前端可逐步渲染雷达图）
            for dim in report.get("dimensions", []):
                yield _sse_event(
                    "delta",
                    dimension=dim.get("name"),
                    score=dim.get("score"),
                    comment=dim.get("comment"),
                )

            # 薄弱点识别完成
            weak_topics = report.get("weak_topics", [])
            if weak_topics:
                yield _sse_event(
                    "delta",
                    weak_topics=weak_topics,
                    message=f"检测到 {len(weak_topics)} 个薄弱知识点",
                )

            # 复习计划
            review_plan = report.get("review_plan", [])
            if review_plan:
                yield _sse_event(
                    "delta",
                    review_plan_count=len(review_plan),
                    message=f"生成 {len(review_plan)} 条复习建议",
                )

            # 最终完整报告
            payload = json.dumps(report, ensure_ascii=False)
            yield f"data: {{\"type\":\"data\",\"data\":{payload}}}\n\n"
            yield f'data: {{"type":"done","session_id":"{request.student_id}"}}\n\n'

        except Exception as exc:
            message = json.dumps(str(exc), ensure_ascii=False)
            yield f'data: {{"type":"error","code":"EVALUATE_FAILED","message":{message}}}\n\n'
            yield 'data: {"type":"done"}\n\n'
        finally:
            db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/report/{student_id}")
async def get_report(student_id: str, db: Session = Depends(get_db)):
    """获取评估报告"""
    return ok(evaluate_service.build_report(db, student_id))


@router.get("/progress/{student_id}")
async def get_progress(student_id: str, db: Session = Depends(get_db)):
    """获取学习进度统计。"""
    return ok(evaluate_service.get_progress_stats(db, student_id))


@router.get("/record")
async def list_learning_records(
    student_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """获取学习记录列表"""
    return ok(evaluate_service.list_records(db, student_id, limit))


@router.get("/{student_id}")
async def get_evaluation(student_id: str, db: Session = Depends(get_db)):
    """获取学生评估（前端兼容）"""
    return ok(evaluate_service.build_report(db, student_id))


@router.get("/{student_id}/history")
async def get_evaluation_history(student_id: str, db: Session = Depends(get_db)):
    """获取评估历史"""
    return ok(evaluate_service.build_report(db, student_id).get("history", []))


@router.get("/{student_id}/progress")
async def get_progress_stats(student_id: str, db: Session = Depends(get_db)):
    """获取学习进度统计（前端兼容）"""
    return ok(evaluate_service.get_progress_stats(db, student_id))


@router.post("/record")
async def record_learning(
    request: LearningRecordRequest,
    db: Session = Depends(get_db),
):
    """提交学习记录"""
    return ok(
        evaluate_service.record_learning(
            db=db,
            student_id=request.student_id,
            action=request.action,
            resource_id=request.resource_id,
            topic=request.topic,
            score=request.score,
            time_spent=request.time_spent,
        ),
        "学习记录已提交",
    )


@router.post("/self")
async def submit_self_eval(
    request: LearningRecordRequest,
    db: Session = Depends(get_db),
):
    """提交自评（前端兼容）"""
    return ok(
        evaluate_service.record_learning(
            db=db,
            student_id=request.student_id,
            action=request.action or "self_eval",
            resource_id=request.resource_id,
            topic=request.topic,
            score=request.score,
            time_spent=request.time_spent,
        ),
        "自评已提交",
    )
