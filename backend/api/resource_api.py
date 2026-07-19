"""
学习资源 API
- POST /api/resource/generate          生成资源（异步任务）
- POST /api/resource/generate/stream   生成资源（SSE）
- GET  /api/resource/list              资源列表
- GET  /api/resource/types             资源类型
- GET  /api/resource/{resource_id}     获取资源详情
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.openapi_examples import TASK_SUCCESS_EXAMPLE, json_responses, sse_responses
from api.response import ApiError, ok, sse_done, sse_error
from database import SessionLocal, get_db
from api.auth_api import require_user
from deps import classroom_service, resource_service, task_service
from models.auth import Course, User

router = APIRouter()


class ResourceGenerateRequest(BaseModel):
    student_id: Optional[str] = Field(default=None, examples=["demo-student-01"])
    topic: str = Field(..., examples=["机器学习入门"])
    types: Optional[List[str]] = Field(default=None, examples=[["document", "exercise", "code"]])
    resource_type: Optional[str] = None
    difficulty: str = Field(default="中级", examples=["初级"])
    count: int = Field(default=1, ge=1, le=5)
    path_id: Optional[str] = None
    stage_id: Optional[str] = None
    course_id: Optional[str] = None
    task_id: Optional[str] = None


class ContextualResourceRequest(BaseModel):
    resource_type: Optional[str] = None
    topic: Optional[str] = None
    stage_id: Optional[str] = None
    trigger_source: str = "learning_task"
    trigger_context: dict = Field(default_factory=dict)
    parent_resource_id: Optional[str] = None
    difficulty: Optional[str] = None
    variant_type: Optional[str] = None
    generation_version: str = "1"
    force_regenerate: bool = False


class ResourceStateUpdateRequest(BaseModel):
    is_favorite: Optional[bool] = None
    learning_status: Optional[str] = None


def _require_owned_course(
    db: Session,
    user: User,
    *,
    course_id: Optional[str],
    requested_student_id: Optional[str] = None,
) -> Course:
    query = db.query(Course).filter(Course.user_id == user.id)
    if course_id:
        query = query.filter(Course.id == course_id)
    elif user.active_course_id:
        query = query.filter(Course.id == user.active_course_id)
    elif requested_student_id:
        query = query.filter(Course.student_id == requested_student_id)
    course = query.order_by(Course.updated_at.desc()).first()
    if not course:
        raise ApiError(
            "COURSE_SCOPE_MISMATCH",
            "课程不存在或不属于当前登录用户",
            status_code=404,
        )
    if requested_student_id and requested_student_id != course.student_id:
        raise ApiError(
            "COURSE_SCOPE_MISMATCH",
            "student_id 与当前课程不匹配",
            status_code=403,
        )
    return course


@router.post(
    "/generate",
    responses=json_responses(
        "RESOURCE_GENERATE_FAILED",
        "PATH_NOT_FOUND",
        success_example=TASK_SUCCESS_EXAMPLE,
    ),
)
async def generate_resource(
    request: ResourceGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """生成学习资源，返回 task_id；前端轮询 /api/task/{task_id}/status。"""
    course = _require_owned_course(
        db,
        user,
        course_id=request.course_id,
        requested_student_id=request.student_id,
    )
    student_id = course.student_id
    requested_types = set(request.types or [])
    if request.resource_type:
        requested_types.add(request.resource_type)
    if "interactive_classroom" in requested_types:
        if not request.course_id:
            raise ApiError("COURSE_SCOPE_MISMATCH", "生成互动课堂需要 course_id", status_code=400)
        task = task_service.create("互动课堂生成任务已创建", owner_user_id=user.id)

        async def run_classroom_task():
            db = SessionLocal()
            try:
                def update(progress: int, phase: str, message: str):
                    task_service.update(task["task_id"], status="running", progress=progress, phase=phase, message=message)

                update(10, "analyzing_goals", "读取阶段学习目标")
                update(28, "retrieving_knowledge", "检索当前课程知识库")
                update(46, "planning_scenes", "规划课堂场景")
                update(68, "generating_content", "生成 PPT、白板、模拟和测验")
                result = await classroom_service.generate_for_stage(
                    db,
                    user=user,
                    course_id=request.course_id,
                    stage_id=str(request.stage_id or "stage_gradient_descent"),
                    task_id=request.task_id or "task_gradient_classroom",
                    topic=request.topic,
                )
                update(88, "validating", "校验课堂内容和课程范围")
                task_service.update(task["task_id"], status="done", progress=100, phase="completed", message="互动课堂生成完成", result=result)
            except Exception as exc:
                task_service.update(
                    task["task_id"],
                    status="failed",
                    progress=100,
                    phase="failed",
                    message="互动课堂生成失败",
                    error={"code": "CLASSROOM_GENERATION_FAILED", "message": str(exc)},
                )
            finally:
                db.close()

        background_tasks.add_task(run_classroom_task)
        return ok(task, "互动课堂生成任务已创建")

    try:
        resource_service.validate_path_ownership(
            db,
            student_id,
            request.path_id,
        )
    except ValueError as exc:
        raise ApiError("PATH_NOT_FOUND", str(exc)) from exc

    task = task_service.create("资源生成任务已创建", owner_user_id=user.id)

    async def run_task():
        db = SessionLocal()
        try:
            def update_progress(progress: int, phase: str, message: str):
                task_service.update(
                    task["task_id"],
                    status="running",
                    progress=progress,
                    phase=phase,
                    message=message,
                )

            update_progress(5, "started", "资源生成任务已开始")
            generation_kwargs = dict(
                db=db,
                student_id=student_id,
                topic=request.topic,
                types=request.types,
                difficulty=request.difficulty,
                count=request.count,
                course_id=course.id,
                path_id=request.path_id,
                task_id=request.task_id,
                trigger_source="ai_workspace",
                trigger_context={"course_id": course.id},
                on_progress=update_progress,
            )
            if request.stage_id is not None:
                generation_kwargs["stage_id"] = request.stage_id
            result = await resource_service.generate_resources(**generation_kwargs)
            task_service.update(
                task["task_id"],
                status="done",
                progress=100,
                phase="completed",
                message="资源生成完成",
                result=result,
            )
        except Exception as exc:
            task_service.update(
                task["task_id"],
                status="failed",
                progress=100,
                phase="failed",
                message="资源生成失败",
                error={"code": "RESOURCE_GENERATE_FAILED", "message": str(exc)},
            )
        finally:
            db.close()

    background_tasks.add_task(run_task)
    return ok(task, "资源生成任务已创建")


@router.post("/generate/stream", responses=sse_responses("RESOURCE_GENERATE_FAILED"))
async def generate_resource_stream(
    request: ResourceGenerateRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """生成学习资源，SSE 流式返回。"""
    course = _require_owned_course(
        db,
        user,
        course_id=request.course_id,
        requested_student_id=request.student_id,
    )

    async def event_generator():
        stream_db = SessionLocal()
        try:
            async for event in resource_service.generate_stream(
                db=stream_db,
                student_id=course.student_id,
                topic=request.topic,
                types=request.types,
                difficulty=request.difficulty,
                count=request.count,
                path_id=request.path_id,
                stage_id=request.stage_id,
            ):
                yield event
        except Exception:
            yield sse_error("RESOURCE_GENERATE_FAILED", "资源生成失败，请稍后重试")
            yield sse_done()
        finally:
            stream_db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/courses/{course_id}/tasks/{task_id}", responses=json_responses("RESOURCE_NOT_FOUND"))
async def get_task_resource(
    course_id: str,
    task_id: str,
    resource_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return ok(resource_service.get_task_resource_context(
            db,
            user=user,
            course_id=course_id,
            task_id=task_id,
            resource_type=resource_type,
            difficulty=difficulty,
        ))
    except ValueError as exc:
        raise ApiError("TASK_SCOPE_MISMATCH", str(exc), status_code=404) from exc


@router.post("/courses/{course_id}/tasks/{task_id}", responses=json_responses("RESOURCE_GENERATE_FAILED"))
async def generate_task_resource(
    course_id: str,
    task_id: str,
    request: ContextualResourceRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        result = await resource_service.generate_contextual_resource(
            db,
            user=user,
            course_id=course_id,
            resource_type=request.resource_type,
            topic=request.topic,
            trigger_source=request.trigger_source,
            trigger_context=request.trigger_context,
            task_id=task_id,
            stage_id=request.stage_id,
            parent_resource_id=request.parent_resource_id,
            generation_options={
                "difficulty": request.difficulty,
                "variant_type": request.variant_type,
                "generation_version": request.generation_version,
                "force_regenerate": request.force_regenerate,
            },
        )
        return ok(result, result.get("message") or ("已复用任务资源" if result["reused"] else "学习内容已准备"))
    except ValueError as exc:
        raise ApiError("TASK_SCOPE_MISMATCH", str(exc), status_code=404) from exc


def _list_resources_payload(
    db: Session,
    owner_user_id: str,
    page: int,
    page_size: int,
    keyword: Optional[str],
    type: Optional[str],
    course_id: Optional[str],
    stage_id: Optional[str],
    task_id: Optional[str],
    difficulty: Optional[str],
    generation_source: Optional[str],
    trigger_source: Optional[str],
    learning_status: Optional[str],
    favorite: Optional[bool],
    created_from: Optional[datetime],
    created_to: Optional[datetime],
    sort: str,
):
    return ok(
        resource_service.list_resources(
            db=db,
            page=page,
            page_size=page_size,
            keyword=keyword,
            resource_type=type,
            course_id=course_id,
            stage_id=stage_id,
            task_id=task_id,
            difficulty=difficulty,
            generation_source=generation_source,
            trigger_source=trigger_source,
            learning_status=learning_status,
            favorite=favorite,
            created_from=created_from,
            created_to=created_to,
            sort=sort,
            owner_user_id=owner_user_id,
        )
    )


@router.get("", responses=json_responses())
@router.get("/", responses=json_responses())
@router.get("/list", responses=json_responses())
async def list_resources(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    course_id: Optional[str] = None,
    stage_id: Optional[str] = None,
    task_id: Optional[str] = None,
    difficulty: Optional[str] = None,
    generation_source: Optional[str] = None,
    trigger_source: Optional[str] = None,
    learning_status: Optional[str] = None,
    favorite: Optional[bool] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    sort: str = "recent",
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """获取学生资源列表"""
    return _list_resources_payload(
        db,
        user.id,
        page,
        page_size,
        keyword,
        type,
        course_id,
        stage_id,
        task_id,
        difficulty,
        generation_source,
        trigger_source,
        learning_status,
        favorite,
        created_from,
        created_to,
        sort,
    )


@router.get("/types", responses=json_responses())
async def get_resource_types():
    """获取支持的资源类型"""
    return ok({
        "items": [
            {"value": "document", "label": "文档"},
            {"value": "exercise", "label": "练习题"},
            {"value": "code", "label": "代码案例"},
            {"value": "mindmap", "label": "思维导图"},
            {"value": "reading", "label": "拓展阅读"},
            {"value": "interactive_classroom", "label": "AI 互动课堂"},
        ]
    })


@router.post("/{resource_id}/bookmark", responses=json_responses("RESOURCE_NOT_FOUND"))
async def bookmark_resource(
    resource_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """收藏资源（前端兼容）"""
    state = resource_service.update_resource_state(
        db,
        user=user,
        resource_id=resource_id,
        toggle_favorite=True,
    )
    if not state:
        raise ApiError("RESOURCE_NOT_FOUND")
    return ok({
        "resource_id": resource_id,
        "bookmarked": state["is_favorite"],
        "user_state": state,
    })


@router.patch("/{resource_id}/state", responses=json_responses("RESOURCE_NOT_FOUND"))
async def update_resource_state(
    resource_id: str,
    request: ResourceStateUpdateRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """更新当前用户对资源的收藏和学习状态。"""
    try:
        state = resource_service.update_resource_state(
            db,
            user=user,
            resource_id=resource_id,
            is_favorite=request.is_favorite,
            learning_status=request.learning_status,
        )
    except ValueError as exc:
        raise ApiError("INVALID_RESOURCE_STATE", str(exc), status_code=422) from exc
    if not state:
        raise ApiError("RESOURCE_NOT_FOUND")
    return ok({"resource_id": resource_id, "user_state": state})


@router.get("/{resource_id}", responses=json_responses("RESOURCE_NOT_FOUND"))
async def get_resource(
    resource_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """获取资源详情"""
    resource = resource_service.get_resource_detail(
        db,
        user=user,
        resource_id=resource_id,
    )
    if not resource:
        raise ApiError("RESOURCE_NOT_FOUND")
    return ok(resource)
