"""课程学习路径、执行上下文、真实 Agent 流程与任务进度 API。"""

import json
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth_api import require_user
from api.response import ok, sse_done, sse_error
from core.agent_context import AgentContext
from database import SessionLocal, get_db
from deps import (
    course_learning_service,
    planner_agent,
    planner_service,
    profile_agent,
    profile_service,
    resource_agent,
)
from models.auth import Course
from services.planner_service import _normalize_path_result


router = APIRouter()


class InitializeCourseRequest(BaseModel):
    goal: str = ""
    message: str = ""


def _event(event_type: str, **payload) -> str:
    return f"data: {json.dumps({'type': event_type, **payload}, ensure_ascii=False)}\n\n"


@router.post("/{course_id}/initialize/stream")
async def initialize_course_learning(
    course_id: str,
    request: InitializeCourseRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.user_id == user.id)
        .first()
    )
    if not course:
        from api.response import ApiError

        raise ApiError("COURSE_NOT_FOUND", "课程不存在或不属于当前登录用户", status_code=404)

    user_id = user.id

    async def event_generator():
        stream_db = SessionLocal()
        profile_run = None
        planner_run = None
        try:
            scoped_course = (
                stream_db.query(Course)
                .filter(Course.id == course_id, Course.user_id == user_id)
                .first()
            )
            if not scoped_course:
                raise ValueError("课程上下文已失效")
            current_profile = profile_service.get_profile(stream_db, scoped_course.student_id)
            if not current_profile:
                raise ValueError("请先完成课程学习画像")

            context = AgentContext(
                user_id=user_id,
                course_id=course_id,
                session_id=f"workflow-{uuid.uuid4().hex[:12]}",
            )
            yield _event("workflow_started", step="profile", message="多智能体课程初始化开始")

            profile_run = planner_service._start_agent_run(stream_db, context, "ProfileAgent")
            yield _event(
                "agent_started",
                step="profile",
                agent="ProfileAgent",
                run_id=profile_run.id,
                message="ProfileAgent 正在确认课程画像",
            )
            profile_output = await profile_agent.build_profile_v2(
                context=context,
                message=request.message or request.goal or current_profile.get("learning_goal") or scoped_course.goal,
                history=[],
                current_profile=current_profile,
            )
            structured_profile = profile_output.model_dump()
            course_profile = structured_profile["profile"]
            legacy_profile = {
                "learning_goal": course_profile.get("learning_goal")
                or request.goal
                or current_profile.get("learning_goal"),
                "knowledge_level": json.dumps(
                    course_profile.get("knowledge_foundation") or {},
                    ensure_ascii=False,
                ),
                "cognitive_style": course_profile.get("cognitive_style")
                or current_profile.get("cognitive_style"),
                "weakness": [
                    item.get("name") or item.get("knowledge_point_id")
                    for item in course_profile.get("weak_points") or []
                ],
                "interest": course_profile.get("interest_directions") or [],
                "completeness": structured_profile.get("completeness", 0),
            }
            profile_service.save_profile(
                stream_db,
                scoped_course.student_id,
                legacy_profile,
                increment_version=True,
            )
            saved_profile = profile_service.get_profile(stream_db, scoped_course.student_id)
            usage = profile_agent.llm.last_usage if profile_agent.llm else None
            profile_metadata = {
                "provider": getattr(usage, "provider", None),
                "model": getattr(usage, "model", None),
                "fallback_used": False,
                "fallback_type": None,
            }
            planner_service._complete_agent_run(
                stream_db,
                profile_run,
                status="completed",
                metadata=profile_metadata,
            )
            yield _event(
                "agent_completed",
                step="profile",
                agent="ProfileAgent",
                run_id=profile_run.id,
                provider=profile_metadata["provider"],
                model=profile_metadata["model"],
                duration_ms=profile_run.duration_ms,
                fallback_used=False,
                message="ProfileAgent 已确认并保存课程画像",
            )

            planner_run = planner_service._start_agent_run(stream_db, context, "PlannerAgent")
            yield _event(
                "agent_started",
                step="planner",
                agent="PlannerAgent",
                run_id=planner_run.id,
                message="PlannerAgent 正在生成个性化阶段与任务",
            )
            path_output = await planner_agent.generate_plan_v2(
                context=context,
                profile={
                    **saved_profile,
                    **course_profile,
                    "learning_goal": request.goal
                    or course_profile.get("learning_goal")
                    or saved_profile.get("learning_goal"),
                },
                course_outline=[],
            )
            resolved_goal = (
                request.goal
                or course_profile.get("learning_goal")
                or saved_profile.get("learning_goal")
                or scoped_course.goal
            )
            path_data = _normalize_path_result(path_output, resolved_goal)
            knowledge_rows = planner_service._retrieve_course_knowledge(
                resolved_goal,
                saved_profile,
            )
            planner_service._attach_stage_knowledge_sources(path_data, knowledge_rows)
            generation_metadata = planner_service._generation_metadata(
                saved_profile,
                planner_run.id,
            )
            planner_service._complete_agent_run(
                stream_db,
                planner_run,
                status="completed",
                metadata=generation_metadata,
                knowledge_hit_count=sum(
                    len(stage.get("knowledge_sources") or [])
                    for stage in path_data.get("stages", [])
                ),
            )
            yield _event(
                "agent_completed",
                step="planner",
                agent="PlannerAgent",
                run_id=planner_run.id,
                provider=generation_metadata.get("provider"),
                model=generation_metadata.get("model"),
                duration_ms=planner_run.duration_ms,
                fallback_used=generation_metadata.get("fallback_used", False),
                message="PlannerAgent 输出已通过结构校验",
            )
            saved_path = planner_service.save_path(
                stream_db,
                scoped_course.student_id,
                path_data,
                user_id=user_id,
                course_id=course_id,
                generation_metadata=generation_metadata,
            )
            path_payload = planner_service._path_to_dict(saved_path)
            yield _event(
                "path_saved",
                step="planner",
                path_id=saved_path.id,
                version=saved_path.version,
                generation_source=saved_path.generation_source,
                message="学习路径、阶段和任务已保存",
            )

            current_stage = next(
                (
                    stage
                    for stage in path_payload["stages"]
                    if str(stage.get("stage_id")) == str(saved_path.current_stage_id)
                ),
                path_payload["stages"][0],
            )
            resource_context = context.model_copy(
                update={"stage_id": str(current_stage.get("stage_id"))}
            )
            yield _event(
                "agent_started",
                step="resource",
                agent="ResourceAgent",
                message="ResourceAgent 正在准备当前阶段资源任务",
            )
            resource_jobs = await resource_agent.prepare_stage_resources(
                context=resource_context,
                stage=current_stage,
                resource_blueprint=current_stage.get("resource_blueprint"),
            )
            for job in resource_jobs:
                yield _event(
                    "resource_job_created",
                    step="resource",
                    agent="ResourceAgent",
                    job=job,
                    message=f"已创建 {job['resource_type']} 资源任务",
                )
            yield _event(
                "agent_completed",
                step="resource",
                agent="ResourceAgent",
                resource_job_count=len(resource_jobs),
                message="ResourceAgent 已创建当前阶段资源任务",
            )
            yield _event("data", step="done", data=path_payload)
            yield _event("workflow_completed", step="done", message="多智能体课程初始化完成")
            yield sse_done()
        except Exception as exc:
            stream_db.rollback()
            failed_run = planner_run or profile_run
            if failed_run:
                planner_service._complete_agent_run(
                    stream_db,
                    failed_run,
                    status="failed",
                    metadata={"fallback_used": False},
                    error_code=exc.__class__.__name__,
                    fallback_reason=str(exc),
                )
            yield _event(
                "agent_failed",
                step="planner" if planner_run else "profile",
                run_id=failed_run.id if failed_run else None,
                message=str(exc),
            )
            yield sse_error("COURSE_INITIALIZE_FAILED", str(exc) or "课程初始化失败")
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


