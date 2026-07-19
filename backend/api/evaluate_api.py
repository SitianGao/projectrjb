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

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.openapi_examples import json_responses, sse_responses
from api.auth_api import require_user
from api.contextual_resource_jobs import queue_contextual_resource
from api.response import ApiError, ok, sse_done, sse_error
from database import SessionLocal, get_db
from deps import evaluate_service, planner_service, resource_service, task_service
from models.auth import Course
from models.evaluation import EvaluationReport, WrongQuestion

router = APIRouter()


def _sse_event(event_type: str, **payload) -> str:
    """构建 SSE 事件字符串 (delegates to core.sse)."""
    from core.sse import sse_event
    return sse_event(event_type, **payload)


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


class EvaluationResourceRequest(BaseModel):
    knowledge_point: str
    resource_type: str = "exercise"
    diagnosis_reason: str = ""
    difficulty: str = "初级"
    force_regenerate: bool = False
    variant_type: Optional[str] = None


class WrongBookResourceRequest(BaseModel):
    question_ids: list[str]
    resource_type: str = "exercise"
    difficulty: Optional[str] = None
    force_regenerate: bool = False
    variant_type: Optional[str] = None


def _require_owned_course(db: Session, user, course_id: str) -> Course:
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
    if not course:
        raise ApiError("COURSE_NOT_FOUND", "课程不存在或不属于当前登录用户", status_code=404)
    return course


def _require_owned_report(db: Session, user, report_id: str) -> EvaluationReport:
    report = (
        db.query(EvaluationReport)
        .join(Course, Course.id == EvaluationReport.course_id)
        .filter(EvaluationReport.id == report_id, Course.user_id == user.id)
        .first()
    )
    if not report:
        raise ApiError("RESOURCE_NOT_FOUND", "评估报告不存在", status_code=404)
    return report


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
            from core.sse import sse_event, sse_done
            yield sse_event("data", data=report)
            yield sse_done(student_id=request.student_id)

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
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    return ok(evaluate_service.list_reports(
        db, student_id, course_id=course_id, page=page, page_size=page_size,
    ))


@router.get("/reports/{report_id}/compare", responses=json_responses("RESOURCE_NOT_FOUND"))
async def compare_reports(report_id: str, db: Session = Depends(get_db)):
    """对比指定报告与上一版本"""
    comparison = evaluate_service.compare_reports(db, report_id)
    if not comparison:
        from api.response import fail
        return fail("RESOURCE_NOT_FOUND", "评估报告不存在")
    return ok(comparison)


