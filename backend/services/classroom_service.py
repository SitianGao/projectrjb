"""互动课堂业务服务。"""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from api.response import ApiError
from models.auth import Course
from models.classroom import (
    ClassroomQuizAttempt,
    ClassroomSceneProgress,
    ClassroomSession,
    InteractiveClassroom,
)
from models.evaluation import LearningRecord, WrongQuestion
from models.learning_path import LearningPath
from models.resource import Resource
from services.openmaic_classroom_client import OpenMaicClassroomClient


CLASSROOM_TYPE = "interactive_classroom"


class ClassroomService:
    def __init__(self, profile_service, evaluate_service=None, planner_service=None, client=None):
        self.profile_service = profile_service
        self.evaluate_service = evaluate_service
        self.planner_service = planner_service
        self.client = client or OpenMaicClassroomClient()

    def get_course_for_user(self, db: Session, user, course_id: str) -> Course:
        course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
        if not course:
            raise ApiError("COURSE_SCOPE_MISMATCH", "课程不存在或不属于当前用户", status_code=403)
        return course

    async def generate_for_stage(
        self,
        db: Session,
        *,
        user,
        course_id: str,
        stage_id: str,
        task_id: str = "task_gradient_classroom",
        topic: str = "梯度下降与学习率",
    ) -> dict[str, Any]:
        course = self.get_course_for_user(db, user, course_id)
        profile = self.profile_service.get_profile(db, course.student_id) or {}
        stage = self._find_stage(db, course.student_id, stage_id)
        brief = self.build_generation_brief(
            user_id=user.id,
            course=course,
            stage=stage,
            task_id=task_id,
            topic=topic,
            profile=profile,
        )
        data = await self.client.generate_classroom(brief)
        classroom = self._save_classroom(db, course, user.id, brief, data)
        return self.to_dict(classroom)

    def build_generation_brief(
        self,
        *,
        user_id: str,
        course: Course,
        stage: dict[str, Any] | None,
        task_id: str,
        topic: str,
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        learning_objectives = _objectives(stage)
        knowledge_point_ids = _knowledge_points(stage) or [
            "kp_loss_function",
            "kp_gradient",
            "kp_learning_rate",
            "kp_convergence",
        ]
        goal_ids = [
            item.get("goal_id")
            for item in (stage or {}).get("learning_objectives", [])
            if isinstance(item, dict) and item.get("goal_id")
        ] or ["goal_gradient_update", "goal_learning_rate"]
        return {
            "user_id": user_id,
            "course_id": course.id,
            "stage_id": str((stage or {}).get("stage_id") or "stage_gradient_descent"),
            "task_id": task_id,
            "classroom_id": "classroom_gradient_001",
            "course_name": course.title or "人工智能与深度学习",
            "title": "梯度下降与学习率沉浸式课堂",
            "topic": topic,
            "difficulty": "medium",
            "audience": "具有 Python 基础的大学本科生",
            "estimated_minutes": 25,
            "learning_goal_ids": goal_ids,
            "learning_objectives": learning_objectives,
            "knowledge_point_ids": knowledge_point_ids,
            "student_profile": {
                "knowledge_level": profile.get("knowledge_level") or "beginner",
                "mathematics_level": "weak" if "数学" in _list(profile.get("weakness")) else "normal",
                "cognitive_style": profile.get("cognitive_style") or "case_driven",
                "weak_points": _list(profile.get("weakness")) or ["学习率选择"],
                "preferred_resources": ["simulation", "ppt", "exercise", "code_case"],
            },
            "scene_requirements": [
                "AI教师课程导入",
                "损失函数与梯度概念讲解",
                "参数沿负梯度方向更新的白板演示",
                "学习率交互模拟",
                "AI同学讨论",
                "课堂即时测验",
                "简单代码案例",
                "课堂总结",
            ],
            "enable_tts": True,
            "enable_subtitle": True,
            "enable_quiz": True,
            "enable_simulation": True,
            "enable_whiteboard": True,
            "enable_code_demo": True,
            "references": [],
        }

    def get_or_create_demo_classroom(self, db: Session, user, course_id: str) -> dict[str, Any]:
        course = self.get_course_for_user(db, user, course_id)
        existing = (
            db.query(InteractiveClassroom)
            .filter(InteractiveClassroom.course_id == course.id, InteractiveClassroom.task_id == "task_gradient_classroom")
            .order_by(InteractiveClassroom.created_at.desc())
            .first()
        )
        if existing:
            return self.to_dict(existing)
        from services.openmaic_classroom_client import build_gradient_descent_classroom

        stage = self._find_stage(db, course.student_id, "stage_gradient_descent")
        brief = self.build_generation_brief(
            user_id=user.id,
            course=course,
            stage=stage,
            task_id="task_gradient_classroom",
            topic="梯度下降与学习率",
            profile=self.profile_service.get_profile(db, course.student_id) or {},
        )
        classroom = self._save_classroom(db, course, user.id, brief, build_gradient_descent_classroom(brief))
        return self.to_dict(classroom)

    def get_classroom(self, db: Session, user, classroom_id: str) -> dict[str, Any]:
        classroom = db.query(InteractiveClassroom).filter(InteractiveClassroom.id == classroom_id).first()
        if not classroom:
            raise ApiError("CLASSROOM_NOT_FOUND", "课堂不存在", status_code=404)
        self.get_course_for_user(db, user, classroom.course_id)
        return self.to_dict(classroom)

    def create_session(self, db: Session, user, classroom_id: str) -> dict[str, Any]:
        classroom = db.query(InteractiveClassroom).filter(InteractiveClassroom.id == classroom_id).first()
        if not classroom:
            raise ApiError("CLASSROOM_NOT_FOUND", "课堂不存在", status_code=404)
        self.get_course_for_user(db, user, classroom.course_id)
        session = (
            db.query(ClassroomSession)
            .filter(
                ClassroomSession.classroom_id == classroom.id,
                ClassroomSession.user_id == user.id,
                ClassroomSession.task_id == classroom.task_id,
            )
            .first()
        )
        if not session:
            session = ClassroomSession(
                id=f"classroom_session_{uuid.uuid4().hex[:12]}",
                classroom_id=classroom.id,
                user_id=user.id,
                course_id=classroom.course_id,
                student_id=classroom.student_id,
                stage_id=classroom.stage_id,
                task_id=classroom.task_id,
                total_scene_count=len(_json(classroom.scenes, [])),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        return self.session_to_dict(session)

    def update_scene(self, db: Session, user, classroom_id: str, session_id: str, scene_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._session(db, user, classroom_id, session_id)
        progress = (
            db.query(ClassroomSceneProgress)
            .filter(ClassroomSceneProgress.session_id == session_id, ClassroomSceneProgress.scene_id == scene_id)
            .first()
        )
        if not progress:
            progress = ClassroomSceneProgress(
                id=f"scene_progress_{uuid.uuid4().hex[:12]}",
                session_id=session_id,
                classroom_id=classroom_id,
                scene_id=scene_id,
            )
            db.add(progress)
        progress.status = payload.get("status") or progress.status
        progress.progress = float(payload.get("progress", progress.progress or 0))
        progress.interactions = json.dumps(payload.get("interactions", []), ensure_ascii=False)
        if progress.status == "completed" and not progress.completed_at:
            progress.completed_at = datetime.datetime.utcnow()
        self._update_session_counts(db, session)
        db.commit()
        db.refresh(progress)
        return self.scene_progress_to_dict(progress)

    def submit_quiz(self, db: Session, user, classroom_id: str, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._session(db, user, classroom_id, session_id)
        classroom = db.query(InteractiveClassroom).filter(InteractiveClassroom.id == classroom_id).first()
        questions = _quiz_questions(_json(classroom.scenes, []))
        answers = payload.get("answers") or {}
        results = []
        correct_count = 0
        for question in questions:
            qid = question["question_id"]
            user_answer = answers.get(qid)
            correct = question.get("answer")
            is_correct = _normalize_answer(user_answer) == _normalize_answer(correct)
            correct_count += 1 if is_correct else 0
            attempt = ClassroomQuizAttempt(
                id=f"quiz_attempt_{uuid.uuid4().hex[:12]}",
                session_id=session_id,
                classroom_id=classroom_id,
                scene_id="scene_quiz",
                question_id=qid,
                user_answer=json.dumps(user_answer, ensure_ascii=False),
                correct_answer=json.dumps(correct, ensure_ascii=False),
                is_correct=1 if is_correct else 0,
                hint_level=1 if is_correct else 2,
                knowledge_point_ids=json.dumps(question.get("knowledge_point_ids", []), ensure_ascii=False),
            )
            db.add(attempt)
            if not is_correct:
                db.add(WrongQuestion(
                    id=f"wrong_{uuid.uuid4().hex[:12]}",
                    student_id=session.student_id,
                    resource_id=classroom.resource_id,
                    question_id=f"{classroom_id}:{qid}",
                    topic=classroom.topic,
                    question=question.get("question", ""),
                    question_text=question.get("question", ""),
                    options=json.dumps(question.get("options", []), ensure_ascii=False),
                    user_answer=json.dumps(user_answer, ensure_ascii=False),
                    correct_answer=json.dumps(correct, ensure_ascii=False),
                    explanation=question.get("explanation", ""),
                ))
            results.append({
                "question_id": qid,
                "is_correct": is_correct,
                "correct_answer": correct,
                "explanation": question.get("explanation", ""),
                "knowledge_point_ids": question.get("knowledge_point_ids", []),
                "tutor_hint": self.quiz_hint(question, is_correct),
            })
        total = max(len(questions), 1)
        session.quiz_score = round(correct_count / total * 100, 1)
        session.quiz_accuracy = round(correct_count / total, 3)
        db.commit()
        return {"score": session.quiz_score, "accuracy": session.quiz_accuracy, "results": results}

    def complete(self, db: Session, user, classroom_id: str, session_id: str) -> dict[str, Any]:
        session = self._session(db, user, classroom_id, session_id)
        if session.status == "completed":
            return self.session_to_dict(session)
        classroom = db.query(InteractiveClassroom).filter(InteractiveClassroom.id == classroom_id).first()
        self._update_session_counts(db, session)
        session.status = "completed"
        session.completed_at = datetime.datetime.utcnow()
        elapsed = session.completed_at - session.started_at
        session.actual_learning_minutes = max(1, round(elapsed.total_seconds() / 60))
        session.tutor_summary = self.build_tutor_summary(session)
        session.evaluation_result = json.dumps(self.evaluate_classroom(session), ensure_ascii=False)
        db.add(LearningRecord(
            id=f"record_{uuid.uuid4().hex[:12]}",
            student_id=session.student_id,
            resource_id=classroom.resource_id,
            action="complete",
            topic=classroom.topic,
            score=session.quiz_score,
            time_spent=session.actual_learning_minutes * 60,
        ))
        self._update_profile_after_classroom(db, session)
        db.commit()
        db.refresh(session)
        return self.session_to_dict(session)

    def tutor_reply(self, db: Session, user, classroom_id: str, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._session(db, user, classroom_id, session_id)
        classroom = db.query(InteractiveClassroom).filter(InteractiveClassroom.id == classroom_id).first()
        session.tutor_question_count = (session.tutor_question_count or 0) + 1
        question = payload.get("question") or "解释当前场景"
        scene_id = payload.get("scene_id") or "scene_learning_rate_simulation"
        response = {
            "answer": _tutor_answer(question, scene_id),
            "response_type": "guided_explanation",
            "knowledge_point_ids": ["kp_learning_rate", "kp_convergence"] if "学习率" in question or scene_id.endswith("simulation") else _json(classroom.knowledge_point_ids, []),
            "suggested_action": {
                "type": "adjust_simulation",
                "instruction": "尝试将学习率调整为 0.1，再观察曲线变化。",
            } if scene_id.endswith("simulation") else None,
            "check_question": {
                "question": "学习率过小时，训练过程通常会出现什么现象？",
                "expected_concept": "收敛速度较慢",
            },
            "recommended_scene_id": None,
            "confidence": 0.91,
        }
        db.commit()
        return response

    def check_intervention(self, db: Session, user, classroom_id: str, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._session(db, user, classroom_id, session_id)
        actions = payload.get("user_actions") or []
        divergent = [
            item for item in actions[-5:]
            if item.get("action") == "set_learning_rate" and float(item.get("value", 0) or 0) >= 1.0
        ]
        if len(divergent) >= 3:
            return {
                "should_intervene": True,
                "message": "看起来你在学习率选择上遇到了困难。可以先比较 0.001、0.1 和 2.0 三种学习率对应的损失曲线，再总结规律。",
                "intervention_cooldown_seconds": 45,
            }
        return {"should_intervene": False}

    def evaluate(self, db: Session, user, classroom_id: str, session_id: str) -> dict[str, Any]:
        session = self._session(db, user, classroom_id, session_id)
        return self.evaluate_classroom(session)

    def _save_classroom(self, db: Session, course: Course, user_id: str, brief: dict[str, Any], data: dict[str, Any]) -> InteractiveClassroom:
        classroom_id = data.get("classroom_id") or f"classroom_{uuid.uuid4().hex[:10]}"
        existing = db.query(InteractiveClassroom).filter(InteractiveClassroom.id == classroom_id).first()
        if existing:
            return existing
        resource = Resource(
            id=f"resource_{uuid.uuid4().hex[:12]}",
            student_id=course.student_id,
            type=CLASSROOM_TYPE,
            title=data.get("title") or "互动课堂",
            content=json.dumps({"classroom_id": classroom_id, "summary": data.get("summary", "")}, ensure_ascii=False),
            topic=data.get("topic") or brief.get("topic"),
            difficulty=brief.get("difficulty", "medium"),
            source_refs=json.dumps(data.get("source_ids", []), ensure_ascii=False),
        )
        db.add(resource)
        classroom = InteractiveClassroom(
            id=classroom_id,
            user_id=user_id,
            course_id=course.id,
            student_id=course.student_id,
            stage_id=str(brief.get("stage_id")),
            task_id=brief.get("task_id"),
            resource_id=resource.id,
            title=data.get("title") or brief.get("title"),
            topic=data.get("topic") or brief.get("topic"),
            difficulty=brief.get("difficulty", "medium"),
            estimated_minutes=int(data.get("estimated_minutes") or brief.get("estimated_minutes", 25)),
            learning_goal_ids=json.dumps(brief.get("learning_goal_ids", []), ensure_ascii=False),
            knowledge_point_ids=json.dumps(brief.get("knowledge_point_ids", []), ensure_ascii=False),
            generation_brief=json.dumps(brief, ensure_ascii=False),
            scenes=json.dumps(data.get("scenes", []), ensure_ascii=False),
            validation_status=data.get("validation_status", "validated"),
            summary=data.get("summary", ""),
        )
        db.add(classroom)
        db.commit()
        db.refresh(classroom)
        return classroom

    def _find_stage(self, db: Session, student_id: str, stage_id: str) -> dict[str, Any] | None:
        path = (
            db.query(LearningPath)
            .filter(LearningPath.student_id == student_id, LearningPath.status == "active")
            .order_by(LearningPath.version.desc())
            .first()
        )
        for stage in _json(path.stages if path else "[]", []):
            if str(stage.get("stage_id")) in {str(stage_id), "2"} or "梯度下降" in str(stage.get("title", "")):
                return stage
        return None

    def _session(self, db: Session, user, classroom_id: str, session_id: str) -> ClassroomSession:
        session = db.query(ClassroomSession).filter(ClassroomSession.id == session_id, ClassroomSession.classroom_id == classroom_id).first()
        if not session:
            raise ApiError("CLASSROOM_SESSION_NOT_FOUND", "课堂会话不存在", status_code=404)
        self.get_course_for_user(db, user, session.course_id)
        return session

    def _update_session_counts(self, db: Session, session: ClassroomSession) -> None:
        rows = db.query(ClassroomSceneProgress).filter(ClassroomSceneProgress.session_id == session.id).all()
        session.completed_scene_count = sum(1 for row in rows if row.status == "completed")
        session.whiteboard_interaction_count = sum(len(_json(row.interactions, [])) for row in rows if "whiteboard" in row.scene_id)
        session.simulation_interaction_count = sum(len(_json(row.interactions, [])) for row in rows if "simulation" in row.scene_id)
        session.discussion_interaction_count = sum(len(_json(row.interactions, [])) for row in rows if "discussion" in row.scene_id)

    def _update_profile_after_classroom(self, db: Session, session: ClassroomSession) -> None:
        profile = self.profile_service.get_profile(db, session.student_id) or {}
        weakness = _list(profile.get("weakness"))
        if session.quiz_score < 80 and "学习率选择" not in weakness:
            weakness.append("学习率选择")
        profile["weakness"] = weakness
        profile["memory_strength"] = {
            **(profile.get("memory_strength") if isinstance(profile.get("memory_strength"), dict) else {}),
            "interactive_classroom_preference": "high",
            "last_update_reason": "interactive_classroom",
            "source_id": session.id,
        }
        profile["completeness"] = max(float(profile.get("completeness") or 0), 0.88)
        self.profile_service.save_profile(db, session.student_id, profile, increment_version=True)

    @staticmethod
    def quiz_hint(question: dict[str, Any], is_correct: bool) -> str:
        if is_correct:
            return "回答正确，可以继续推进课堂。"
        return f"先抓住关键概念：{question.get('explanation', '回到对应场景复习后再试一次。')}"

    @staticmethod
    def build_tutor_summary(session: ClassroomSession) -> str:
        return (
            "课堂学习总结\n\n"
            "已理解：梯度下降沿负梯度方向更新参数；学习率影响参数更新步长。\n\n"
            "仍需巩固：学习率过大导致震荡的原因，以及震荡、发散和收敛缓慢之间的区别。\n\n"
            "建议：完成学习率专项练习，回看“学习率交互模拟”。"
        )

    @staticmethod
    def evaluate_classroom(session: ClassroomSession) -> dict[str, Any]:
        lr_score = 52 if (session.quiz_score or 0) < 80 else 78
        return {
            "classroom_evaluation": {
                "overall_score": round((session.quiz_score or 70) * 0.7 + min(100, session.completed_scene_count / max(session.total_scene_count, 1) * 100) * 0.3, 1),
                "knowledge_mastery": [
                    {"knowledge_point_id": "kp_gradient", "score": 84},
                    {"knowledge_point_id": "kp_learning_rate", "score": lr_score},
                ],
                "strengths": ["能够理解负梯度方向"],
                "weaknesses": [
                    {
                        "knowledge_point_id": "kp_learning_rate",
                        "evidence": ["课堂测验相关题目答错", "模拟实验中选择过大学习率"],
                    }
                ] if lr_score < 70 else [],
                "recommendations": [{"type": "exercise", "title": "学习率专项练习"}],
                "path_adjustments": [{"action": "insert_review_task", "knowledge_point_id": "kp_learning_rate"}] if lr_score < 70 else [],
            }
        }

    @staticmethod
    def to_dict(classroom: InteractiveClassroom) -> dict[str, Any]:
        return {
            "classroom_id": classroom.id,
            "id": classroom.id,
            "user_id": classroom.user_id,
            "course_id": classroom.course_id,
            "student_id": classroom.student_id,
            "stage_id": classroom.stage_id,
            "task_id": classroom.task_id,
            "resource_id": classroom.resource_id,
            "title": classroom.title,
            "topic": classroom.topic,
            "difficulty": classroom.difficulty,
            "status": classroom.status,
            "version": classroom.version,
            "estimated_minutes": classroom.estimated_minutes,
            "learning_goal_ids": _json(classroom.learning_goal_ids, []),
            "knowledge_point_ids": _json(classroom.knowledge_point_ids, []),
            "generation_brief": _json(classroom.generation_brief, {}),
            "scenes": _json(classroom.scenes, []),
            "summary": classroom.summary,
            "validation_status": classroom.validation_status,
        }

    @staticmethod
    def session_to_dict(session: ClassroomSession) -> dict[str, Any]:
        return {
            "classroom_session_id": session.id,
            "session_id": session.id,
            "classroom_id": session.classroom_id,
            "user_id": session.user_id,
            "course_id": session.course_id,
            "stage_id": session.stage_id,
            "task_id": session.task_id,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "actual_learning_minutes": session.actual_learning_minutes,
            "completed_scene_count": session.completed_scene_count,
            "total_scene_count": session.total_scene_count,
            "viewed_slide_count": session.viewed_slide_count,
            "whiteboard_interaction_count": session.whiteboard_interaction_count,
            "simulation_interaction_count": session.simulation_interaction_count,
            "discussion_interaction_count": session.discussion_interaction_count,
            "tutor_question_count": session.tutor_question_count,
            "quiz_score": session.quiz_score,
            "quiz_accuracy": session.quiz_accuracy,
            "status": session.status,
            "tutor_summary": session.tutor_summary,
            "evaluation_result": _json(session.evaluation_result, {}),
        }

    @staticmethod
    def scene_progress_to_dict(progress: ClassroomSceneProgress) -> dict[str, Any]:
        return {
            "scene_id": progress.scene_id,
            "status": progress.status,
            "progress": progress.progress,
            "interactions": _json(progress.interactions, []),
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
        }


def _json(value: Any, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (TypeError, json.JSONDecodeError):
        return default


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value:
        return [value]
    return []


def _objectives(stage: dict[str, Any] | None) -> list[str]:
    raw = (stage or {}).get("learning_objectives") or (stage or {}).get("objectives") or []
    if isinstance(raw, str):
        return [raw]
    result = []
    for item in raw:
        if isinstance(item, dict):
            result.append(item.get("description") or item.get("title") or "")
        else:
            result.append(str(item))
    return [item for item in result if item] or ["理解梯度下降参数更新过程", "比较不同学习率对模型收敛的影响"]


def _knowledge_points(stage: dict[str, Any] | None) -> list[str]:
    return _list((stage or {}).get("knowledge_point_ids"))


def _quiz_questions(scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for scene in scenes:
        if scene.get("scene_type") == "quiz":
            return scene.get("content", {}).get("questions", [])
    return []


def _normalize_answer(value: Any) -> str:
    if isinstance(value, list):
        return "|".join(sorted(str(item).strip() for item in value))
    return str(value).strip()


def _tutor_answer(question: str, scene_id: str) -> str:
    if "震荡" in question or scene_id.endswith("simulation"):
        return "当前学习率可能设置得过大，每次参数更新跨过最低点，损失值会在两侧反复变化。建议把学习率调到 0.1，对比 2.0 的曲线。"
    if "例子" in question:
        return "可以把学习率理解成下山时每一步迈多远：步子太小走得慢，步子太大容易跨过谷底。"
    return "我会结合当前课堂场景解释：先看目标，再看变量变化，最后用一个小练习确认你是否理解。"
