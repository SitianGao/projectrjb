"""登录后会话启动聚合 API。"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.auth_api import require_user
from api.response import ok
from database import get_db
from deps import profile_service
from models.auth import Course
from models.learning_path import LearningPath
from services.auth_service import auth_service


router = APIRouter()


def _safe_json(value, default):
    if not value:
        return default
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
        return parsed if parsed is not None else default
    except (TypeError, json.JSONDecodeError):
        return default


def _first_current_task(path: LearningPath | None):
    if not path:
        return None
    stages = _safe_json(path.stages, [])
    if not stages:
        return None
    current_stage_key = str(path.current_stage or 1)
    current_stage = next(
        (stage for stage in stages if str(stage.get("stage_id", 1)) == current_stage_key),
        stages[0],
    )
    tasks = current_stage.get("tasks") or []
    seen = set()
    for task in tasks:
        task_id = task.get("task_id") or task.get("id")
        if not task_id or task_id in seen:
            continue
        seen.add(task_id)
        if task.get("status") in ("completed", "locked"):
            continue
        return {
            "task_id": task_id,
            "stage_id": current_stage.get("stage_id"),
            "title": task.get("title") or task.get("description") or "当前学习任务",
        }
    return None


def _resolve_continue_target(course: Course | None, path: LearningPath | None):
    if not course:
        return {"route": "/courses", "reason": "NO_COURSE"}
    if not path:
        return {
            "route": f"/course/{course.id}/profile/setup",
            "reason": "COURSE_PROFILE_OR_PATH_REQUIRED",
        }
    task = _first_current_task(path)
    if task:
        return {
            "route": f"/course/{course.id}/learn/{task['task_id']}",
            "reason": "CURRENT_TASK",
            "task": task,
        }
    return {"route": f"/course/{course.id}/path", "reason": "PATH_READY"}


@router.get("/bootstrap")
async def bootstrap(user=Depends(require_user), db: Session = Depends(get_db)):
    """返回登录落点所需的最小聚合状态。"""
    serialized_user = auth_service.serialize_user(db, user)
    active = serialized_user.get("active_course")
    course = None
    path = None
    profile = None

    if active:
        course = db.query(Course).filter(Course.id == active["id"], Course.user_id == user.id).first()
        profile = profile_service.get_profile(db, course.student_id) if course else None
        path = (
            db.query(LearningPath)
            .filter(LearningPath.student_id == course.student_id, LearningPath.status == "active")
            .order_by(LearningPath.version.desc())
            .first()
            if course
            else None
        )

    profile_completion = float(profile.get("completeness") or 0) if profile else 0.0
    from config import PROFILE_READY_THRESHOLD
    profile_ready = profile_completion >= PROFILE_READY_THRESHOLD
    has_path = bool(path)
    continue_target = _resolve_continue_target(course, path)

    return ok({
        "user": serialized_user,
        "global_profile": {
            "status": "account_profile",
            "scope": "user",
            "ready": True,
        },
        "course_profile": {
            "scope": "course",
            "course_id": course.id if course else None,
            "student_id": course.student_id if course else None,
            "completion": profile_completion,
            "ready": profile_ready,
            "requires_setup": bool(course and (not profile or not profile_ready)),
            "requires_update": bool(course and profile and not profile_ready),
        },
        "learning_path": {
            "exists": has_path,
            "path_id": path.id if path else None,
            "current_stage": path.current_stage if path else None,
        },
        "continue_target": continue_target,
    })
