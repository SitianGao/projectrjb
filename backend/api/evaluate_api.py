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
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.openapi_examples import json_responses, sse_responses
from api.response import ok, sse_done, sse_error
from database import SessionLocal, get_db
from deps import evaluate_service
from models.evaluation import WrongQuestion

router = APIRouter()


def _sse_event(event_type: str, **payload) -> str:
    """构建 SSE 事件字符串"""
    data = {"type": event_type, **payload}
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (TypeError, json.JSONDecodeError):
        return default


def _wrong_question_to_dict(row: WrongQuestion) -> dict:
    question_text = row.question_text or row.question
    options = _json_loads(row.options, [])
    if isinstance(options, str):
        options = _json_loads(options, [])
    return {
        "id": row.id,
        "student_id": row.student_id,
        "question_id": row.question_id,
        "topic": row.topic,
        "question": question_text,
        "question_text": question_text,
        "options": options,
        "user_answer": row.user_answer,
        "correct_answer": row.correct_answer,
        "explanation": row.explanation,
        "difficulty": row.difficulty,
        "tags": _json_loads(row.tags, []),
        "wrong_count": row.wrong_count or 0,
        "correct_streak": row.correct_streak or 0,
        "status": row.status or "unmastered",
        "last_wrong_at": row.last_wrong_at.isoformat() if row.last_wrong_at else None,
        "next_review_at": row.next_review_at.isoformat() if row.next_review_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


class EvaluationStartRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])
    user_id: Optional[str] = None
    course_id: Optional[str] = None
    stage_id: Optional[str] = None
    scope_type: str = Field(default="last_30_days", examples=["last_30_days"])
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    force: bool = False


class LearningRecordRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])
    action: str = Field(..., examples=["complete"])
    resource_id: Optional[str] = None
    topic: Optional[str] = Field(default=None, examples=["二次函数"])
    score: Optional[float] = Field(default=None, ge=0, le=100)
    time_spent: Optional[int] = Field(default=None, ge=0)


class WrongQuestionUpdateRequest(BaseModel):
    student_id: Optional[str] = None
    user_answer: Optional[str] = None
    status: Optional[str] = None
    correct_streak: Optional[int] = None
    wrong_count: Optional[int] = None


@router.post("/start", responses=json_responses())
async def start_evaluation(
    request: EvaluationStartRequest,
    db: Session = Depends(get_db),
):
    """开始学习评估"""
    return ok(evaluate_service.start_evaluation(db, **request.model_dump(exclude={"user_id"})))


@router.post("/generate", responses=json_responses())
async def generate_evaluation(
    request: EvaluationStartRequest,
    db: Session = Depends(get_db),
):
    """生成评估报告（前端兼容）"""
    return ok(evaluate_service.start_evaluation(db, **request.model_dump(exclude={"user_id"})))


@router.post("/generate/stream", responses=sse_responses("EVALUATE_FAILED"))
async def generate_evaluation_stream(request: EvaluationStartRequest):
    """流式生成评估 (SSE) —— Day 9 升级：异步 AI 增强评估"""

    async def event_generator():
        db = SessionLocal()
        try:
            yield _sse_event("start", message="开始生成学习评估")

            # Day 9: 异步 AI 增强评估
            report = await evaluate_service.start_evaluation_async(db, **request.model_dump(exclude={"user_id"}))

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

        except Exception:
            yield sse_error("EVALUATE_FAILED", "学习评估失败，请稍后重试")
            yield sse_done()
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