@router.get("/dashboard/{student_id}", responses=json_responses())
async def get_dashboard_summary(
    student_id: str,
    course_id: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """统一仪表盘摘要 —— 首页/路径/评估三页共用"""
    return ok(evaluate_service.get_learning_dashboard_summary(
        db, student_id, course_id=course_id or "", user_id=user_id or "",
    ))


@router.get("/assessment-dashboard", responses=json_responses())
async def get_assessment_dashboard(
    student_id: Optional[str] = None,
    course_id: Optional[str] = None,
    scope: str = "last_30_days",
    stage_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """学习评估仪表盘 —— 供 LearningAssessmentPage 使用。

    至少需要传 student_id 或 course_id 其一；course_id 优先用于解析学生。
    """
    from api.response import fail
    if not student_id and not course_id:
        return fail("VALIDATION_ERROR", "student_id 或 course_id 至少需要提供一个")
    return ok(evaluate_service.build_assessment_dashboard(
        db,
        student_id=student_id or "",
        course_id=course_id,
        scope_type=scope,
        stage_id=stage_id,
    ))


@router.get("/reports/{report_id}/adjustments", responses=json_responses())
async def get_adjustment_status(report_id: str, db: Session = Depends(get_db)):
    """获取某次评估的画像/路径调整状态"""
    from models.evaluation import PathAdjustmentLog, ProfileUpdateLog
    path_adj = (
        db.query(PathAdjustmentLog)
        .filter(PathAdjustmentLog.source_evaluation_id == report_id)
        .all()
    )
    profile_adj = (
        db.query(ProfileUpdateLog)
        .filter(ProfileUpdateLog.source_evaluation_id == report_id)
        .all()
    )
    return ok({
        "report_id": report_id,
        "path_adjustments": [
            {"action": a.action, "knowledge_point": a.knowledge_point, "status": a.status, "reason": a.reason}
            for a in path_adj
        ],
        "profile_updates": [
            {"field": u.field, "status": u.status, "confidence": u.confidence, "reason": u.reason}
            for u in profile_adj
        ],
    })


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
async def preview_path_adjustment(
    report_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    _require_owned_report(db, user, report_id)
    report = evaluate_service.get_report_by_id(db, report_id)
    return ok({
        "evaluation_id": report_id,
        "status": "preview",
        "adjustments": report.get("path_adjustments") or report.get("pathAdjustments") or [],
        "message": "这是路径调整草案，尚未修改学习路径。",
    })


@router.post("/reports/{report_id}/path-adjustments/apply", responses=json_responses("RESOURCE_NOT_FOUND"))
async def apply_path_adjustment(
    report_id: str,
    background_tasks: BackgroundTasks,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    report_row = _require_owned_report(db, user, report_id)
    report = evaluate_service.get_report_by_id(db, report_id)
    suggestions = report.get("path_adjustments") or report.get("pathAdjustments") or []
    if isinstance(suggestions, dict):
        suggestions = suggestions.get("adjustments") or []
    applied = planner_service.apply_evaluation_adjustments(
        db,
        user_id=user.id,
        course_id=report_row.course_id,
        evaluation_id=report_id,
        suggestions=suggestions,
    )
    jobs = []
    for item in applied:
        jobs.append(queue_contextual_resource(
            background_tasks=background_tasks,
            task_service=task_service,
            resource_service=resource_service,
            owner_user_id=user.id,
            course_id=report_row.course_id,
            learning_task=item,
            topic=item.get("knowledge_point") or item.get("topic"),
            resource_type=item.get("suggested_resource_type") or item.get("resource_type") or "exercise",
            trigger_source="path_adjustment",
            trigger_context={
                "source_evaluation_id": report_id,
                "adjustment_key": item["adjustment_key"],
                "diagnosis_reason": item.get("reason") or "",
            },
            difficulty=item.get("difficulty") or "初级",
        ))
    return ok({
        "evaluation_id": report_id,
        "status": "generating" if jobs else "ready",
        "applied": applied,
        "jobs": jobs,
        "message": "路径任务已更新，相关资源正在后台准备。" if jobs else "当前没有需要应用的路径调整。",
    })


@router.post("/reports/{report_id}/resources", responses=json_responses("RESOURCE_NOT_FOUND"))
async def create_evaluation_resource(
    report_id: str,
    request: EvaluationResourceRequest,
    background_tasks: BackgroundTasks,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    report = _require_owned_report(db, user, report_id)
    learning_task = planner_service.create_contextual_task(
        db,
        user_id=user.id,
        course_id=report.course_id,
        source_key=f"evaluation:{report_id}",
        topic=request.knowledge_point,
        resource_type=request.resource_type,
        reason=request.diagnosis_reason or "根据学习评估薄弱点生成",
        difficulty=request.difficulty,
        trigger_source="evaluation",
    )
    job = queue_contextual_resource(
        background_tasks=background_tasks,
        task_service=task_service,
        resource_service=resource_service,
        owner_user_id=user.id,
        course_id=report.course_id,
        learning_task=learning_task,
        topic=request.knowledge_point,
        resource_type=request.resource_type,
        trigger_source="evaluation",
        trigger_context={
            "source_evaluation_id": report_id,
            "knowledge_point": request.knowledge_point,
            "diagnosis_reason": request.diagnosis_reason,
        },
        difficulty=request.difficulty,
        force_regenerate=request.force_regenerate,
        variant_type=request.variant_type,
    )
    return ok(job, "专项学习任务已创建")


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
    student_id: Optional[str] = None,
    status: Optional[str] = None,
    course_id: Optional[str] = None,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    owned_courses = db.query(Course).filter(Course.user_id == user.id).all()
    if course_id:
        owned_courses = [course for course in owned_courses if course.id == course_id]
        if not owned_courses:
            raise ApiError("COURSE_NOT_FOUND", "课程不存在或不属于当前登录用户", status_code=404)
    student_ids = [course.student_id for course in owned_courses]
    query = db.query(WrongQuestion).filter(WrongQuestion.student_id.in_(student_ids))
    if status:
        if status == "unmastered":
            query = query.filter(WrongQuestion.status.in_(["unmastered", "pending", "reviewing"]))
        else:
            query = query.filter(WrongQuestion.status == status)
    rows = query.order_by(WrongQuestion.created_at.desc()).all()
    course_by_student = {course.student_id: course for course in owned_courses}
    items = []
    for row in rows:
        item = _wrong_question_to_dict(row)
        course = course_by_student.get(row.student_id)
        item["course_id"] = course.id if course else None
        item["course_title"] = course.title if course else None
        items.append(item)
    return ok({"items": items, "total": len(items)})


@router.patch("/wrong-book/{question_id}", responses=json_responses())
async def update_wrong_question(
    question_id: str,
    request: WrongQuestionUpdateRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    owned_students = db.query(Course.student_id).filter(Course.user_id == user.id)
    query = db.query(WrongQuestion).filter(
        WrongQuestion.id == question_id,
        WrongQuestion.student_id.in_(owned_students),
    )
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


@router.post("/wrong-book/resources", responses=json_responses("RESOURCE_NOT_FOUND"))
async def create_wrong_book_resource(
    request: WrongBookResourceRequest,
    background_tasks: BackgroundTasks,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    unique_ids = list(dict.fromkeys(request.question_ids))
    owned_students = db.query(Course.student_id).filter(Course.user_id == user.id)
    rows = (
        db.query(WrongQuestion)
        .filter(
            WrongQuestion.id.in_(unique_ids),
            WrongQuestion.student_id.in_(owned_students),
        )
        .all()
    )
    if not rows or len(rows) != len(unique_ids):
        raise ApiError("RESOURCE_NOT_FOUND", "错题不存在或不属于当前登录用户", status_code=404)
    student_ids = {row.student_id for row in rows}
    if len(student_ids) != 1:
        raise ApiError("COURSE_SCOPE_MISMATCH", "请选择同一课程下的错题", status_code=422)
    course = db.query(Course).filter(
        Course.user_id == user.id,
        Course.student_id == rows[0].student_id,
    ).first()
    topic_counts = {}
    for row in rows:
        topic_counts[row.topic or "综合知识"] = topic_counts.get(row.topic or "综合知识", 0) + 1
    topic = max(topic_counts, key=topic_counts.get)
    difficulty = request.difficulty or rows[0].difficulty or "初级"
    source_key = "wrong_book:" + ",".join(sorted(unique_ids))
    learning_task = planner_service.create_contextual_task(
        db,
        user_id=user.id,
        course_id=course.id,
        source_key=source_key,
        topic=topic,
        resource_type=request.resource_type,
        reason=f"针对 {len(rows)} 道真实错题的薄弱点训练",
        difficulty=difficulty,
        trigger_source="wrong_book",
    )
    job = queue_contextual_resource(
        background_tasks=background_tasks,
        task_service=task_service,
        resource_service=resource_service,
        owner_user_id=user.id,
        course_id=course.id,
        learning_task=learning_task,
        topic=topic,
        resource_type=request.resource_type,
        trigger_source="wrong_book",
        trigger_context={
            "wrong_question_ids": unique_ids,
            "knowledge_point": topic,
            "wrong_count": sum(row.wrong_count or 0 for row in rows),
            "user_answers": [row.user_answer for row in rows],
            "correct_answers": [row.correct_answer for row in rows],
        },
        difficulty=difficulty,
        force_regenerate=request.force_regenerate,
        variant_type=request.variant_type,
    )
    return ok(job, "错题专项学习任务已创建")


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
