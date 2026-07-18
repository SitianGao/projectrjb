"""Learning evaluation service —— 集成 EvaluateAgent（Day 9）

队长重构（main）：DB 持久化 + 统计维度 + 辅助函数
队员B增强（feature/ai-core）：EvaluateAgent LLM 增强 + 异步 SSE 入口
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import math
import uuid
from collections import defaultdict
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from api.response import ApiError
from models.auth import Course
from models.evaluation import EvaluationReport, LearningRecord, WrongQuestion
from models.learning_path import LearningPath
from models.resource import Resource

logger = logging.getLogger(__name__)


class EvaluateService:
    """学习记录管理 + 多维度评估报告（DB 持久化 + EvaluateAgent 增强）"""

    VALID_ACTIONS = {"view", "complete", "answer", "ask", "self_eval", "code_submit", "review"}

    def __init__(self, profile_service, evaluate_agent=None):
        self.profile_service = profile_service
        self.evaluate_agent = evaluate_agent

    # ── 评估入口 ──────────────────────────────────────────

    def start_evaluation(
        self,
        db: Session,
        student_id: str,
        course_id: Optional[str] = None,
        scope_type: str = "last_30_days",
        stage_id: Optional[str] = None,
        start_at: Optional[datetime.datetime] = None,
        end_at: Optional[datetime.datetime] = None,
        force: bool = False,
    ) -> Dict:
        """生成评估报告、保存到 DB（同步，纯统计）"""
        self.profile_service.get_or_create_student(db, student_id)
        context = self._resolve_evaluation_context(
            db, student_id, course_id, scope_type, stage_id, start_at, end_at
        )
        report = self._compute_report(db, context)
        duplicate = self._find_duplicate_report(db, student_id, report.get("input_data_hash"))
        if duplicate and not force:
            latest = self._report_to_dict(duplicate)
            latest["can_generate"] = False
            latest["reason"] = "no_new_learning_data"
            return latest
        saved = self._save_report(db, student_id, report)
        result = self._report_to_dict(saved)
        result["can_generate"] = True
        return result

    async def start_evaluation_async(
        self,
        db: Session,
        student_id: str,
        course_id: Optional[str] = None,
        scope_type: str = "last_30_days",
        stage_id: Optional[str] = None,
        start_at: Optional[datetime.datetime] = None,
        end_at: Optional[datetime.datetime] = None,
        force: bool = False,
    ) -> Dict:
        """异步评估入口（SSE 端点使用，含 EvaluateAgent LLM 增强）"""
        self.profile_service.get_or_create_student(db, student_id)
        context = self._resolve_evaluation_context(
            db, student_id, course_id, scope_type, stage_id, start_at, end_at
        )
        report = self._compute_report(db, context)
        duplicate = self._find_duplicate_report(db, student_id, report.get("input_data_hash"))
        if duplicate and not force:
            latest = self._report_to_dict(duplicate)
            latest["can_generate"] = False
            latest["reason"] = "no_new_learning_data"
            return latest
        # EvaluateAgent 增强：用 LLM 优化 dimensions/suggestions/review_plan
        report = await self._enhance_with_agent(student_id, db, report)
        saved = self._save_report(db, student_id, report)
        result = self._report_to_dict(saved)
        result["can_generate"] = True
        return result

    # ── 学习记录 ──────────────────────────────────────────

    def record_learning(
        self,
        db: Session,
        student_id: str,
        action: str,
        resource_id: Optional[str] = None,
        topic: Optional[str] = None,
        score: Optional[float] = None,
        time_spent: Optional[int] = None,
    ) -> Dict:
        self.profile_service.get_or_create_student(db, student_id)
        if action not in self.VALID_ACTIONS:
            raise ApiError(
                "VALIDATION_ERROR",
                f"action 必须是 {', '.join(sorted(self.VALID_ACTIONS))} 之一",
            )

        if resource_id:
            resource = (
                db.query(Resource)
                .filter(
                    Resource.id == resource_id,
                    Resource.student_id == student_id,
                )
                .first()
            )
            if not resource:
                raise ApiError("RESOURCE_NOT_FOUND", "学习资源不存在或不属于当前学生")
            if not topic:
                topic = resource.topic

        record = LearningRecord(
            id=str(uuid.uuid4()),
            student_id=student_id,
            resource_id=resource_id,
            action=action,
            topic=topic,
            score=score,
            time_spent=time_spent,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return self._record_to_dict(record)

    def build_report(
        self,
        db: Session,
        student_id: str,
        course_id: Optional[str] = None,
        scope_type: str = "last_30_days",
        stage_id: Optional[str] = None,
        start_at: Optional[datetime.datetime] = None,
        end_at: Optional[datetime.datetime] = None,
    ) -> Dict:
        """返回最新保存的报告，无报告时新建"""
        self.profile_service.get_or_create_student(db, student_id)
        if course_id:
            context = self._resolve_evaluation_context(
                db, student_id, course_id, scope_type, stage_id, start_at, end_at
            )
            student_id = context["student_id"]
        latest = (
            db.query(EvaluationReport)
            .filter(EvaluationReport.student_id == student_id)
            .order_by(EvaluationReport.created_at.desc())
            .first()
        )
        if latest:
            return self._report_to_dict(latest)
        return self.start_evaluation(
            db,
            student_id,
            course_id=course_id,
            scope_type=scope_type,
            stage_id=stage_id,
            start_at=start_at,
            end_at=end_at,
        )

    def get_progress_stats(self, db: Session, student_id: str) -> Dict:
        return self.build_report(db, student_id)["progress_stats"]

    def list_reports(
        self,
        db: Session,
        student_id: str,
        course_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        if course_id:
            context = self._resolve_evaluation_context(db, student_id, course_id)
            student_id = context["student_id"]
        rows = (
            db.query(EvaluationReport)
            .filter(EvaluationReport.student_id == student_id)
            .order_by(EvaluationReport.created_at.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
        return [self._report_to_dict(row) for row in rows]

    def get_report_by_id(self, db: Session, report_id: str) -> Optional[Dict]:
        row = db.query(EvaluationReport).filter(EvaluationReport.id == report_id).first()
        return self._report_to_dict(row) if row else None

    def list_records(self, db: Session, student_id: str, limit: int = 50) -> list[Dict]:
        self.profile_service.get_or_create_student(db, student_id)
        records = (
            db.query(LearningRecord)
            .filter(LearningRecord.student_id == student_id)
            .order_by(LearningRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._record_to_dict(record) for record in records]

    # ── 核心：计算报告（队长统计） ──────────────────────────

    def _compute_report(self, db: Session, context: Dict) -> Dict:
        """统计 + 规则化评估：课程隔离、范围过滤、结构化诊断。"""
        student_id = context["student_id"]
        path = context.get("path") or {}
        valid_topics = _extract_path_topics(path)

        query = db.query(LearningRecord).filter(LearningRecord.student_id == student_id)
        if context["scope"]["start_at"]:
            query = query.filter(LearningRecord.created_at >= context["scope"]["start_at"])
        if context["scope"]["end_at"]:
            query = query.filter(LearningRecord.created_at <= context["scope"]["end_at"])
        records = query.order_by(LearningRecord.created_at.asc()).all()
        scoped_records = [record for record in records if _record_matches_topics(record, valid_topics)]
        dropped = len(records) - len(scoped_records)
        if dropped:
            logger.warning(
                "evaluation_course_scope_mismatch student=%s course=%s dropped=%s",
                student_id,
                context.get("course_id"),
                dropped,
            )
        records = scoped_records

        wrong_questions = (
            db.query(WrongQuestion)
            .filter(WrongQuestion.student_id == student_id)
            .all()
        )
        wrong_questions = [row for row in wrong_questions if _topic_in_scope(row.topic, valid_topics)]

        scored = [record for record in records if record.score is not None]
        answer_records = [record for record in records if record.action == "answer"]
        complete_records = [record for record in records if record.action == "complete"]
        unique_completed = _unique_completed_tasks(complete_records)
        stage_progress = _build_stage_progress(path, unique_completed)
        total_tasks = stage_progress["total_tasks"]
        completed_count = min(len(unique_completed), total_tasks) if total_tasks else len(unique_completed)
        questions_answered = len(answer_records)
        tests_completed = len([record for record in records if record.action == "self_eval"])
        wrongbook_reviews = len([record for record in records if record.action == "review"])
        total_time = sum(record.time_spent or 0 for record in records)
        learning_minutes = round(total_time / 60)

        test_accuracy = _average_score(answer_records)
        knowledge_scores = _build_topic_scores(scored, valid_topics, wrong_questions)
        knowledge_mastery = _average_topic_score(knowledge_scores)
        task_completion = _clamp(round((completed_count / total_tasks) * 100)) if total_tasks else 0
        streak_days = _compute_streak_days(records)
        learning_consistency = _clamp(min(streak_days, 7) / 7 * 100)

        overall = _weighted_overall(
            knowledge_mastery,
            test_accuracy,
            task_completion,
            learning_consistency,
        )
        previous_scores = self._previous_report_scores(db, student_id)
        trend = _build_trend(previous_scores + [overall])
        confidence = _compute_confidence(
            tasks=completed_count,
            questions=questions_answered,
            tests=tests_completed,
            wrongbook_reviews=len(wrong_questions),
        )
        dimensions = [
            _dimension("knowledge_mastery", "知识掌握度", knowledge_mastery, trend["score_delta"], "基于当前课程知识点练习、错题和测评表现计算。"),
            _dimension("test_accuracy", "测评正确率", test_accuracy, None, f"基于 {questions_answered} 次作答记录计算。"),
            _dimension("task_completion", "任务完成度", task_completion, None, f"已完成 {completed_count} / {total_tasks} 个唯一学习任务。"),
            _dimension("learning_consistency", "学习连续性", learning_consistency, None, f"连续学习 {streak_days} 天，学习时长不直接等同掌握程度。"),
        ]
        strengths, weaknesses = _split_knowledge_diagnosis(
            knowledge_scores,
            wrong_questions,
            complete_records,
            context,
        )
        summary = _build_diagnosis_summary(overall, trend, weaknesses)
        path_adjustments = _build_path_adjustments(weaknesses, context)
        history = _build_daily_history(records, overall, unique_completed)
        weekly_activity = _build_weekly_activity(records)
        input_hash = _input_data_hash(records, context, path)

        total_topics = max(len(knowledge_scores), len(valid_topics))
        mastered = sum(1 for item in knowledge_scores if item["score"] >= 80)
        learning = sum(1 for item in knowledge_scores if 60 <= item["score"] < 80)
        not_started = max(total_topics - mastered - learning, 0)

        scope = {
            "type": context["scope"]["type"],
            "start_at": _iso_or_none(context["scope"]["start_at"]),
            "end_at": _iso_or_none(context["scope"]["end_at"]),
        }
        data_summary = {
            "unique_tasks_completed": completed_count,
            "total_tasks": total_tasks,
            "questions_answered": questions_answered,
            "unique_questions_answered": questions_answered,
            "tests_completed": tests_completed,
            "wrongbook_reviews": wrongbook_reviews,
            "learning_minutes": learning_minutes,
            "records_count": len(records),
        }
        overall_block = {
            "score": overall,
            "previous_score": trend["previous_score"],
            "score_delta": trend["score_delta"],
            "period_average": trend["period_average"],
            "confidence": confidence,
            "level": _score_level_text(overall),
            "short_term_trend": trend["short_term_trend"],
            "long_term_trend": trend["long_term_trend"],
        }
        structured = {
            "evaluation_id": None,
            "user_id": context.get("user_id"),
            "student_id": student_id,
            "course_id": context.get("course_id"),
            "course_name": context.get("course_name"),
            "stage_id": context.get("stage_id"),
            "stage_title": context.get("stage_title"),
            "scope": scope,
            "data_summary": data_summary,
            "overall": overall_block,
            "dimensions": {
                "knowledge_mastery": knowledge_mastery,
                "test_accuracy": test_accuracy,
                "task_completion": task_completion,
                "learning_consistency": learning_consistency,
            },
            "dimension_cards": dimensions,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "summary": summary,
            "path_adjustments": path_adjustments,
            "course_progress": stage_progress,
            "generated_at": datetime.datetime.utcnow().isoformat(),
        }
        review_plan = _build_review_plan(records, knowledge_scores)

        return {
            "student_id": student_id,
            "overall_score": overall,
            "dimensions": dimensions,
            "weak_topics": [item["name"] for item in weaknesses],
            "suggestions": [summary] + [item["reason"] for item in path_adjustments[:2]],
            "review_plan": review_plan,
            "recent_trend": overall_block["short_term_trend"],
            "completed_tasks": completed_count,
            "questions_answered": questions_answered,
            "tests_completed": tests_completed,
            "total_time": total_time,
            "topic_scores": knowledge_scores,
            "history": history,
            "weekly_activity": weekly_activity,
            "weeklyActivity": weekly_activity,
            "streak_days": streak_days,
            "streakDays": streak_days,
            "progress_stats": {
                "total_topics": total_topics,
                "mastered_topics": mastered,
                "learning_topics": learning,
                "not_started_topics": not_started,
                "streak_days": streak_days,
                "weekly_activity": weekly_activity,
                "totalTopics": total_topics,
                "masteredTopics": mastered,
                "learningTopics": learning,
                "notStartedTopics": not_started,
                "streakDays": streak_days,
                "weeklyActivity": weekly_activity,
            },
            "records": [self._record_to_dict(record) for record in records[-20:]],
            "source_summary": {
                "record_count": len(records),
                "scored_count": len(scored),
                "active_days": len({(record.created_at or datetime.datetime.utcnow()).date() for record in records}),
                "generated_by": "evaluate_service_v2",
                "dropped_scope_mismatch": dropped,
            },
            "structured": structured,
            "scope": scope,
            "data_summary": data_summary,
            "course_progress": stage_progress,
            "path_adjustments": path_adjustments,
            "input_data_hash": input_hash,
        }

    # ── EvaluateAgent 增强（队员B Day 9）───────────────────

    async def _enhance_with_agent(self, student_id: str, db: Session, report: Dict) -> Dict:
        """用 EvaluateAgent LLM 增强报告中的 AI 字段（dimensions/weak_topics/suggestions/review_plan）"""
        if not self.evaluate_agent:
            return report

        try:
            records = (
                db.query(LearningRecord)
                .filter(LearningRecord.student_id == student_id)
                .order_by(LearningRecord.created_at.asc())
                .all()
            )
            record_dicts = [self._record_to_dict(r) for r in records]
            profile = self._get_profile(db, student_id)

            raw = await self.evaluate_agent.evaluate(
                student_id=student_id,
                profile=profile,
                records=record_dicts,
                path=None,
            )
            ai_fields = self._parse_agent_result(raw)

            # 用 Agent 的 AI 增强结果覆盖统计结果（更个性化）
            if ai_fields.get("dimensions"):
                report["dimensions"] = ai_fields["dimensions"]
            if ai_fields.get("weak_topics"):
                report["weak_topics"] = ai_fields["weak_topics"]
            if ai_fields.get("suggestions"):
                report["suggestions"] = ai_fields["suggestions"]
            if ai_fields.get("review_plan"):
                report["review_plan"] = ai_fields["review_plan"]
        except Exception as exc:
            logger.warning("EvaluateAgent 增强失败，保留统计结果: %s", exc)

        return report

    @staticmethod
    def _parse_agent_result(raw: str) -> Dict:
        """解析 Agent JSON，提取 AI 增强字段"""
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return {}
        return {
            "dimensions": data.get("dimensions", []),
            "weak_topics": data.get("weak_topics", []),
            "suggestions": data.get("suggestions", []),
            "review_plan": data.get("review_plan", []),
        }

    def _get_profile(self, db: Session, student_id: str) -> Dict:
        """获取学生画像 dict（供 Agent 使用）"""
        try:
            profile = self.profile_service.get_profile(db, student_id)
            return profile if isinstance(profile, dict) else {}
        except Exception:
            return {}

    # ── 持久化 ────────────────────────────────────────────

    def _save_report(self, db: Session, student_id: str, report: Dict) -> EvaluationReport:
        record = EvaluationReport(
            id=str(uuid.uuid4()),
            student_id=student_id,
            overall_score=float(report["overall_score"]),
            dimensions=json.dumps(report["dimensions"], ensure_ascii=False),
            weak_topics=json.dumps(report["weak_topics"], ensure_ascii=False),
            suggestions=json.dumps(report["suggestions"], ensure_ascii=False),
            review_plan=json.dumps(report["review_plan"], ensure_ascii=False),
            source_snapshot=json.dumps({
                "topic_scores": report["topic_scores"],
                "history": report["history"],
                "weekly_activity": report["weekly_activity"],
                "streak_days": report["streak_days"],
                "progress_stats": report["progress_stats"],
                "records": report["records"],
                "source_summary": report["source_summary"],
                "recent_trend": report["recent_trend"],
                "completed_tasks": report["completed_tasks"],
                "questions_answered": report.get("questions_answered", 0),
                "tests_completed": report.get("tests_completed", 0),
                "total_time": report["total_time"],
                "structured": report.get("structured", {}),
                "scope": report.get("scope", {}),
                "data_summary": report.get("data_summary", {}),
                "course_progress": report.get("course_progress", {}),
                "path_adjustments": report.get("path_adjustments", []),
                "input_data_hash": report.get("input_data_hash"),
            }, ensure_ascii=False),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def _record_to_dict(record: LearningRecord) -> Dict:
        return {
            "id": record.id,
            "student_id": record.student_id,
            "resource_id": record.resource_id,
            "action": record.action,
            "topic": record.topic,
            "score": record.score,
            "time_spent": record.time_spent,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }

    @staticmethod
    def _report_to_dict(report: EvaluationReport) -> Dict:
        snapshot = _safe_json_loads(report.source_snapshot, {})
        dimensions = _safe_json_loads(report.dimensions, [])
        weak_topics = _safe_json_loads(report.weak_topics, [])
        suggestions = _safe_json_loads(report.suggestions, [])
        review_plan = _safe_json_loads(report.review_plan, [])
        overall = round(float(report.overall_score))
        structured = snapshot.get("structured") or {}
        if structured:
            structured = {**structured, "evaluation_id": report.id}

        result = {
            "report_id": report.id,
            "evaluation_id": report.id,
            "student_id": report.student_id,
            "overall_score": overall,
            "overallScore": overall,
            "dimensions": dimensions,
            "weak_topics": weak_topics,
            "weakTopics": weak_topics,
            "suggestions": suggestions,
            "review_plan": review_plan,
            "reviewPlan": review_plan,
            "recent_trend": snapshot.get("recent_trend", "flat"),
            "recentTrend": snapshot.get("recent_trend", "flat"),
            "completed_tasks": snapshot.get("completed_tasks", 0),
            "completedTasks": snapshot.get("completed_tasks", 0),
            "questions_answered": snapshot.get("questions_answered", 0),
            "questionsAnswered": snapshot.get("questions_answered", 0),
            "tests_completed": snapshot.get("tests_completed", 0),
            "testsCompleted": snapshot.get("tests_completed", 0),
            "total_time": snapshot.get("total_time", 0),
            "totalTime": snapshot.get("total_time", 0),
            "topic_scores": snapshot.get("topic_scores", []),
            "topicScores": snapshot.get("topic_scores", []),
            "history": snapshot.get("history", []),
            "weekly_activity": snapshot.get("weekly_activity", []),
            "weeklyActivity": snapshot.get("weekly_activity", []),
            "streak_days": snapshot.get("streak_days", 0),
            "streakDays": snapshot.get("streak_days", 0),
            "progress_stats": snapshot.get("progress_stats", {}),
            "records": snapshot.get("records", []),
            "source_summary": snapshot.get("source_summary", {}),
            "structured": structured,
            "scope": snapshot.get("scope", {}),
            "data_summary": snapshot.get("data_summary", {}),
            "course_progress": snapshot.get("course_progress", {}),
            "path_adjustments": snapshot.get("path_adjustments", []),
            "input_data_hash": snapshot.get("input_data_hash"),
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        }
        if structured:
            result.update({
                "course_id": structured.get("course_id"),
                "course_name": structured.get("course_name"),
                "stage_id": structured.get("stage_id"),
                "stage_title": structured.get("stage_title"),
                "overall": structured.get("overall", {}),
                "dataSummary": structured.get("data_summary", {}),
                "strengths": structured.get("strengths", []),
                "weaknesses": structured.get("weaknesses", []),
                "summary": structured.get("summary", ""),
                "pathAdjustments": structured.get("path_adjustments", []),
                "courseProgress": structured.get("course_progress", {}),
            })
        return result

    def _resolve_evaluation_context(
        self,
        db: Session,
        student_id: str,
        course_id: Optional[str] = None,
        scope_type: str = "last_30_days",
        stage_id: Optional[str] = None,
        start_at: Optional[datetime.datetime] = None,
        end_at: Optional[datetime.datetime] = None,
    ) -> Dict:
        course = None
        if course_id:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise ApiError("COURSE_NOT_FOUND", "课程不存在")
            student_id = course.student_id
        else:
            course = db.query(Course).filter(Course.student_id == student_id).first()

        path_row = (
            db.query(LearningPath)
            .filter(LearningPath.student_id == student_id, LearningPath.status == "active")
            .order_by(LearningPath.version.desc())
            .first()
        )
        path = _path_to_dict(path_row) if path_row else None
        scope = _resolve_scope(scope_type, start_at, end_at)
        current_stage = _current_stage(path, stage_id)
        if scope_type == "current_stage" and current_stage:
            stage_id = str(current_stage.get("stage_id"))

        return {
            "user_id": course.user_id if course else None,
            "student_id": student_id,
            "course_id": course.id if course else course_id,
            "course_name": course.title if course else "当前课程",
            "stage_id": str(stage_id or (current_stage.get("stage_id") if current_stage else "")),
            "stage_title": current_stage.get("title") if current_stage else "",
            "path": path,
            "scope": scope,
        }

    @staticmethod
    def _find_duplicate_report(
        db: Session,
        student_id: str,
        input_hash: Optional[str],
    ) -> Optional[EvaluationReport]:
        if not input_hash:
            return None
        latest = (
            db.query(EvaluationReport)
            .filter(EvaluationReport.student_id == student_id)
            .order_by(EvaluationReport.created_at.desc())
            .first()
        )
        if not latest:
            return None
        snapshot = _safe_json_loads(latest.source_snapshot, {})
        latest_hash = snapshot.get("input_data_hash")
        if latest_hash == input_hash:
            return latest
        return None

    @staticmethod
    def _previous_report_scores(db: Session, student_id: str) -> List[int]:
        rows = (
            db.query(EvaluationReport)
            .filter(EvaluationReport.student_id == student_id)
            .order_by(EvaluationReport.created_at.desc())
            .limit(6)
            .all()
        )
        return [round(float(row.overall_score)) for row in reversed(rows)]


# ══════════════════════════════════════════════════════════════
# 模块级辅助函数（队长）
# ══════════════════════════════════════════════════════════════

def _score_to_percent(score: float) -> float:
    score = float(score)
    return score * 100 if 0 <= score <= 1 else score


def _score_level(score: int) -> str:
    if score >= 85:
        return "优秀"
    if score >= 70:
        return "良好"
    if score >= 60:
        return "需提升"
    return "薄弱"


def _safe_json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def _clamp(value: float, min_value: int = 0, max_value: int = 100) -> int:
    return int(max(min_value, min(max_value, value)))


def _iso_or_none(value: Optional[datetime.datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _path_to_dict(path: Optional[LearningPath]) -> Optional[Dict]:
    if not path:
        return None
    return {
        "id": path.id,
        "student_id": path.student_id,
        "goal": path.goal,
        "stages": _safe_json_loads(path.stages, []),
        "current_stage": path.current_stage,
        "version": path.version,
        "status": path.status,
        "created_at": path.created_at.isoformat() if path.created_at else None,
        "updated_at": path.updated_at.isoformat() if path.updated_at else None,
    }


def _resolve_scope(
    scope_type: str,
    start_at: Optional[datetime.datetime],
    end_at: Optional[datetime.datetime],
) -> Dict:
    now = end_at or datetime.datetime.utcnow()
    normalized = scope_type or "last_30_days"
    if normalized == "last_7_days":
        start_at = now - datetime.timedelta(days=7)
    elif normalized == "last_30_days":
        start_at = now - datetime.timedelta(days=30)
    elif normalized in {"all", "course_all"}:
        start_at = None
    elif normalized == "current_stage":
        start_at = None
    elif normalized == "custom":
        start_at = start_at
    else:
        normalized = "last_30_days"
        start_at = now - datetime.timedelta(days=30)
    return {"type": normalized, "start_at": start_at, "end_at": now}


def _current_stage(path: Optional[Dict], stage_id: Optional[str] = None) -> Optional[Dict]:
    stages = path.get("stages") if isinstance(path, dict) else []
    if not isinstance(stages, list) or not stages:
        return None
    target = stage_id or path.get("current_stage") or 1
    return (
        next((stage for stage in stages if str(stage.get("stage_id")) == str(target)), None)
        or stages[0]
    )


def _extract_path_topics(path: Optional[Dict]) -> set[str]:
    topics = set()
    stages = path.get("stages") if isinstance(path, dict) else []
    if not isinstance(stages, list):
        return topics
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        for value in [stage.get("title"), *(stage.get("topics") or [])]:
            text = str(value or "").strip().lower()
            if text:
                topics.add(text)
    return topics


def _topic_in_scope(topic: Optional[str], valid_topics: set[str]) -> bool:
    if not valid_topics:
        return True
    text = str(topic or "").strip().lower()
    if not text:
        return False
    return any(text in topic_value or topic_value in text for topic_value in valid_topics)


def _record_matches_topics(record: LearningRecord, valid_topics: set[str]) -> bool:
    if not valid_topics:
        return True
    return _topic_in_scope(record.topic, valid_topics)


def _unique_completed_tasks(records: List[LearningRecord]) -> set[str]:
    ids = set()
    for record in records:
        key = record.resource_id or record.topic or record.id
        if key:
            ids.add(str(key))
    return ids


def _build_stage_progress(path: Optional[Dict], unique_completed: set[str]) -> Dict:
    stages = path.get("stages") if isinstance(path, dict) else []
    if not isinstance(stages, list) or not stages:
        return {
            "current_stage": None,
            "overall_percent": 0,
            "completed_tasks": 0,
            "remaining_tasks": 0,
            "total_tasks": 0,
            "stages": [],
        }
    current = path.get("current_stage") or 1
    rows = []
    total_tasks = 0
    completed_total = 0
    for stage in stages:
        tasks = stage.get("tasks") if isinstance(stage.get("tasks"), list) else []
        task_ids = {str(task.get("task_id") or task.get("id") or task.get("description")) for task in tasks if isinstance(task, dict)}
        completed = len(task_ids & unique_completed)
        # Historical records often do not store task_id. Fall back to task status in path.
        completed = max(completed, len([task for task in tasks if isinstance(task, dict) and task.get("status") == "completed"]))
        total = len(task_ids)
        completed = min(completed, total)
        total_tasks += total
        completed_total += completed
        percent = _clamp(round((completed / total) * 100)) if total else 0
        rows.append({
            "stage_id": stage.get("stage_id"),
            "title": stage.get("title") or f"阶段 {stage.get('stage_id')}",
            "completed_tasks": completed,
            "total_tasks": total,
            "percent": percent,
            "locked": int(stage.get("stage_id") or 0) > int(current or 1),
            "is_current": str(stage.get("stage_id")) == str(current),
        })
    return {
        "current_stage": current,
        "overall_percent": _clamp(round((completed_total / total_tasks) * 100)) if total_tasks else 0,
        "completed_tasks": min(completed_total, total_tasks),
        "remaining_tasks": max(total_tasks - completed_total, 0),
        "total_tasks": total_tasks,
        "stages": rows,
    }


def _average_score(records: List[LearningRecord]) -> int:
    scored = [record for record in records if record.score is not None]
    if not scored:
        return 0
    return _clamp(round(sum(_score_to_percent(record.score) for record in scored) / len(scored)))


def _build_topic_scores(
    scored: List[LearningRecord],
    valid_topics: set[str],
    wrong_questions: List[WrongQuestion],
) -> List[Dict]:
    by_topic = defaultdict(list)
    for record in scored:
        topic = record.topic or "综合"
        if not _topic_in_scope(topic, valid_topics):
            continue
        by_topic[topic].append(_score_to_percent(record.score))
    for wrong in wrong_questions:
        if wrong.topic and wrong.topic not in by_topic:
            by_topic[wrong.topic].append(max(0, 60 - wrong.wrong_count * 8))
    result = []
    for topic, scores in by_topic.items():
        score = _clamp(round(sum(scores) / len(scores)))
        result.append({
            "topic": topic,
            "name": topic,
            "score": score,
            "level": _score_level(score),
            "evidence_count": len(scores),
        })
    return sorted(result, key=lambda item: item["score"])


def _average_topic_score(topic_scores: List[Dict]) -> int:
    if not topic_scores:
        return 0
    return _clamp(round(sum(item.get("score", 0) for item in topic_scores) / len(topic_scores)))


def _weighted_overall(
    knowledge_mastery: int,
    test_accuracy: int,
    task_completion: int,
    learning_consistency: int,
) -> int:
    return _clamp(round(
        _clamp(knowledge_mastery) * 0.4
        + _clamp(test_accuracy) * 0.25
        + _clamp(task_completion) * 0.2
        + _clamp(learning_consistency) * 0.15
    ))


def _compute_confidence(tasks: int, questions: int, tests: int, wrongbook_reviews: int) -> float:
    raw = 0.25
    raw += min(tasks, 8) / 8 * 0.25
    raw += min(questions, 30) / 30 * 0.3
    raw += min(tests, 3) / 3 * 0.1
    raw += min(wrongbook_reviews, 6) / 6 * 0.1
    return round(min(raw, 0.95), 2)


def _build_trend(scores: List[int]) -> Dict:
    clean = [_clamp(score) for score in scores if score is not None]
    if not clean:
        return {
            "latest_score": 0,
            "previous_score": None,
            "score_delta": 0,
            "period_average": 0,
            "short_term_trend": "insufficient_data",
            "long_term_trend": "insufficient_data",
        }
    latest = clean[-1]
    previous = clean[-2] if len(clean) >= 2 else None
    delta = latest - previous if previous is not None else 0
    average = round(sum(clean) / len(clean))
    if len(clean) < 2:
        short = "insufficient_data"
    elif delta >= 5 and latest < average:
        short = "recovering"
    elif delta >= 3:
        short = "improving"
    elif delta <= -3:
        short = "declining"
    else:
        short = "stable"
    if len(clean) < 4:
        long = "insufficient_data"
    else:
        long_delta = clean[-1] - clean[0]
        long = "improving" if long_delta >= 5 else "declining" if long_delta <= -5 else "stable"
    return {
        "latest_score": latest,
        "previous_score": previous,
        "score_delta": delta,
        "period_average": average,
        "short_term_trend": short,
        "long_term_trend": long,
    }


def _dimension(name: str, label: str, score: int, delta: Optional[int], comment: str) -> Dict:
    return {
        "name": name,
        "label": label,
        "score": _clamp(score),
        "delta": delta,
        "comment": comment,
    }


def _split_knowledge_diagnosis(
    topic_scores: List[Dict],
    wrong_questions: List[WrongQuestion],
    complete_records: List[LearningRecord],
    context: Dict,
) -> tuple[List[Dict], List[Dict]]:
    wrong_by_topic = defaultdict(list)
    for wrong in wrong_questions:
        wrong_by_topic[wrong.topic or "综合"].append(wrong)
    complete_by_topic = defaultdict(int)
    for record in complete_records:
        complete_by_topic[record.topic or "综合"] += 1

    strengths = []
    weaknesses = []
    for item in topic_scores:
        topic = item["topic"]
        score = _clamp(item["score"])
        wrongs = wrong_by_topic.get(topic, [])
        evidence = [
            f"相关证据 {item.get('evidence_count', 0)} 条",
            f"相关任务完成 {complete_by_topic.get(topic, 0)} 次",
        ]
        if wrongs:
            evidence.append(f"累计错误 {sum(row.wrong_count for row in wrongs)} 次")
        base = {
            "knowledge_point_id": _topic_id(topic),
            "course_id": context.get("course_id"),
            "stage_id": context.get("stage_id"),
            "name": topic,
            "score": score,
            "evidence_count": item.get("evidence_count", 0) + len(wrongs),
            "evidence": evidence,
            "confidence": 0.8 if item.get("evidence_count", 0) >= 3 else 0.55,
        }
        if score >= 80:
            strengths.append({
                **base,
                "reason": "最近相关练习正确率较高，学习任务推进稳定。",
            })
        elif score < 70:
            priority = "high" if score < 50 else "medium"
            weaknesses.append({
                **base,
                "priority": priority,
                "reason": "相关作答或错题显示概念掌握不稳定，需要优先复习。",
                "actions": [
                    {"type": "exercise", "title": f"{topic}专项练习", "estimated_minutes": 20},
                    {"type": "document", "title": f"回看{topic}核心讲义", "estimated_minutes": 15},
                    {"type": "ai_tutor", "title": "问 AI 导师换一种方式讲解", "estimated_minutes": 10},
                ],
                "wrong_questions": [
                    {
                        "id": row.id,
                        "question_id": row.question_id,
                        "question": row.question,
                        "wrong_count": row.wrong_count,
                        "last_wrong_at": row.last_wrong_at.isoformat() if row.last_wrong_at else None,
                    }
                    for row in wrongs[:5]
                ],
            })
    return strengths[:4], weaknesses[:6]


def _build_diagnosis_summary(overall: int, trend: Dict, weaknesses: List[Dict]) -> str:
    weak_names = "、".join(item["name"] for item in weaknesses[:2])
    trend_text = {
        "recovering": "近期成绩较上一次有所回升",
        "improving": "近期成绩持续改善",
        "stable": "近期成绩基本稳定",
        "declining": "近期成绩整体下降",
        "insufficient_data": "当前数据仍然偏少",
    }.get(trend.get("short_term_trend"), "当前趋势稳定")
    if weak_names:
        return f"{trend_text}，但 {weak_names} 仍存在掌握不稳。建议先完成薄弱知识点专项练习，再进入阶段测评。"
    return f"{trend_text}，综合评分 {overall} 分。建议保持当前节奏，并用阶段测评验证迁移能力。"


def _build_path_adjustments(weaknesses: List[Dict], context: Dict) -> List[Dict]:
    items = []
    for weakness in weaknesses[:3]:
        action = "insert_review_task" if weakness.get("priority") == "high" else "add_practice"
        items.append({
            "action": action,
            "stage_id": context.get("stage_id"),
            "knowledge_point_id": weakness.get("knowledge_point_id"),
            "knowledge_point_name": weakness.get("name"),
            "reason": f"{weakness.get('name')} 掌握度 {weakness.get('score')}%，建议在当前阶段增加复习任务。",
            "estimated_score_after": [min(100, weakness.get("score", 0) + 12), min(100, weakness.get("score", 0) + 20)],
            "status": "pending_confirmation",
        })
    return items


def _build_daily_history(
    records: List[LearningRecord],
    fallback_score: int,
    unique_completed: set[str],
) -> List[Dict]:
    by_day = defaultdict(lambda: {"score_sum": 0.0, "score_count": 0, "tasks": set(), "answers": 0})
    for record in records:
        day = (record.created_at or datetime.datetime.utcnow()).date().isoformat()
        if record.action == "complete":
            by_day[day]["tasks"].add(record.resource_id or record.topic or record.id)
        if record.action == "answer":
            by_day[day]["answers"] += 1
        if record.score is not None:
            by_day[day]["score_sum"] += _score_to_percent(record.score)
            by_day[day]["score_count"] += 1
    history = []
    for day, item in sorted(by_day.items()):
        score = round(item["score_sum"] / item["score_count"]) if item["score_count"] else fallback_score
        history.append({
            "date": day,
            "score": _clamp(score),
            "tasks": min(len(item["tasks"]), len(unique_completed)),
            "unique_tasks_completed": len(item["tasks"]),
            "questions_answered": item["answers"],
        })
    return history


def _input_data_hash(records: List[LearningRecord], context: Dict, path: Optional[Dict]) -> str:
    payload = {
        "student_id": context.get("student_id"),
        "course_id": context.get("course_id"),
        "scope": {
            "type": context.get("scope", {}).get("type"),
            "start_at": _iso_or_none(context.get("scope", {}).get("start_at")),
            "end_at": _iso_or_none(context.get("scope", {}).get("end_at")),
        },
        "stage_id": context.get("stage_id"),
        "path_version": path.get("version") if isinstance(path, dict) else None,
        "records": [
            {
                "id": record.id,
                "action": record.action,
                "resource_id": record.resource_id,
                "topic": record.topic,
                "score": record.score,
                "time_spent": record.time_spent,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
            for record in records
        ],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _topic_id(topic: str) -> str:
    digest = hashlib.sha1(str(topic).encode("utf-8")).hexdigest()[:10]
    return f"kp_{digest}"


def _score_level_text(score: int) -> str:
    if score >= 85:
        return "熟练掌握"
    if score >= 70:
        return "稳步提升"
    if score >= 60:
        return "基础掌握"
    return "需要补强"


def _dimension_comment(score: int, label: str) -> str:
    if score >= 85:
        return f"{label}表现优秀，可以进入更高难度任务。"
    if score >= 70:
        return f"{label}整体良好，建议继续稳定练习。"
    if score >= 60:
        return f"{label}仍有提升空间，建议针对薄弱点复盘。"
    return f"{label}偏弱，需要优先补基础并增加练习反馈。"


def _build_suggestions(
    overall: int,
    weak_topics: list[str],
    completed: list[LearningRecord],
    records: list[LearningRecord],
    total_time: int,
) -> list[str]:
    suggestions = []
    real_weak_topics = [topic for topic in weak_topics if topic != "暂未检测到明显薄弱点"]
    if overall < 70:
        suggestions.append("先回到低分知识点的基础讲解，再用 3-5 道同类练习验证掌握情况。")
    if real_weak_topics:
        suggestions.append(f"优先复习 {real_weak_topics[0]}，复习后提交一次新的练习记录。")
    if records and len(completed) / max(len(records), 1) < 0.5:
        suggestions.append("学习记录中完成类任务偏少，建议把阅读、练习、总结串成闭环。")
    if total_time < 1800 and records:
        suggestions.append("累计学习时长偏短，建议安排至少 30 分钟连续学习后再评估。")
    if not suggestions:
        suggestions.append("当前学习节奏稳定，可以增加综合题或项目式任务来巩固迁移能力。")
    return suggestions


def _build_review_plan(records: list[LearningRecord], topic_scores: list[Dict]) -> list[Dict]:
    now = datetime.datetime.utcnow()
    topic_last_seen = {}
    for record in records:
        if not record.topic:
            continue
        current = record.created_at or now
        if record.topic not in topic_last_seen or current > topic_last_seen[record.topic]:
            topic_last_seen[record.topic] = current

    score_map = {item["topic"]: item["score"] for item in topic_scores}
    topics = set(topic_last_seen) | set(score_map)
    plan = []
    for topic in topics:
        score = score_map.get(topic, 65)
        last_seen = topic_last_seen.get(topic, now)
        days_since = max((now - last_seen).total_seconds() / 86400, 0)
        strength = max(1.0, 2.0 + (score / 100) * 8.0)
        retention = math.exp(-days_since / strength)

        if score < 60 or retention < 0.45:
            urgency = "high"
            interval_days = 1
        elif score < 75 or retention < 0.65:
            urgency = "medium"
            interval_days = 3
        else:
            urgency = "low"
            interval_days = 7

        if urgency == "low" and score >= 85 and days_since < 1:
            continue

        due_date = (now + datetime.timedelta(days=interval_days)).date().isoformat()
        plan.append({
            "topic": topic,
            "urgency": urgency,
            "due_date": due_date,
            "reason": (
                f"当前掌握度约 {score} 分，距上次学习 {days_since:.1f} 天，"
                f"遗忘曲线估算记忆保持率约 {retention:.0%}。"
            ),
            "recommended_resources": ["document", "exercise"] if score < 75 else ["reading", "exercise"],
            "retention": round(retention, 3),
            "days_since_last_study": round(days_since, 1),
            "estimated_minutes": 25 if urgency == "high" else 20 if urgency == "medium" else 15,
        })

    return sorted(plan, key=lambda item: {"high": 0, "medium": 1, "low": 2}[item["urgency"]])


def _build_weekly_activity(records: list[LearningRecord]) -> list[Dict]:
    today = datetime.datetime.utcnow().date()
    start = today - datetime.timedelta(days=6)
    by_day = {
        (start + datetime.timedelta(days=offset)).isoformat(): {
            "date": (start + datetime.timedelta(days=offset)).isoformat(),
            "studied": False,
            "minutes": 0,
            "tasks": 0,
        }
        for offset in range(7)
    }

    for record in records:
        record_date = (record.created_at or datetime.datetime.utcnow()).date()
        key = record_date.isoformat()
        if key not in by_day:
            continue
        by_day[key]["studied"] = True
        by_day[key]["minutes"] += round((record.time_spent or 0) / 60)
        by_day[key]["tasks"] += 1

    return list(by_day.values())


def _compute_streak_days(records: list[LearningRecord]) -> int:
    studied_days = {
        (record.created_at or datetime.datetime.utcnow()).date()
        for record in records
    }
    if not studied_days:
        return 0

    today = datetime.datetime.utcnow().date()
    cursor = today if today in studied_days else today - datetime.timedelta(days=1)
    streak = 0
    while cursor in studied_days:
        streak += 1
        cursor -= datetime.timedelta(days=1)
    return streak