@router.get("/report/{student_id}", responses=json_responses())
async def get_report(
    student_id: str,
    course_id: Optional[str] = None,
    scope_type: str = "last_30_days",
    stage_id: Optional[str] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """获取评估报告"""
    return ok(evaluate_service.build_report(
        db,
        student_id,
        course_id=course_id,
        scope_type=scope_type,
        stage_id=stage_id,
        start_at=start_at,
        end_at=end_at,
    ))


@router.get("/reports/{report_id}", responses=json_responses("RESOURCE_NOT_FOUND"))
async def get_report_by_id(report_id: str, db: Session = Depends(get_db)):
    report = evaluate_service.get_report_by_id(db, report_id)
    if not report:
        from api.response import fail
        return fail("RESOURCE_NOT_FOUND", "评估报告不存在")
    return ok(report)


@router.get("/history/{student_id}", responses=json_responses())
async def list_reports(
    student_id: str,
    course_id: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return ok(evaluate_service.list_reports(db, student_id, course_id=course_id, limit=limit))


@router.get("/courses/{course_id}/latest", responses=json_responses())
async def get_course_latest_report(
    course_id: str,
    student_id: str,
    scope_type: str = "last_30_days",
    stage_id: Optional[str] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    return ok(evaluate_service.build_report(
        db,
        student_id,
        course_id=course_id,
        scope_type=scope_type,
        stage_id=stage_id,
        start_at=start_at,
        end_at=end_at,
    ))


@router.post("/reports/{report_id}/path-adjustments/preview", responses=json_responses("RESOURCE_NOT_FOUND"))
async def preview_path_adjustment(report_id: str, db: Session = Depends(get_db)):
    report = evaluate_service.get_report_by_id(db, report_id)
    if not report:
        from api.response import fail
        return fail("RESOURCE_NOT_FOUND", "评估报告不存在")
    return ok({
        "evaluation_id": report_id,
        "status": "preview",
        "adjustments": report.get("path_adjustments") or report.get("pathAdjustments") or [],
        "message": "这是路径调整草案，尚未修改学习路径。",
    })


@router.post("/reports/{report_id}/path-adjustments/apply", responses=json_responses("RESOURCE_NOT_FOUND"))
async def apply_path_adjustment(report_id: str, db: Session = Depends(get_db)):
    report = evaluate_service.get_report_by_id(db, report_id)
    if not report:
        from api.response import fail
        return fail("RESOURCE_NOT_FOUND", "评估报告不存在")
    return ok({
        "evaluation_id": report_id,
        "status": "pending_planner",
        "message": "已确认调整建议；当前版本先返回确认结果，后续由 PlannerAgent 生成路径变更草案。",
    })


@router.get("/progress/{student_id}", responses=json_responses())
async def get_progress(student_id: str, db: Session = Depends(get_db)):
    """获取学习进度统计。"""
    return ok(evaluate_service.get_progress_stats(db, student_id))


@router.get("/record", responses=json_responses())
async def list_learning_records(
    student_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """获取学习记录列表"""
    return ok(evaluate_service.list_records(db, student_id, limit))


@router.get("/wrong-book", responses=json_responses())
async def list_wrong_book(
    student_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(WrongQuestion).filter(WrongQuestion.student_id == student_id)
    if status:
        if status == "unmastered":
            query = query.filter(WrongQuestion.status.in_(["unmastered", "pending", "reviewing"]))
        else:
            query = query.filter(WrongQuestion.status == status)
    rows = query.order_by(WrongQuestion.created_at.desc()).all()
    items = [_wrong_question_to_dict(row) for row in rows]
    return ok({"items": items, "total": len(items)})


@router.patch("/wrong-book/{question_id}", responses=json_responses())
async def update_wrong_question(
    question_id: str,
    request: WrongQuestionUpdateRequest,
    db: Session = Depends(get_db),
):
    query = db.query(WrongQuestion).filter(WrongQuestion.id == question_id)
    if request.student_id:
        query = query.filter(WrongQuestion.student_id == request.student_id)
    row = query.first()
    if not row:
        return ok({"id": question_id, "updated": False})
    for field in ["user_answer", "status", "correct_streak", "wrong_count"]:
        value = getattr(request, field)
        if value is not None:
            setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return ok(_wrong_question_to_dict(row))


@router.get("/{student_id}", responses=json_responses())
async def get_evaluation(student_id: str, db: Session = Depends(get_db)):
    """获取学生评估（前端兼容）"""
    return ok(evaluate_service.build_report(db, student_id))


@router.get("/{student_id}/history", responses=json_responses())
async def get_evaluation_history(student_id: str, db: Session = Depends(get_db)):
    """获取评估历史"""
    return ok(evaluate_service.build_report(db, student_id).get("history", []))


@router.get("/{student_id}/progress", responses=json_responses())
async def get_progress_stats(student_id: str, db: Session = Depends(get_db)):
    """获取学习进度统计（前端兼容）"""
    return ok(evaluate_service.get_progress_stats(db, student_id))


@router.post("/record", responses=json_responses())
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


@router.post("/self", responses=json_responses())
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
