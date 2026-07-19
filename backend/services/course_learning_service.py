"""课程范围内的学习执行查询与任务进度服务。"""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from api.response import ApiError
from models.auth import Course, User
from models.classroom import ClassroomQuizAttempt, ClassroomSession
from models.evaluation import EvaluationReport, LearningRecord
from models.learning_path import LearningPath, LearningStage, LearningTask
from models.resource import Resource
from models.student import StudentProfile
from models.study_session import StudySession


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

    def resolve_active_learning_state(
        self,
        db: Session,
        *,
        user: User,
        course_id: str,
    ) -> dict:
        """Return the single course-scoped learning state used by all pages."""
        course = self._require_course(db, user, course_id)
        path = self._resolve_effective_path(db, user, course, allow_missing=True)
        if not path:
            # 区分：画像不完整 vs 画像完整但路径缺失
            profile_ready = self._is_profile_ready_for_path(db, course)
            if profile_ready:
                # 画像已就绪，缺少路径 → 引导生成路径而非重做画像
                return self._empty_learning_state(course, user, "path_missing")
            else:
                return self._empty_learning_state(course, user, "profile_incomplete")

        self.planner_service.ensure_normalized_entities(db, path)
        stages, tasks = self._load_ordered_path_entities(db, path)
        statuses = self._effective_statuses(path, stages, tasks)
        path_progress = self._progress(tasks, statuses)
        completed = path_progress["total"] > 0 and path_progress["completed"] >= path_progress["total"]
        if completed:
            course_status = "completed"
        elif path_progress["total"] == 0:
            course_status = "path_missing"
        elif path_progress["completed"] == 0:
            course_status = "not_started"
        else:
            course_status = "learning"

        current_task = None if completed else self._continue_task(tasks, statuses)
        next_task = None
        if current_task:
            current_index = tasks.index(current_task)
            next_task = next(
                (
                    task for task in tasks[current_index + 1:]
                    if statuses.get(task.task_id) in {"active", "not_started"}
                ),
                None,
            )
        current_stage = self._resolve_current_stage(path, stages, current_task)
        stage_by_id = {stage.stage_id: stage for stage in stages}
        current_stage_for_task = stage_by_id.get(current_task.stage_id) if current_task else current_stage

        if course_status == "completed":
            continue_target = {
                "type": "course_summary",
                "route": f"/course/{course.id}/path",
                "task_id": None,
            }
        elif course_status in {"learning", "not_started"} and current_task:
            continue_target = {
                "type": "task",
                "route": f"/course/{course.id}/learn/{current_task.task_id}",
                "task_id": current_task.task_id,
            }
        elif course_status == "path_missing":
            continue_target = {
                "type": "profile_setup",
                "route": f"/course/{course.id}/profile/setup",
                "task_id": None,
            }
        else:
            continue_target = {
                "type": "learning_path",
                "route": f"/course/{course.id}/path",
                "task_id": None,
            }

        updated_candidates = [
            course.updated_at,
            path.updated_at,
            *(stage.updated_at for stage in stages),
            *(task.updated_at for task in tasks),
        ]
        updated_at = max(
            (value for value in updated_candidates if value),
            default=datetime.datetime.utcnow(),
        )

        serialized_stages = self._serialized_stages(stages, tasks, statuses)
        return {
            "user": {
                "user_id": user.id,
                "display_name": user.name or user.username,
            },
            "course": {
                "course_id": course.id,
                "course_name": course.title,
                "id": course.id,
                "name": course.title,
                "title": course.title,
                "status": course_status,
            },
            "learning_goal": course.goal or path.goal or "",
            "course_status": course_status,
            "path": {
                "path_id": path.id,
                "id": path.id,
                "version": path.version,
                "status": "completed" if completed else path.status,
                "goal": path.goal or "",
                "active_path_id": path.id,
                "current_stage": path.current_stage,
                "current_stage_id": path.current_stage_id,
                "stages": serialized_stages,
            },
            "progress": {
                "completed_tasks": path_progress["completed"],
                "total_tasks": path_progress["total"],
                "percent": path_progress["percent"],
                "completed": path_progress["completed"],
                "total": path_progress["total"],
            },
            "course_status": course_status,
            "current_stage": (
                self._stage_dict(current_stage) if current_stage else None
            ),
            "current_task": (
                self._task_dict(current_task, statuses[current_task.task_id], current_stage_for_task)
                if current_task and current_stage_for_task
                else None
            ),
            "next_task": (
                {"task_id": next_task.task_id, "title": next_task.title}
                if next_task
                else None
            ),
            "continue_target": continue_target,
            "profile_conversation": {
                "conversation_id": f"profile-{course.id}-draft",
                "route": f"/course/{course.id}/profile/setup",
            },
            "updated_at": updated_at.isoformat(),
        }

    def get_home_dashboard(
        self,
        db: Session,
        *,
        user: User,
        course_id: str,
    ) -> dict:
        """聚合当前用户、课程和有效路径的首页实时数据。"""
        state = self.resolve_active_learning_state(db, user=user, course_id=course_id)
        course = self._require_course(db, user, course_id)
        path = None
        if state.get("path"):
            path = db.query(LearningPath).filter(LearningPath.id == state["path"]["path_id"]).first()

        stages: list[LearningStage] = []
        tasks: list[LearningTask] = []
        statuses: dict[str, str] = {}
        current_stage = None
        current_task = None
        next_task = None
        path_progress = {"completed": 0, "total": 0, "percent": 0}

        if path:
            stages, tasks = self._load_ordered_path_entities(db, path)
            statuses = self._effective_statuses(path, stages, tasks)
            path_progress = self._progress(tasks, statuses)
            current_stage = next(
                (stage for stage in stages if stage.stage_id == path.current_stage_id),
                None,
            ) or next(
                (stage for stage in stages if stage.order == int(path.current_stage or 1)),
                stages[0] if stages else None,
            )
            current_task = self._continue_task(tasks, statuses)
            if current_task:
                current_index = tasks.index(current_task)
                next_task = next(
                    (
                        task for task in tasks[current_index + 1:]
                        if statuses.get(task.task_id) in {"active", "not_started"}
                    ),
                    None,
                )

        records = (
            db.query(LearningRecord)
            .join(Course, Course.student_id == LearningRecord.student_id)
            .filter(
                Course.id == course.id,
                Course.user_id == user.id,
                LearningRecord.student_id == course.student_id,
            )
            .all()
        )
        valid_time_actions = {
            "complete",
            "answer",
            "code_submit",
            "self_eval",
            "assessment",
            "classroom_complete",
        }
        confirmed_records = [
            record
            for record in records
            if record.action in valid_time_actions
        ]
        study_sessions = (
            db.query(StudySession)
            .filter(
                StudySession.user_id == user.id,
                StudySession.course_id == course.id,
                StudySession.path_id == path.id if path else False,
                StudySession.status == "completed",
            )
            .all()
            if path
            else []
        )
        study_seconds = sum(record.time_spent or 0 for record in confirmed_records)
        study_seconds += sum(session.duration_seconds or 0 for session in study_sessions)

        answer_records = [record for record in records if record.action == "answer"]
        classroom_attempts = (
            db.query(ClassroomQuizAttempt)
            .join(ClassroomSession, ClassroomSession.id == ClassroomQuizAttempt.session_id)
            .filter(
                ClassroomSession.user_id == user.id,
                ClassroomSession.course_id == course.id,
            )
            .all()
        )
        answered_questions = len(answer_records) + len(classroom_attempts)
        correct_answers = sum(
            1 for record in answer_records if _score_is_correct(record.score)
        ) + sum(1 for attempt in classroom_attempts if bool(attempt.is_correct))
        accuracy_rate = (
            round(correct_answers / answered_questions * 100)
            if answered_questions
            else None
        )

        activity_dates = {
            _local_activity_date(record.created_at)
            for record in confirmed_records
            if record.created_at
        }
        activity_dates.update(
            _local_activity_date(task.completed_at)
            for task in tasks
            if task.completed_at
        )
        activity_dates.update(
            _local_activity_date(session.ended_at)
            for session in study_sessions
            if session.ended_at and (session.duration_seconds or 0) > 0
        )
        streak_days = _current_streak(activity_dates)

        if not path:
            # 沿用 resolve_active_learning_state 的判断，区分画像不完整 vs 画像就绪
            course_status = state.get("course_status", "path_missing")
        elif path_progress["total"] == 0:
            course_status = "path_missing"
        elif path_progress["completed"] == 0:
            course_status = "not_started"
        elif path_progress["completed"] >= path_progress["total"]:
            course_status = "completed"
        else:
            course_status = "learning"

        serialized_stages = self._serialized_stages(stages, tasks, statuses) if path else []

        current_task_payload = (
            self._task_dict(current_task, statuses[current_task.task_id], current_stage)
            if current_task and current_stage
            else None
        )
        next_task_payload = (
            {
                "task_id": next_task.task_id,
                "title": next_task.title,
            }
            if next_task
            else None
        )
        continue_target = state["continue_target"]
        continue_route = continue_target.get("route")
        updated_candidates = [
            course.updated_at,
            path.updated_at if path else None,
            *(task.updated_at for task in tasks),
            *(record.created_at for record in records),
            *(session.updated_at for session in study_sessions),
        ]
        updated_at = max(
            (value for value in updated_candidates if value),
            default=datetime.datetime.utcnow(),
        )

        statistics = {
            "progress_percent": path_progress["percent"],
            "study_minutes": max(0, round(study_seconds / 60)),
            "accuracy_rate": accuracy_rate,
            "streak_days": streak_days,
            "completed_tasks": path_progress["completed"],
            "total_tasks": path_progress["total"],
            "answered_questions": answered_questions,
        }
        learning_context = {
            "learning_goal": state.get("learning_goal") or "",
            "current_stage_id": state.get("current_stage", {}).get("stage_id") if state.get("current_stage") else None,
            "current_stage_title": state.get("current_stage", {}).get("title") if state.get("current_stage") else None,
            "current_task_id": state.get("current_task", {}).get("task_id") if state.get("current_task") else None,
            "current_task_title": state.get("current_task", {}).get("title") if state.get("current_task") else None,
            "next_task_id": state.get("next_task", {}).get("task_id") if state.get("next_task") else None,
            "next_task_title": state.get("next_task", {}).get("title") if state.get("next_task") else None,
        }
        return {
            "user": {
                "user_id": user.id,
                "display_name": user.name or user.username,
            },
            "course": {
                "course_id": course.id,
                "course_name": course.title,
                "id": course.id,
                "name": course.title,
                "title": course.title,
                "goal": learning_context["learning_goal"],
                "status": course_status,
            },
            "course_status": course_status,
            "learning_context": learning_context,
            "statistics": statistics,
            "continue_target": continue_target,
            "updated_at": updated_at.isoformat(),
            # 兼容现有首页和课程组件，值与 statistics 来自同一次计算。
            "progress": {
                "percentage": statistics["progress_percent"],
                "completed_tasks": statistics["completed_tasks"],
                "total_tasks": statistics["total_tasks"],
                "learning_minutes": statistics["study_minutes"],
                "accuracy": statistics["accuracy_rate"],
                "streak_days": statistics["streak_days"],
                "answered_questions": statistics["answered_questions"],
            },
            "current_stage": state.get("current_stage"),
            "current_task": current_task_payload,
            "stages": serialized_stages,
            "profile_summary": self._build_profile_summary(db, course),
            "weak_points": self._build_weak_points(db, course),
            "recommended_resources": self._build_recommended_resources(db, course),
        }

    # ── 首页新增数据聚合 ──

    @staticmethod
    def _build_profile_summary(db: Session, course: Course) -> dict | None:
        """从最新 StudentProfile 提取首页需要的画像摘要。"""
        profile = (
            db.query(StudentProfile)
            .filter(StudentProfile.student_id == course.student_id)
            .order_by(StudentProfile.version.desc())
            .first()
        )
        if not profile:
            return None
        extras = json.loads(profile.memory_strength) if profile.memory_strength else {}
        if not isinstance(extras, dict):
            extras = {}
        return {
            "completeness": round(float(profile.completeness or 0) * 100),
            "cognitive_style": profile.cognitive_style or "",
            "preferred_resources": extras.get("preferred_resources") or [],
            "can_start_journey": bool(extras.get("can_start_journey")),
        }

    @staticmethod
    def _build_weak_points(db: Session, course: Course) -> list[dict]:
        """从最新 EvaluationReport 读取薄弱知识点（top 3）。"""
        report = (
            db.query(EvaluationReport)
            .filter(
                EvaluationReport.student_id == course.student_id,
                EvaluationReport.course_id == course.id,
                EvaluationReport.has_sufficient_data.is_(True),
            )
            .order_by(EvaluationReport.created_at.desc())
            .first()
        )
        if not report:
            return []
        weak_topics = json.loads(report.weak_topics) if report.weak_topics else []
        if not isinstance(weak_topics, list):
            return []
        # weak_topics 可能是 str 列表或 dict 列表，做归一化
        result = []
        for item in weak_topics[:3]:
            if isinstance(item, dict):
                result.append(item)
            elif isinstance(item, str):
                result.append({"name": item, "score": None, "reason": "来自最近评估"})
        return result

    @staticmethod
    def _build_recommended_resources(db: Session, course: Course) -> list[dict]:
        """从 Resource 表读取当前课程已生成的资源（最新4条）。"""
        rows = (
            db.query(Resource)
            .filter(
                Resource.student_id == course.student_id,
                Resource.course_id == course.id,
                Resource.generation_status == "ready",
            )
            .order_by(Resource.created_at.desc())
            .limit(4)
            .all()
        )
        result = []
        for r in rows:
            result.append({
                "id": r.id,
                "title": r.title,
                "type": r.type,
                "topic": r.topic or "",
                "difficulty": r.difficulty or "中级",
                "task_id": r.task_id or "",
                "stage_id": r.stage_id or "",
                "generation_source": r.generation_source or "agent",
                "trigger_source": r.trigger_source or "",
                "created_at": r.created_at.isoformat() if r.created_at else "",
            })
        return result

    def start_study_session(
        self,
        db: Session,
        *,
        user: User,
        course_id: str,
        task_id: Optional[str] = None,
    ) -> dict:
        course = self._require_course(db, user, course_id)
        path = self._resolve_effective_path(db, user, course)
        if path.status == "completed":
            raise ApiError("COURSE_ALREADY_COMPLETED", "课程已经完成，无需开启新的学习会话", status_code=409)
        task = None
        if task_id:
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

        existing = (
            db.query(StudySession)
            .filter(
                StudySession.user_id == user.id,
                StudySession.course_id == course.id,
                StudySession.path_id == path.id,
                StudySession.task_id == (task.task_id if task else None),
                StudySession.status == "active",
            )
            .order_by(StudySession.started_at.desc())
            .first()
        )
        if existing:
            return _study_session_dict(existing, reused=True)

        session = StudySession(
            id=f"study_{uuid.uuid4().hex}",
            user_id=user.id,
            course_id=course.id,
            path_id=path.id,
            stage_id=task.stage_id if task else path.current_stage_id,
            task_id=task.task_id if task else None,
            status="active",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return _study_session_dict(session, reused=False)

    def close_study_session(
        self,
        db: Session,
        *,
        user: User,
        course_id: str,
        session_id: str,
    ) -> dict:
        self._require_course(db, user, course_id)
        session = (
            db.query(StudySession)
            .filter(
                StudySession.id == session_id,
                StudySession.user_id == user.id,
                StudySession.course_id == course_id,
            )
            .first()
        )
        if not session:
            raise ApiError("STUDY_SESSION_NOT_FOUND", "学习会话不存在", status_code=404)
        if session.status != "active":
            return _study_session_dict(session, reused=True)

        ended_at = datetime.datetime.utcnow()
        elapsed = max(
            0,
            round((ended_at - session.started_at).total_seconds()),
        )
        session.ended_at = ended_at
        session.duration_seconds = min(elapsed, 4 * 60 * 60)
        session.status = "completed" if session.duration_seconds >= 10 else "discarded"
        if session.status == "discarded":
            session.duration_seconds = 0
        db.commit()
        db.refresh(session)
        return _study_session_dict(session, reused=False)

    def get_learning_context(
        self,
        db: Session,
        *,
        user: User,
        course_id: str,
        task_id: Optional[str] = None,
    ) -> dict:
        if task_id and str(task_id).lower() in {"null", "undefined", "none"}:
            raise ApiError("LEARNING_CONTEXT_MISMATCH", "任务参数无效", status_code=400)
        course = self._require_course(db, user, course_id)
        path = self._resolve_effective_path(db, user, course)
        stages, tasks = self._load_ordered_path_entities(db, path)
        if not stages or not tasks:
            raise ApiError("LEARNING_PATH_NOT_FOUND", "学习路径缺少可执行的阶段或任务", status_code=404)

        stage_by_id = {stage.stage_id: stage for stage in stages}
        effective_status = self._effective_statuses(path, stages, tasks)
        path_progress = self._progress(tasks, effective_status)
        course_completed = path_progress["total"] > 0 and path_progress["completed"] >= path_progress["total"]
        selected_task = None
        if task_id:
            selected_task = next((task for task in tasks if task.task_id == task_id), None)
            if not selected_task:
                if course_completed:
                    raise ApiError("COURSE_ALREADY_COMPLETED", "课程已经完成，请查看学习总结", status_code=404)
                raise ApiError("LEARNING_TASK_NOT_FOUND", "任务不存在或不属于当前课程", status_code=404)
        if not selected_task:
            selected_task = None if course_completed else self._continue_task(tasks, effective_status)

        selected_stage = (
            stage_by_id.get(selected_task.stage_id)
            if selected_task
            else self._resolve_current_stage(path, stages, selected_task)
        )
        stage_tasks = [task for task in tasks if task.stage_id == selected_stage.stage_id]
        stage_progress = self._progress(stage_tasks, effective_status)
        serialized_tasks = [
            self._task_dict(task, effective_status[task.task_id], selected_stage)
            for task in stage_tasks
        ]
        current_task = (
            self._task_dict(
                selected_task,
                effective_status[selected_task.task_id],
                selected_stage,
            )
            if selected_task
            else None
        )
        state = self.resolve_active_learning_state(db, user=user, course_id=course.id)

        return {
            "course": {
                "id": course.id,
                "course_id": course.id,
                "name": course.title,
                "title": course.title,
                "goal": course.goal or path.goal or "",
            },
            "path": self._path_dict(path, stages, tasks, effective_status),
            "stage": self._stage_dict(selected_stage) if selected_stage else None,
            "current_task": current_task,
            "tasks": serialized_tasks,
            "progress": stage_progress,
            "path_progress": path_progress,
            "course_status": state["course_status"],
            "continue_target": state["continue_target"],
            "generation": self._generation_dict(path),
            "tutor_context": {
                "user_id": user.id,
                "course_id": course.id,
                "stage_id": selected_stage.stage_id if selected_stage else None,
                "task_id": selected_task.task_id if selected_task else None,
                "knowledge_point_ids": _loads(selected_stage.knowledge_point_ids, []) if selected_stage else [],
                "current_knowledge_point": selected_task.title if selected_task else None,
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
        path = self._resolve_effective_path(db, user, course)
        if path.status == "completed":
            raise ApiError("COURSE_ALREADY_COMPLETED", "课程已经完成", status_code=409)
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

    @staticmethod
    def _is_profile_ready_for_path(db: Session, course: Course) -> bool:
        """检查课程关联的学生画像是否已就绪（可生成学习路径）。"""
        from models.student import StudentProfile
        import json as _json

        profile = (
            db.query(StudentProfile)
            .filter(StudentProfile.student_id == course.student_id)
            .order_by(StudentProfile.version.desc())
            .first()
        )
        if not profile:
            return False

        # 从 memory_strength 中读取 can_start_journey
        extras = _json.loads(profile.memory_strength) if profile.memory_strength else {}
        if isinstance(extras, dict):
            if extras.get("can_start_journey"):
                return True

        # 备选：通过 completeness 判断（>= PROFILE_READY_THRESHOLD）
        try:
            from config import PROFILE_READY_THRESHOLD
        except ModuleNotFoundError:
            PROFILE_READY_THRESHOLD = 0.75
        return float(profile.completeness or 0) >= PROFILE_READY_THRESHOLD

    def _resolve_effective_path(
        self,
        db: Session,
        user: User,
        course: Course,
        *,
        allow_missing: bool = False,
    ) -> Optional[LearningPath]:
        paths = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == course.student_id,
                LearningPath.user_id == user.id,
                LearningPath.course_id == course.id,
                LearningPath.status != "archived",
            )
            .order_by(LearningPath.version.desc())
            .all()
        )
        active_paths = [path for path in paths if path.status == "active"]
        if len(active_paths) > 1:
            raise ApiError(
                "LEARNING_PATH_STATE_CONFLICT",
                "当前课程存在多个有效学习路径，请先处理路径版本状态",
                status_code=409,
            )
        path = active_paths[0] if active_paths else next(
            (item for item in paths if item.status == "completed"),
            None,
        )
        if not path:
            if allow_missing:
                return None
            raise ApiError("LEARNING_PATH_NOT_FOUND", "当前课程还没有学习路径", status_code=404)
        self.planner_service.ensure_normalized_entities(db, path)
        return path

    def _load_ordered_path_entities(
        self,
        db: Session,
        path: LearningPath,
    ) -> tuple[list[LearningStage], list[LearningTask]]:
        stages = (
            db.query(LearningStage)
            .filter(LearningStage.path_id == path.id)
            .order_by(LearningStage.order.asc())
            .all()
        )
        tasks = (
            db.query(LearningTask)
            .filter(LearningTask.path_id == path.id)
            .all()
        )
        stage_order = {stage.stage_id: stage.order for stage in stages}
        tasks.sort(key=lambda item: (stage_order.get(item.stage_id, 999), item.order))
        return stages, tasks

    def _resolve_current_stage(
        self,
        path: LearningPath,
        stages: list[LearningStage],
        current_task: Optional[LearningTask],
    ) -> Optional[LearningStage]:
        if not stages:
            return None
        if current_task:
            matched = next((stage for stage in stages if stage.stage_id == current_task.stage_id), None)
            if matched:
                return matched
        return next(
            (stage for stage in stages if stage.stage_id == path.current_stage_id),
            None,
        ) or next(
            (stage for stage in stages if stage.order == int(path.current_stage or 1)),
            stages[-1],
        )

    def _serialized_stages(
        self,
        stages: list[LearningStage],
        tasks: list[LearningTask],
        statuses: dict[str, str],
    ) -> list[dict]:
        tasks_by_stage: dict[str, list[LearningTask]] = {}
        for task in tasks:
            tasks_by_stage.setdefault(task.stage_id, []).append(task)
        return [
            {
                **self._stage_dict(stage),
                "tasks": [
                    self._task_dict(task, statuses[task.task_id], stage)
                    for task in tasks_by_stage.get(stage.stage_id, [])
                ],
            }
            for stage in stages
        ]

    def _empty_learning_state(self, course: Course, user: User, course_status: str) -> dict:
        return {
            "user": {
                "user_id": user.id,
                "display_name": user.name or user.username,
            },
            "course": {
                "course_id": course.id,
                "course_name": course.title,
                "id": course.id,
                "name": course.title,
                "title": course.title,
                "status": course_status,
            },
            "learning_goal": course.goal or "",
            "course_status": course_status,
            "path": None,
            "progress": {
                "completed_tasks": 0,
                "total_tasks": 0,
                "percent": 0,
                "completed": 0,
                "total": 0,
            },
            "course_status": course_status,
            "current_stage": None,
            "current_task": None,
            "next_task": None,
            "continue_target": {
                "type": "profile_setup",
                "route": f"/course/{course.id}/profile/setup",
                "task_id": None,
            },
            "profile_conversation": {
                "conversation_id": f"profile-{course.id}-draft",
                "route": f"/course/{course.id}/profile/setup",
            },
            "updated_at": (course.updated_at or datetime.datetime.utcnow()).isoformat(),
        }

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
        # v3: extract adaptation_reason from resource_blueprint
        blueprint = _loads(stage.resource_blueprint, {})
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
            "unlock_conditions": _loads(stage.unlock_conditions, []),
            "adaptation_reason": blueprint.get("adaptation_reason", "") if isinstance(blueprint, dict) else "",
        }

    @staticmethod
    def _task_dict(
        task: LearningTask,
        status: str,
        stage: LearningStage,
    ) -> dict:
        content = task.content or _default_task_content(task, stage)
        # v3: extract extended metadata from content JSON
        meta = {}
        metadata_fields = (
            "dynamic_source",
            "unlock_condition",
            "trigger_source",
            "adjustment_reason",
            "content_preparation_status",
        )
        if isinstance(content, dict):
            meta = {k: v for k, v in content.items() if k in metadata_fields}
        # Also try parsing if content is a JSON string
        elif isinstance(content, str) and content.strip().startswith("{"):
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    meta = {k: v for k, v in parsed.items() if k in metadata_fields}
            except (json.JSONDecodeError, TypeError):
                pass
        if meta.get("dynamic_source"):
            meta["content_preparation_status"] = (
                "ready" if task.resource_id else meta.get("content_preparation_status", "pending")
            )

        result = {
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
        # Merge v3 extended fields
        result.update(meta)
        return result

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
        if tasks and len(completed) == len({task.task_id for task in tasks}):
            path.status = "completed"
            if stages:
                path.current_stage = stages[-1].order
                path.current_stage_id = stages[-1].stage_id
            return

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


def _score_is_correct(score: Optional[float]) -> bool:
    if score is None:
        return False
    value = float(score)
    return value >= 60 if value > 1 else value >= 0.6


def _current_streak(activity_dates: set[datetime.date]) -> int:
    normalized = {
        value.date() if isinstance(value, datetime.datetime) else value
        for value in activity_dates
    }
    today = _local_activity_date(datetime.datetime.utcnow())
    streak = 0
    while today - datetime.timedelta(days=streak) in normalized:
        streak += 1
    return streak


def _local_activity_date(value: datetime.datetime) -> datetime.date:
    """项目统一使用 Asia/Shanghai 自然日；数据库时间为 UTC naive datetime。"""
    if value.tzinfo is not None:
        value = value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return (value + datetime.timedelta(hours=8)).date()


def _study_session_dict(session: StudySession, *, reused: bool) -> dict:
    return {
        "session_id": session.id,
        "id": session.id,
        "user_id": session.user_id,
        "course_id": session.course_id,
        "path_id": session.path_id,
        "stage_id": session.stage_id,
        "task_id": session.task_id,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "duration_seconds": max(0, int(session.duration_seconds or 0)),
        "status": session.status,
        "reused": reused,
    }


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
