"""课程范围内的学习执行查询与任务进度服务。"""

from __future__ import annotations

import datetime
import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from api.response import ApiError
from models.auth import Course, User
from models.learning_path import LearningPath, LearningStage, LearningTask


TASK_TYPE_LABELS = {
    "objective": "学习目标",
    "goal": "学习目标",
    "document": "核心讲义",
    "lecture": "核心讲义",
    "mindmap": "概念图解",
    "diagram": "概念图解",
    "exercise": "知识检查",
    "quiz": "知识检查",
    "assessment": "阶段测评",
    "exam": "阶段测评",
    "code": "代码实操",
    "ppt": "教学课件",
    "interactive_classroom": "AI 互动课堂",
}


class CourseLearningService:
    def __init__(self, planner_service):
        self.planner_service = planner_service

    def get_learning_context(
        self,
        db: Session,
        *,
        user: User,
        course_id: str,
        task_id: Optional[str] = None,
    ) -> dict:
        course = self._require_course(db, user, course_id)
        path = self._require_path(db, user, course)
        stages = (
            db.query(LearningStage)
            .filter(LearningStage.path_id == path.id)
            .order_by(LearningStage.order.asc())
            .all()
        )
        tasks = (
            db.query(LearningTask)
            .filter(LearningTask.path_id == path.id)
            .order_by(LearningTask.stage_id.asc(), LearningTask.order.asc())
            .all()
        )
        if not stages or not tasks:
            raise ApiError("PATH_NOT_FOUND", "学习路径缺少可执行的阶段或任务", status_code=404)

        stage_by_id = {stage.stage_id: stage for stage in stages}
        effective_status = self._effective_statuses(path, stages, tasks)
        selected_task = None
        if task_id:
            selected_task = next((task for task in tasks if task.task_id == task_id), None)
            if not selected_task:
                raise ApiError("TASK_NOT_FOUND", "任务不存在或不属于当前课程", status_code=404)
        if not selected_task:
            selected_task = self._continue_task(tasks, effective_status)
        if not selected_task:
            selected_task = tasks[-1]

        selected_stage = stage_by_id[selected_task.stage_id]
        stage_tasks = [task for task in tasks if task.stage_id == selected_stage.stage_id]
        stage_progress = self._progress(stage_tasks, effective_status)
        path_progress = self._progress(tasks, effective_status)
        serialized_tasks = [
            self._task_dict(task, effective_status[task.task_id], selected_stage)
            for task in stage_tasks
        ]
        current_task = self._task_dict(
            selected_task,
            effective_status[selected_task.task_id],
            selected_stage,
        )
        continue_task = self._continue_task(tasks, effective_status)

        return {
            "course": {
                "id": course.id,
                "course_id": course.id,
                "name": course.title,
                "title": course.title,
                "goal": course.goal or path.goal or "",
            },
            "path": self._path_dict(path, stages, tasks, effective_status),
            "stage": self._stage_dict(selected_stage),
            "current_task": current_task,
            "tasks": serialized_tasks,
            "progress": stage_progress,
            "path_progress": path_progress,
            "continue_target": {
                "task_id": continue_task.task_id if continue_task else None,
                "route": (
                    f"/course/{course.id}/learn/{continue_task.task_id}"
                    if continue_task
                    else f"/course/{course.id}/path"
                ),
            },
            "generation": self._generation_dict(path),
            "tutor_context": {
                "user_id": user.id,
                "course_id": course.id,
                "stage_id": selected_stage.stage_id,
                "task_id": selected_task.task_id,
                "knowledge_point_ids": _loads(selected_stage.knowledge_point_ids, []),
                "current_knowledge_point": selected_task.title,
            },
        }

    def complete_task(
        self,
        db: Session,
        *,
        user: User,
        course_id: str,
        task_id: str,
    ) -> dict:
        course = self._require_course(db, user, course_id)
        path = self._require_path(db, user, course)
        task = (
            db.query(LearningTask)
            .filter(
                LearningTask.path_id == path.id,
                LearningTask.task_id == task_id,
            )
            .first()
        )
        if not task:
            raise ApiError("TASK_NOT_FOUND", "任务不存在或不属于当前课程", status_code=404)

        all_tasks = (
            db.query(LearningTask)
            .filter(LearningTask.path_id == path.id)
            .order_by(LearningTask.stage_id.asc(), LearningTask.order.asc())
            .all()
        )
        completed_ids = {
            item.task_id for item in all_tasks if item.status == "completed"
        }
        prerequisites = set(_loads(task.prerequisite_task_ids, []))
        if not prerequisites.issubset(completed_ids):
            raise ApiError("TASK_LOCKED", "请先完成前置任务", status_code=409)

        was_completed = task.status == "completed"
        if not was_completed:
            task.status = "completed"
            task.completed_at = datetime.datetime.utcnow()

        self._advance_path(db, path, all_tasks)
        self._sync_snapshot(path, db)
        db.commit()

        context = self.get_learning_context(
            db,
            user=user,
            course_id=course_id,
        )
        next_task = context.get("current_task")
        return {
            "completed_task_id": task.task_id,
            "idempotent": was_completed,
            "progress": context["progress"],
            "path_progress": context["path_progress"],
            "next_task": next_task
            if next_task and next_task.get("task_id") != task.task_id
            else None,
            "continue_target": context["continue_target"]["route"],
        }

    def _require_course(self, db: Session, user: User, course_id: str) -> Course:
        course = (
            db.query(Course)
            .filter(Course.id == course_id, Course.user_id == user.id)
            .first()
        )
        if not course:
            raise ApiError(
                "COURSE_NOT_FOUND",
                "课程不存在或不属于当前登录用户",
                status_code=404,
            )
        return course

    def _require_path(self, db: Session, user: User, course: Course) -> LearningPath:
        path = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == course.student_id,
                LearningPath.user_id == user.id,
                LearningPath.course_id == course.id,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.version.desc())
            .first()
        )
        if not path:
            raise ApiError("PATH_NOT_FOUND", "当前课程还没有学习路径", status_code=404)
        self.planner_service.ensure_normalized_entities(db, path)
        return path

    @staticmethod
    def _effective_statuses(
        path: LearningPath,
        stages: list[LearningStage],
        tasks: list[LearningTask],
    ) -> dict[str, str]:
        completed = {task.task_id for task in tasks if task.status == "completed"}
        current_order = max(1, int(path.current_stage or 1))
        result: dict[str, str] = {}
        active_assigned = False
        stage_order = {stage.stage_id: stage.order for stage in stages}
        for task in sorted(tasks, key=lambda item: (stage_order.get(item.stage_id, 999), item.order)):
            if task.task_id in completed:
                result[task.task_id] = "completed"
                continue
            prerequisites = set(_loads(task.prerequisite_task_ids, []))
            if stage_order.get(task.stage_id, 999) > current_order:
                result[task.task_id] = "locked"
            elif not prerequisites.issubset(completed):
                result[task.task_id] = "locked"
            elif not active_assigned:
                result[task.task_id] = "active"
                active_assigned = True
            else:
                result[task.task_id] = "not_started"
        return result

    @staticmethod
    def _continue_task(
        tasks: list[LearningTask],
        statuses: dict[str, str],
    ) -> Optional[LearningTask]:
        return next(
            (
                task
                for task in tasks
                if statuses.get(task.task_id) in {"active", "not_started"}
            ),
            None,
        )

    @staticmethod
    def _progress(tasks: list[LearningTask], statuses: dict[str, str]) -> dict:
        unique = {task.task_id: task for task in tasks}
        total = len(unique)
        completed = sum(
            1 for task_id in unique if statuses.get(task_id) == "completed"
        )
        completed = min(completed, total)
        return {
            "completed": completed,
            "total": total,
            "percent": round(completed / total * 100) if total else 0,
        }

    @staticmethod
    def _stage_dict(stage: LearningStage) -> dict:
        return {
            "stage_id": stage.stage_id,
            "title": stage.title,
            "description": stage.description or "",
            "order": stage.order,
            "status": stage.status,
            "learning_objectives": _loads(stage.learning_objectives, []),
            "objectives": _loads(stage.learning_objectives, []),
            "knowledge_point_ids": _loads(stage.knowledge_point_ids, []),
            "topics": _loads(stage.topics, []),
            "estimated_days": max(1, int(stage.estimated_days or 1)),
        }

    @staticmethod
    def _task_dict(
        task: LearningTask,
        status: str,
        stage: LearningStage,
    ) -> dict:
        content = task.content or _default_task_content(task, stage)
        return {
            "id": task.task_id,
            "task_id": task.task_id,
            "type": task.task_type,
            "task_type": task.task_type,
            "type_label": TASK_TYPE_LABELS.get(task.task_type, "学习任务"),
            "title": task.title,
            "description": task.description or "",
            "objective": task.description or task.title,
            "content": content,
            "order": task.order,
            "estimated_minutes": max(5, min(480, int(task.estimated_minutes or 20))),
            "estimatedMinutes": max(5, min(480, int(task.estimated_minutes or 20))),
            "difficulty": task.difficulty or "初级",
            "status": status,
            "prerequisite_task_ids": _loads(task.prerequisite_task_ids, []),
            "resource_id": task.resource_id,
        }

    def _path_dict(
        self,
        path: LearningPath,
        stages: list[LearningStage],
        tasks: list[LearningTask],
        statuses: dict[str, str],
    ) -> dict:
        tasks_by_stage: dict[str, list[LearningTask]] = {}
        for task in tasks:
            tasks_by_stage.setdefault(task.stage_id, []).append(task)
        return {
            "id": path.id,
            "path_id": path.id,
            "version": path.version,
            "goal": path.goal or "",
            "current_stage": path.current_stage,
            "current_stage_id": path.current_stage_id,
            "estimated_days": path.estimated_days,
            "status": path.status,
            "generation_source": path.generation_source or "legacy",
            "generated_by": path.generated_by,
            "provider": path.provider,
            "model": path.model,
            "agent_run_id": path.agent_run_id,
            "profile_version": path.profile_version,
            "fallback_used": bool(path.fallback_used),
            "fallback_type": path.fallback_type,
            "generated_at": path.generated_at.isoformat() if path.generated_at else None,
            "created_at": path.created_at.isoformat() if path.created_at else None,
            "updated_at": path.updated_at.isoformat() if path.updated_at else None,
            "stages": [
                {
                    **self._stage_dict(stage),
                    "tasks": [
                        self._task_dict(task, statuses[task.task_id], stage)
                        for task in tasks_by_stage.get(stage.stage_id, [])
                    ],
                }
                for stage in stages
            ],
        }

    @staticmethod
    def _generation_dict(path: LearningPath) -> dict:
        return {
            "generation_source": path.generation_source or "legacy",
            "generated_by": path.generated_by,
            "provider": path.provider,
            "model": path.model,
            "agent_run_id": path.agent_run_id,
            "profile_version": path.profile_version,
            "path_version": path.version,
            "fallback_used": bool(path.fallback_used),
            "fallback_type": path.fallback_type,
            "generated_at": path.generated_at.isoformat() if path.generated_at else None,
        }

    @staticmethod
    def _advance_path(
        db: Session,
        path: LearningPath,
        tasks: list[LearningTask],
    ) -> None:
        stages = (
            db.query(LearningStage)
            .filter(LearningStage.path_id == path.id)
            .order_by(LearningStage.order.asc())
            .all()
        )
        for stage in stages:
            stage_tasks = [task for task in tasks if task.stage_id == stage.stage_id]
            if stage_tasks and all(task.status == "completed" for task in stage_tasks):
                stage.status = "completed"

        current = next(
            (stage for stage in stages if stage.order == int(path.current_stage or 1)),
            stages[0],
        )
        if current.status == "completed":
            next_stage = next((stage for stage in stages if stage.order > current.order), None)
            if next_stage:
                next_stage.status = "active"
                path.current_stage = next_stage.order
                path.current_stage_id = next_stage.stage_id

        completed = {task.task_id for task in tasks if task.status == "completed"}
        active_set = False
        stage_order = {stage.stage_id: stage.order for stage in stages}
        for task in sorted(
            tasks,
            key=lambda item: (stage_order.get(item.stage_id, 999), item.order),
        ):
            if task.status == "completed":
                continue
            prerequisites = set(_loads(task.prerequisite_task_ids, []))
            stage = next(stage for stage in stages if stage.stage_id == task.stage_id)
            if (
                stage.order == int(path.current_stage or 1)
                and prerequisites.issubset(completed)
                and not active_set
            ):
                task.status = "active"
                active_set = True
            elif task.status == "active":
                task.status = "not_started"

    @staticmethod
    def _sync_snapshot(path: LearningPath, db: Session) -> None:
        stages = _loads(path.stages, [])
        task_rows = {
            task.task_id: task
            for task in db.query(LearningTask).filter(LearningTask.path_id == path.id).all()
        }
        stage_rows = {
            stage.stage_id: stage
            for stage in db.query(LearningStage).filter(LearningStage.path_id == path.id).all()
        }
        for stage in stages:
            stage_id = str(stage.get("stage_id"))
            if stage_id in stage_rows:
                stage["status"] = stage_rows[stage_id].status
            for task in stage.get("tasks") or []:
                row = task_rows.get(str(task.get("task_id") or task.get("id")))
                if row:
                    task["status"] = row.status
        path.stages = json.dumps(stages, ensure_ascii=False)


def _loads(value: Any, default):
    if value is None or value == "":
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _default_task_content(task: LearningTask, stage: LearningStage) -> str:
    objectives = _loads(stage.learning_objectives, [])
    topics = _loads(stage.topics, [])
    sections = [f"### {task.title}"]
    if task.description:
        sections.append(task.description)
    if task.task_type in {"objective", "goal"} and objectives:
        sections.append("### 本阶段目标\n" + "\n".join(f"- {item}" for item in objectives))
    if topics:
        sections.append("### 关键知识点\n" + "\n".join(f"- {item}" for item in topics))
    return "\n\n".join(sections)