@router.get("/{course_id}/learning-path")
async def get_course_learning_path(
    course_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    context = course_learning_service.get_learning_context(
        db,
        user=user,
        course_id=course_id,
    )
    return ok({
        "course": context["course"],
        "path": context["path"],
        "progress": context["path_progress"],
        "continue_target": context["continue_target"],
        "generation": context["generation"],
    })


@router.get("/{course_id}/learn/{task_id}")
async def get_course_learning_context(
    course_id: str,
    task_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    return ok(course_learning_service.get_learning_context(
        db,
        user=user,
        course_id=course_id,
        task_id=task_id,
    ))


@router.get("/{course_id}/learn")
async def get_course_continue_context(
    course_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    return ok(course_learning_service.get_learning_context(
        db,
        user=user,
        course_id=course_id,
    ))


@router.post("/{course_id}/tasks/{task_id}/complete")
async def complete_course_task(
    course_id: str,
    task_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    return ok(
        course_learning_service.complete_task(
            db,
            user=user,
            course_id=course_id,
            task_id=task_id,
        ),
        "学习进度已保存",
    )


@router.get("/{course_id}/learning-path/generation")
async def get_path_generation_source(
    course_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    context = course_learning_service.get_learning_context(
        db,
        user=user,
        course_id=course_id,
    )
    return ok(context["generation"])
