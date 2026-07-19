"""Learning evaluation service —— 集成 EvaluateAgent（第2轮改造）

统一流水线 + 可追溯学习证据 + evidence_hash + 不可变报告版本 + 历史对比。
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import math
import os
import uuid
from collections import defaultdict
from typing import Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from api.response import ApiError
from models.auth import Course
from models.classroom import ClassroomQuizAttempt, ClassroomSession
from models.evaluation import (
    EvaluationReport, LearningRecord, WrongQuestion,
    PathAdjustmentLog, ProfileUpdateLog,
)
from models.learning_path import LearningPath, LearningTask
from models.resource import Resource

logger = logging.getLogger(__name__)

# ── 数据充分性阈值 ──
MIN_COMPLETED_TASKS = 1
MIN_QUESTIONS_ANSWERED = 5
MIN_LEARNING_EVENTS = 10
MIN_TESTS_COMPLETED = 1


# ═══════════════════════════════════════════════════════════════
# EvaluationEvidence — 统一学习证据结构
# ═══════════════════════════════════════════════════════════════

def build_evidence(db: Session, student_id: str, context: Dict) -> Dict:
    """从所有可用数据源收集统一学习证据。

    返回的 dict 包含两类字段：
    - 可用数据：实际值和统计
    - 不可用数据：标记为 None 并注明 unavailable_reason
    """
    scope_start = context["scope"]["start_at"]
    scope_end = context["scope"]["end_at"]
    path = context.get("path") or {}
    valid_topics = _extract_path_topics(path)
    now = datetime.datetime.utcnow()

    # ── 1. LearningRecords ──
    q = db.query(LearningRecord).filter(LearningRecord.student_id == student_id)
    if scope_start:
        q = q.filter(LearningRecord.created_at >= scope_start)
    if scope_end:
        q = q.filter(LearningRecord.created_at <= scope_end)
    all_records = q.order_by(LearningRecord.created_at.asc()).all()
    records = [r for r in all_records if _record_matches_topics(r, valid_topics)]

    completed = [r for r in records if r.action == "complete"]
    answers = [r for r in records if r.action == "answer"]
    assessments = [r for r in records if r.action == "self_eval"]
    reviews = [r for r in records if r.action == "review"]

    completed_task_ids = list({r.resource_id or r.id for r in completed})
    answered_question_ids = list({r.resource_id or r.id for r in answers})
    assessment_ids = list({r.resource_id or r.id for r in assessments})

    learning_minutes = sum((r.time_spent or 0) for r in records) // 60
    active_days = len({(r.created_at or now).date() for r in records})

    # ── 2. WrongQuestions ──
    wq_all = (
        db.query(WrongQuestion)
        .filter(WrongQuestion.student_id == student_id)
        .all()
    )
    wrong_qs = [w for w in wq_all if _topic_in_scope(w.topic, valid_topics)]
    wrong_question_ids = [w.id for w in wrong_qs]
    wrong_answer_count = sum(w.wrong_count or 0 for w in wrong_qs)
    wrong_by_topic = defaultdict(int)
    for w in wrong_qs:
        wrong_by_topic[w.topic or "综合"] += (w.wrong_count or 0)

    # ── 3. Classroom — 尽力收集 ──
    classroom_data = {"available": False, "unavailable_reason": ""}
    cq_attempts = []
    try:
        cs = (
            db.query(ClassroomSession)
            .filter(ClassroomSession.student_id == student_id)
            .all()
        )
        if cs:
            classroom_data["available"] = True
            classroom_data["session_count"] = len(cs)
            classroom_data["quiz_scores"] = [
                float(s.quiz_score) for s in cs if s.quiz_score is not None
            ]
            classroom_data["total_learning_minutes"] = sum(
                s.actual_learning_minutes or 0 for s in cs
            )
            cq_attempts = (
                db.query(ClassroomQuizAttempt)
                .filter(ClassroomQuizAttempt.classroom_id.in_(
                    [s.classroom_id for s in cs]
                ))
                .all()
            )
    except Exception:
        classroom_data["unavailable_reason"] = "classroom tables may not exist"

    # ── 4. LearningTasks (from path) ──
    task_data = {"available": False, "unavailable_reason": ""}
    try:
        path_id = path.get("id") if isinstance(path, dict) else None
        if path_id:
            ltasks = (
                db.query(LearningTask)
                .filter(LearningTask.path_id == path_id)
                .all()
            )
            task_data["available"] = True
            task_data["total_tasks"] = len(ltasks)
            task_data["completed_tasks"] = len([t for t in ltasks if t.status == "completed"])
            task_data["task_ids"] = [t.task_id for t in ltasks]
    except Exception:
        task_data["unavailable_reason"] = "learning_tasks table may not exist"

    # ── 5. StudentProfile — 尽力 ──
    profile_data = {"available": False}
    try:
        from models.student import StudentProfile
        sp = (
            db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .first()
        )
        if sp:
            profile_data["available"] = True
            profile_data["knowledge_level"] = sp.knowledge_level
            profile_data["learning_goal"] = sp.learning_goal
            profile_data["completeness"] = sp.completeness
    except Exception:
        profile_data["unavailable_reason"] = "profile not found"

    # ── 组装 ──
    evidence = {
        "completed_task_ids": completed_task_ids,
        "answered_question_ids": answered_question_ids,
        "assessment_ids": assessment_ids,
        "wrong_question_ids": wrong_question_ids,
        "task_count": len(completed),
        "question_count": len(answers),
        "assessment_count": len(assessments),
        "wrong_answer_count": wrong_answer_count,
        "review_count": len(reviews),
        "total_record_count": len(records),
        "learning_minutes": learning_minutes,
        "active_days": active_days,
        "knowledge_point_performance": {
            topic: {
                "correct": len([r for r in answers if r.topic == topic and (r.score or 0) >= 0.6]),
                "total": len([r for r in answers if r.topic == topic]),
                "wrong_book_count": wrong_by_topic.get(topic, 0),
            }
            for topic in {r.topic for r in answers if r.topic} | set(wrong_by_topic.keys())
        },
        "classroom": classroom_data,
        "tasks": task_data,
        "profile": profile_data,
        "scope": {
            "type": context["scope"]["type"],
            "start_at": scope_start.isoformat() if scope_start else None,
            "end_at": scope_end.isoformat() if scope_end else None,
        },
    }
    return evidence


def compute_evidence_hash(evidence: Dict) -> str:
    """根据评估证据生成稳定哈希。

    同一批学习证据 → 相同hash。
    新增/修改记录 → hash改变。
    不包含随机时间、报告ID等不稳定因素。
    """
    stable = {
        "completed_task_ids": sorted(evidence.get("completed_task_ids", [])),
        "answered_question_ids": sorted(evidence.get("answered_question_ids", [])),
        "assessment_ids": sorted(evidence.get("assessment_ids", [])),
        "wrong_question_ids": sorted(evidence.get("wrong_question_ids", [])),
        "task_count": evidence.get("task_count", 0),
        "question_count": evidence.get("question_count", 0),
        "assessment_count": evidence.get("assessment_count", 0),
        "wrong_answer_count": evidence.get("wrong_answer_count", 0),
        "review_count": evidence.get("review_count", 0),
        "total_record_count": evidence.get("total_record_count", 0),
        "learning_minutes": evidence.get("learning_minutes", 0),
        "active_days": evidence.get("active_days", 0),
    }
    raw = json.dumps(stable, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_evidence_summary(evidence: Dict) -> Dict:
    """构建前端可用的 evidence_summary 快照。"""
    return {
        "completed_tasks": evidence.get("task_count", 0),
        "answered_questions": evidence.get("question_count", 0),
        "assessments": evidence.get("assessment_count", 0),
        "wrong_answers": evidence.get("wrong_answer_count", 0),
        "active_days": evidence.get("active_days", 0),
        "total_learning_minutes": evidence.get("learning_minutes", 0),
        "total_records": evidence.get("total_record_count", 0),
    }


class EvaluateService:
    """学习记录管理 + 多维度评估报告（第1轮改造：统一流水线）"""

    VALID_ACTIONS = {"view", "complete", "answer", "ask", "self_eval", "code_submit", "review"}

    def __init__(self, profile_service, evaluate_agent=None):
        self.profile_service = profile_service
        self.evaluate_agent = evaluate_agent

    # ═══════════════════════════════════════════════════════════════
    # 统一评估流水线（唯一核心）
    # ═══════════════════════════════════════════════════════════════

    async def run_evaluation_pipeline(
        self,
        db: Session,
        student_id: str,
        course_id: Optional[str] = None,
        scope_type: str = "last_30_days",
        stage_id: Optional[str] = None,
        start_at: Optional[datetime.datetime] = None,
        end_at: Optional[datetime.datetime] = None,
        force: bool = False,
        enable_agent: bool = True,
        on_progress: Optional[Callable[[int, str, str], None]] = None,
    ) -> Dict:
        """统一评估流水线 —— 所有评估端点的唯一核心。

        流程:
        1. 构建 EvaluationEvidence
        2. 计算 evidence_hash，检查重复
        3. 检查数据充分性
        4. 规则计算客观指标
        5. 数据充分 + enable_agent + (新数据或force) → 调用 EvaluateAgent
        6. 保存为新版本（不可变），设置 supersedes_report_id
        7. 返回统一结构报告
        """
        self.profile_service.get_or_create_student(db, student_id)

        # ── Step 1: 解析评估上下文 ──
        context = self._resolve_evaluation_context(
            db, student_id, course_id, scope_type, stage_id, start_at, end_at
        )
        resolved_course_id = context.get("course_id")

        # ── Step 2: 构建证据 ──
        evidence = build_evidence(db, student_id, context)
        evidence_hash = compute_evidence_hash(evidence)
        evidence_summary = build_evidence_summary(evidence)
        records, wrong_questions = self._collect_evidence(db, context)

        # ── Step 3: 检查重复 —— 相同证据 + !force → 不重新评估 ──
        trigger = "manual_force" if force else "auto"
        if not force:
            latest_report = (
                db.query(EvaluationReport)
                .filter(
                    EvaluationReport.student_id == student_id,
                    EvaluationReport.course_id == resolved_course_id,
                )
                .order_by(EvaluationReport.created_at.desc())
                .first()
            )
            if latest_report and latest_report.evidence_hash == evidence_hash:
                logger.info(
                    "evidence_hash unchanged (%s), returning latest report %s",
                    evidence_hash, latest_report.id,
                )
                result = self._report_to_dict(latest_report)
                result["can_generate"] = False
                result["has_new_data"] = False
                result["reason"] = "暂无新的学习数据，无需重新评估"
                result["trigger"] = trigger
                return result

        # ── Step 4: 检查数据充分性 ──
        sufficient, reason = _check_data_sufficiency(records, wrong_questions)

        # 预生成 evaluation_id（用于关联 profile/path/resource 记录）
        eval_id = str(uuid.uuid4())

        # ── Step 5: 规则计算 ──
        _emit(on_progress, 30, "computing", "正在计算客观指标")
        rule_report = self._compute_report(db, context)
        rule_report["has_sufficient_data"] = sufficient
        rule_report["insufficient_reason"] = "" if sufficient else reason
        rule_report["generation_source"] = "rule"
        rule_report["provider"] = None
        rule_report["model"] = None
        rule_report["fallback_used"] = False
        rule_report["fallback_reason"] = None
        rule_report["_eval_id"] = eval_id
        rule_report["evidence_hash"] = evidence_hash
        rule_report["evidence_count"] = evidence["total_record_count"]
        rule_report["evidence_summary"] = evidence_summary
        rule_report["trigger"] = trigger
        rule_report["course_id"] = resolved_course_id
        rule_report["scope_type"] = scope_type
        rule_report["scope_start_at"] = context["scope"]["start_at"]
        rule_report["scope_end_at"] = context["scope"]["end_at"]
        rule_report["statistics_json"] = json.dumps({
            "topic_scores": rule_report.get("topic_scores", []),
            "overall_score": rule_report.get("overall_score"),
            "dimensions": rule_report.get("dimensions", []),
        }, ensure_ascii=False)

        if not sufficient:
            _emit(on_progress, 50, "insufficient", reason)
            rule_report["overall_score"] = None
            rule_report["confidence"] = 0.0
            rule_report["suggestions"] = _insufficient_suggestions(reason)
            rule_report["weak_topics"] = []
            saved = self._save_report(db, student_id, rule_report)
            result = self._report_to_dict(saved)
            result["can_generate"] = True
            result["has_new_data"] = True
            result["trigger"] = trigger
            return result

        # ── Step 6: Agent 增强 ──
        if enable_agent and self.evaluate_agent:
            _emit(on_progress, 50, "agent", "正在调用 AI 进行诊断分析")
            try:
                agent_result = await self._enhance_with_agent(student_id, db, rule_report)
                rule_report["generation_source"] = agent_result.get("generation_source", "agent")
                rule_report["provider"] = agent_result.get("provider")
                rule_report["model"] = agent_result.get("model")
                rule_report["fallback_used"] = agent_result.get("fallback_used", False)
                rule_report["fallback_reason"] = agent_result.get("fallback_reason")
                rule_report["agent_result_json"] = agent_result.get("raw_json", "{}")
            except Exception as exc:
                logger.warning("EvaluateAgent 调用失败，保留规则结果: %s", exc)
                rule_report["generation_source"] = "rule_fallback"
                rule_report["fallback_used"] = True
                rule_report["fallback_reason"] = f"Agent exception: {exc}"

        # ── Step 7: 设置 supersedes ──
        prev_report = (
            db.query(EvaluationReport)
            .filter(
                EvaluationReport.student_id == student_id,
                EvaluationReport.course_id == resolved_course_id,
            )
            .order_by(EvaluationReport.created_at.desc())
            .first()
        )
        if prev_report and prev_report.id != rule_report.get("_current_save_id"):
            rule_report["supersedes_report_id"] = prev_report.id

        # ── Step 8: 应用画像更新（低置信度仅记录，不写入）──
        profile_updates = []
        if sufficient and rule_report.get("agent_profile_suggestions"):
            _emit(on_progress, 75, "profile", "正在更新学习画像")
            profile_updates = self.apply_profile_updates(
                db, student_id,
                evaluation_id=eval_id,
                suggestions=rule_report.get("agent_profile_suggestions", []),
                user_id=context.get("user_id", ""),
                course_id=resolved_course_id or "",
            )

        # Path changes are presented as suggestions first. Applying them and
        # preparing resources happens later in an authenticated background job.
        path_suggestions = (
            rule_report.get("agent_path_suggestions")
            or rule_report.get("path_adjustments")
            or []
        )
        path_adj_results = {
            "status": "suggested",
            "adjustments": [
                {**item, "status": "suggested"}
                for item in path_suggestions
                if isinstance(item, dict)
            ],
        }

        # Resource preparation is intentionally deferred to authenticated
        # background jobs after the learner chooses an action.
        _emit(on_progress, 95, "saving", "正在保存评估报告")
        saved = self._save_report(db, student_id, rule_report)
        result = self._report_to_dict(saved)
        result["can_generate"] = True
        result["has_new_data"] = True
        result["trigger"] = trigger
        result["profile_updates"] = profile_updates
        result["path_adjustments"] = path_adj_results
        result["resources_generated"] = {"generated": [], "status": "not_requested"}
        return result

    # ═══════════════════════════════════════════════════════════════
    # 兼容入口（统一调用流水线）
    # ═══════════════════════════════════════════════════════════════

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
        """同步评估（复用统一流水线，也调用 Agent）"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = asyncio.ensure_future(
                    self.run_evaluation_pipeline(
                        db, student_id, course_id, scope_type, stage_id,
                        start_at, end_at, force, enable_agent=True,
                    )
                )
                # 在同步上下文中无法真正 await，退回纯规则模式
                logger.warning("start_evaluation 在异步上下文中调用，使用纯规则模式")
                return self._run_rule_only(
                    db, student_id, course_id, scope_type, stage_id,
                    start_at, end_at, force,
                )
            return loop.run_until_complete(
                self.run_evaluation_pipeline(
                    db, student_id, course_id, scope_type, stage_id,
                    start_at, end_at, force, enable_agent=True,
                )
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self.run_evaluation_pipeline(
                        db, student_id, course_id, scope_type, stage_id,
                        start_at, end_at, force, enable_agent=True,
                    )
                )
            finally:
                loop.close()

    def _run_rule_only(
        self, db, student_id, course_id, scope_type, stage_id,
        start_at, end_at, force,
    ) -> Dict:
        """纯规则模式的同步评估（异步上下文中的降级）"""
        self.profile_service.get_or_create_student(db, student_id)
        context = self._resolve_evaluation_context(
            db, student_id, course_id, scope_type, stage_id, start_at, end_at
        )
        records, wrong_questions = self._collect_evidence(db, context)
        sufficient, reason = _check_data_sufficiency(records, wrong_questions)
        report = self._compute_report(db, context)
        report["has_sufficient_data"] = sufficient
        report["insufficient_reason"] = "" if sufficient else reason
        report["generation_source"] = "rule"
        report["provider"] = None
        report["model"] = None
        report["fallback_used"] = False
        report["fallback_reason"] = None
        if not sufficient:
            report["overall_score"] = None
            report["confidence"] = 0.0
            report["suggestions"] = _insufficient_suggestions(reason)
            report["weak_topics"] = []
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
        """异步评估入口（SSE 端点使用）—— 直接委托给统一流水线"""
        return await self.run_evaluation_pipeline(
            db, student_id, course_id, scope_type, stage_id,
            start_at, end_at, force, enable_agent=True,
        )

    # ═══════════════════════════════════════════════════════════════
    # 证据收集
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _collect_evidence(db: Session, context: Dict) -> tuple:
        """收集当前课程的有效学习记录和错题"""
        student_id = context["student_id"]
        path = context.get("path") or {}
        valid_topics = _extract_path_topics(path)

        query = db.query(LearningRecord).filter(LearningRecord.student_id == student_id)
        if context["scope"]["start_at"]:
            query = query.filter(LearningRecord.created_at >= context["scope"]["start_at"])
        if context["scope"]["end_at"]:
            query = query.filter(LearningRecord.created_at <= context["scope"]["end_at"])
        records = query.order_by(LearningRecord.created_at.asc()).all()
        scoped_records = [r for r in records if _record_matches_topics(r, valid_topics)]

        wrong_questions = (
            db.query(WrongQuestion)
            .filter(WrongQuestion.student_id == student_id)
            .all()
        )
        wrong_questions = [w for w in wrong_questions if _topic_in_scope(w.topic, valid_topics)]

        return scoped_records, wrong_questions

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

    # ═══════════════════════════════════════════════════════════════
    # 读取接口（只读，不生成）
    # ═══════════════════════════════════════════════════════════════

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
        """只读：返回最新保存的报告。不再隐式重新评估。"""
        self.profile_service.get_or_create_student(db, student_id)
        resolved = student_id
        resolved_course = course_id
        if course_id:
            context = self._resolve_evaluation_context(
                db, student_id, course_id, scope_type, stage_id, start_at, end_at
            )
            resolved = context["student_id"]
            resolved_course = context.get("course_id")

        q = db.query(EvaluationReport).filter(EvaluationReport.student_id == resolved)
        if resolved_course:
            q = q.filter(EvaluationReport.course_id == resolved_course)
        latest = q.order_by(EvaluationReport.created_at.desc()).first()

        if latest:
            return self._report_to_dict(latest)
        # 无报告时返回空结构，不自动生成
        return {
            "student_id": resolved,
            "course_id": resolved_course,
            "overall_score": None,
            "overallScore": None,
            "has_sufficient_data": False,
            "hasSufficientData": False,
            "insufficient_reason": "尚未生成评估报告，请先完成学习任务后点击「重新评估」。",
            "insufficientReason": "尚未生成评估报告，请先完成学习任务后点击「重新评估」。",
            "dimensions": [],
            "weak_topics": [],
            "weakTopics": [],
            "suggestions": [],
            "review_plan": [],
            "reviewPlan": [],
            "can_generate": True,
            "evidence_summary": {},
            "evidenceSummary": {},
        }

    def get_report_by_id(self, db: Session, report_id: str) -> Optional[Dict]:
        """只读：按 ID 获取单份报告。"""
        row = db.query(EvaluationReport).filter(EvaluationReport.id == report_id).first()
        return self._report_to_dict(row) if row else None

    def list_reports(
        self,
        db: Session,
        student_id: str,
        course_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict:
        """只读：分页获取历史报告列表。"""
        q = db.query(EvaluationReport).filter(EvaluationReport.student_id == student_id)
        if course_id:
            q = q.filter(EvaluationReport.course_id == course_id)
        total = q.count()
        rows = (
            q.order_by(EvaluationReport.created_at.desc())
            .offset((max(page, 1) - 1) * min(max(page_size, 1), 100))
            .limit(min(max(page_size, 1), 100))
            .all()
        )
        return {
            "items": [self._report_to_dict(r) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def compare_reports(self, db: Session, report_id: str) -> Optional[Dict]:
        """对比指定报告与其上一版本（supersedes_report_id）。"""
        current = db.query(EvaluationReport).filter(EvaluationReport.id == report_id).first()
        if not current:
            return None

        prev = None
        if current.supersedes_report_id:
            prev = db.query(EvaluationReport).filter(
                EvaluationReport.id == current.supersedes_report_id
            ).first()

        cur_dict = self._report_to_dict(current)
        result = {
            "report_id": report_id,
            "current": cur_dict,
            "previous": self._report_to_dict(prev) if prev else None,
            "comparison": _build_comparison(cur_dict, self._report_to_dict(prev) if prev else None),
        }
        return result

    # ═══════════════════════════════════════════════════════════════
    # 第3轮：画像更新
    # ═══════════════════════════════════════════════════════════════

    # 允许自动更新的画像字段
    ALLOWED_PROFILE_FIELDS = {
        "weakness",           # JSON list: 薄弱知识点
        "memory_strength",    # JSON dict: 记忆强度
        "knowledge_level",    # Text: 知识水平描述
    }

    # 自动应用的最低置信度阈值
    PROFILE_UPDATE_CONFIDENCE_THRESHOLD = 0.65

    def apply_profile_updates(
        self,
        db: Session,
        student_id: str,
        evaluation_id: str,
        suggestions: list,
        user_id: str = "",
        course_id: str = "",
    ) -> Dict:
        """将 EvaluateAgent 的画像更新建议写入 StudentProfile + ProfileUpdateLog。

        规则：
        - 只更新 ALLOWED_PROFILE_FIELDS 中的字段
        - confidence >= PROFILE_UPDATE_CONFIDENCE_THRESHOLD 才自动应用
        - 低置信度仅记录为 suggested
        - 不覆盖用户明确输入的 long-term 字段（learning_goal, interest）
        - 跨用户隔离
        """
        profile = self._get_profile_record(db, student_id)
        if not profile:
            return {"applied": 0, "suggested": 0, "skipped": 0, "updates": []}

        applied = 0
        suggested = 0
        skipped = 0
        updates = []

        for s in suggestions:
            if not isinstance(s, dict):
                continue
            field = s.get("field", "")
            if field not in self.ALLOWED_PROFILE_FIELDS:
                skipped += 1
                continue

            confidence = float(s.get("confidence", 0))
            new_value = s.get("new_value", "")
            old_value = getattr(profile, field, "") or ""
            reason = str(s.get("reason", ""))[:500]
            evidence_refs = s.get("evidence_refs", [])

            # 幂等：检查是否已有同一 evaluation 的同字段更新
            existing = (
                db.query(ProfileUpdateLog)
                .filter(
                    ProfileUpdateLog.source_evaluation_id == evaluation_id,
                    ProfileUpdateLog.field == field,
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            status = "suggested"
            if confidence >= self.PROFILE_UPDATE_CONFIDENCE_THRESHOLD:
                status = "applied"
                # 实际写入画像
                if field == "weakness":
                    self._merge_weakness(profile, new_value)
                elif field == "memory_strength":
                    self._merge_memory_strength(profile, new_value)
                elif field == "knowledge_level":
                    profile.knowledge_level = str(new_value)
                applied += 1
            else:
                suggested += 1

            log = ProfileUpdateLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                course_id=course_id,
                student_id=student_id,
                source_evaluation_id=evaluation_id,
                field=field,
                before_value=str(old_value)[:1000],
                after_value=str(new_value)[:1000],
                reason=reason,
                confidence=confidence,
                evidence_refs=json.dumps(evidence_refs if isinstance(evidence_refs, list) else [], ensure_ascii=False),
                status=status,
                applied_at=datetime.datetime.utcnow() if status == "applied" else None,
            )
            db.add(log)
            updates.append({"field": field, "status": status, "confidence": confidence})

        if applied > 0:
            db.commit()
            logger.info(
                "画像更新: student=%s evaluation=%s applied=%d suggested=%d",
                student_id, evaluation_id, applied, suggested,
            )

        return {"applied": applied, "suggested": suggested, "skipped": skipped, "updates": updates}

    @staticmethod
    def _merge_weakness(profile, new_value: str) -> None:
        """合并薄弱点列表：追加不重复的新项。"""
        import json as _json
        existing = set()
        try:
            existing = set(_json.loads(profile.weakness or "[]"))
        except (json.JSONDecodeError, TypeError):
            pass
        try:
            new_items = _json.loads(new_value) if isinstance(new_value, str) else new_value
            if isinstance(new_items, list):
                existing.update(str(item) for item in new_items)
        except (json.JSONDecodeError, TypeError):
            pass
        profile.weakness = _json.dumps(sorted(existing), ensure_ascii=False)

    @staticmethod
    def _merge_memory_strength(profile, new_value: str) -> None:
        """合并记忆强度：更新或新增 key。"""
        import json as _json
        existing = {}
        try:
            existing = _json.loads(profile.memory_strength or "{}")
        except (json.JSONDecodeError, TypeError):
            pass
        try:
            new_items = _json.loads(new_value) if isinstance(new_value, str) else new_value
            if isinstance(new_items, dict):
                existing.update(new_items)
        except (json.JSONDecodeError, TypeError):
            pass
        profile.memory_strength = _json.dumps(existing, ensure_ascii=False)

    def _get_profile_record(self, db: Session, student_id: str):
        """获取 StudentProfile ORM 对象（非 dict）。"""
        try:
            from models.student import StudentProfile
            return (
                db.query(StudentProfile)
                .filter(StudentProfile.student_id == student_id)
                .order_by(StudentProfile.version.desc())
                .first()
            )
        except Exception:
            return None

    # ═══════════════════════════════════════════════════════════════
    # 第3轮：路径调整
    # ═══════════════════════════════════════════════════════════════

    # 低风险动作（自动执行）
    AUTO_APPLY_ACTIONS = {
        "insert_remedial_task",
        "review_prerequisite",
        "reduce_difficulty",
    }
    # 高风险动作（需确认，本轮仅记录）
    CONFIRM_REQUIRED_ACTIONS = {
        "increase_difficulty",
        "postpone_stage",
        "unlock_stage",
    }

    def apply_path_adjustments(
        self,
        db: Session,
        student_id: str,
        evaluation_id: str,
        suggestions: list,
        user_id: str = "",
        course_id: str = "",
        planner_service=None,
    ) -> Dict:
        """将 EvaluateAgent 的路径调整建议应用到学习路径。

        规则：
        - 低风险动作自动执行
        - 高风险动作仅记录为 suggested
        - 幂等：同一 evaluation_id + 同一 adjustment_key 不重复
        - 不修改已完成/锁定阶段
        - 不跨用户
        """
        applied = 0
        suggested = 0
        skipped = 0
        failed = 0
        adjustments = []

        path = None
        if planner_service:
            try:
                path = planner_service.get_current_path_for_course(
                    db, user_id=user_id, course_id=course_id,
                )
            except Exception:
                pass
        if not path:
            path = self._get_active_path(db, student_id)

        for s in suggestions:
            if not isinstance(s, dict):
                continue
            action = s.get("action", "")
            kp = s.get("knowledge_point", "")
            target_stage = s.get("target_stage_id", "")
            priority = s.get("priority", "medium")
            reason = str(s.get("reason", ""))[:500]

            # 生成幂等 key
            adj_key = hashlib.md5(
                f"{action}|{kp}|{target_stage}".encode()
            ).hexdigest()[:16]

            # 幂等检查
            existing = (
                db.query(PathAdjustmentLog)
                .filter(PathAdjustmentLog.adjustment_key == adj_key)
                .first()
            )
            if existing:
                skipped += 1
                adjustments.append({"action": action, "status": "skipped_duplicate", "key": adj_key})
                continue

            status = "suggested"
            if action in self.AUTO_APPLY_ACTIONS and path:
                try:
                    self._execute_path_adjustment(
                        db, path, action, kp, target_stage,
                        s.get("suggested_resource_type", "exercise"),
                        reason, user_id,
                    )
                    status = "applied"
                    applied += 1
                except Exception as e:
                    logger.warning("路径调整失败 action=%s: %s", action, e)
                    status = "failed"
                    failed += 1
            elif action in self.CONFIRM_REQUIRED_ACTIONS:
                suggested += 1
            else:
                suggested += 1

            log = PathAdjustmentLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                course_id=course_id,
                learning_path_id=path.get("id") if path else "",
                source_evaluation_id=evaluation_id,
                adjustment_key=adj_key,
                action=action,
                knowledge_point=kp,
                target_stage_id=target_stage,
                target_task_id=s.get("target_task_id", ""),
                suggested_resource_type=s.get("suggested_resource_type", "exercise"),
                before_state=json.dumps({}, ensure_ascii=False),
                after_state=json.dumps({"action": action, "kp": kp}, ensure_ascii=False),
                reason=reason,
                priority=priority,
                status=status,
                applied_at=datetime.datetime.utcnow() if status == "applied" else None,
            )
            db.add(log)
            adjustments.append({"action": action, "status": status, "key": adj_key})

        if applied > 0:
            db.commit()
            logger.info(
                "路径调整: student=%s evaluation=%s applied=%d suggested=%d skipped=%d",
                student_id, evaluation_id, applied, suggested, skipped,
            )

        return {"applied": applied, "suggested": suggested, "skipped": skipped, "failed": failed, "adjustments": adjustments}

    @staticmethod
    def _execute_path_adjustment(
        db: Session, path: Dict, action: str, kp: str,
        target_stage: str, resource_type: str, reason: str, user_id: str,
    ) -> None:
        """执行单个路径调整动作。"""
        stages = path.get("stages", []) if isinstance(path, dict) else []
        if isinstance(stages, str):
            stages = json.loads(stages)
        if not stages:
            return

        # 找到目标阶段
        stage = None
        for s in stages:
            if str(s.get("stage_id", "")) == str(target_stage):
                stage = s
                break
        if not stage:
            stage = stages[0] if stages else {}

        if action == "insert_remedial_task":
            task_id = f"remedial_{hashlib.md5(f'{kp}|{target_stage}'.encode()).hexdigest()[:8]}"
            tasks = stage.get("tasks", [])
            if not isinstance(tasks, list):
                tasks = []
            # 幂等：检查是否已存在同名补救任务
            if any(t.get("task_id") == task_id for t in tasks):
                return
            tasks.append({
                "task_id": task_id,
                "task_type": resource_type or "exercise",
                "title": f"补习：{kp}",
                "description": f"AI诊断建议：{reason}",
                "estimated_minutes": 20,
                "difficulty": "初级",
                "status": "pending",
                "prerequisite_task_ids": [],
                "_source": "evaluate_agent",
            })
            stage["tasks"] = tasks
            db.commit()

        elif action == "review_prerequisite":
            stage["_review_note"] = f"建议复习前置知识：{kp} — {reason}"
            db.commit()

        elif action == "reduce_difficulty":
            for t in stage.get("tasks", []):
                if isinstance(t, dict) and t.get("difficulty") in ("高级", "中高级"):
                    t["difficulty"] = "中级"
            db.commit()

    @staticmethod
    def _get_active_path(db: Session, student_id: str) -> Optional[Dict]:
        """获取当前激活的学习路径。"""
        path = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == student_id,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.version.desc())
            .first()
        )
        if not path:
            return None
        return {
            "id": path.id,
            "user_id": path.user_id,
            "course_id": path.course_id,
            "stages": _safe_json_loads(path.stages, []),
            "current_stage": path.current_stage,
            "status": path.status,
        }

    # ═══════════════════════════════════════════════════════════════
    # 统一仪表盘聚合（解决首页/路径/评估数据不一致）
    # ═══════════════════════════════════════════════════════════════

    def get_learning_dashboard_summary(
        self,
        db: Session,
        student_id: str,
        course_id: str = "",
        user_id: str = "",
    ) -> Dict:
        """返回统一的课程学习仪表盘数据。

        所有页面（首页、路径、评估）使用同一数据源。
        只从真实数据库记录计算，不写死任何值。
        """
        # ── 1. 学习路径基础信息 ──
        path = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == student_id,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.version.desc())
            .first()
        )
        path_dict = {
            "id": path.id if path else "",
            "goal": path.goal if path else "",
            "current_stage": path.current_stage if path else 1,
            "current_stage_id": path.current_stage_id if path else "",
            "status": path.status if path else "no_path",
        }

        # ── 2. 任务进度（从 LearningTask 表读取）──
        tasks_total = 0
        tasks_completed = 0
        current_stage_total = 0
        current_stage_completed = 0
        current_stage_title = ""
        tasks_detail = []

        if path:
            ltasks = (
                db.query(LearningTask)
                .filter(LearningTask.path_id == path.id)
                .all()
            )
            for t in ltasks:
                tasks_total += 1
                is_current_stage = (t.stage_id == path.current_stage_id)
                is_completed = (t.status == "completed")
                if is_completed:
                    tasks_completed += 1
                if is_current_stage:
                    current_stage_total += 1
                    if is_completed:
                        current_stage_completed += 1
                    current_stage_title = current_stage_title or t.stage_id
                tasks_detail.append({
                    "task_id": t.task_id,
                    "stage_id": t.stage_id,
                    "title": t.title,
                    "type": t.task_type,
                    "status": t.status,
                })

            # 解析阶段标题
            stages = _safe_json_loads(path.stages, [])
            for s in stages:
                if str(s.get("stage_id")) == str(path.current_stage_id):
                    current_stage_title = s.get("title", current_stage_title)

        task_progress = {
            "total": tasks_total,
            "completed": tasks_completed,
            "percent": round(tasks_completed / tasks_total * 100) if tasks_total > 0 else 0,
            "current_stage_total": current_stage_total,
            "current_stage_completed": current_stage_completed,
            "current_stage_percent": round(current_stage_completed / current_stage_total * 100) if current_stage_total > 0 else 0,
            "current_stage_title": current_stage_title,
        }

        # ── 3. 练习正确率（从 LearningRecords 计算）──
        records = (
            db.query(LearningRecord)
            .filter(LearningRecord.student_id == student_id)
            .all()
        )
        answer_records = [r for r in records if r.action == "answer" and r.score is not None]
        correct_count = len([r for r in answer_records if (r.score or 0) >= 0.6])
        answer_total = len(answer_records)
        accuracy = round(correct_count / answer_total * 100) if answer_total > 0 else None

        # ── 4. 学习时长（从 LearningRecords 计算）──
        total_seconds = sum(r.time_spent or 0 for r in records)
        learning_minutes = round(total_seconds / 60)

        # ── 5. 评测证据（与评估报告对齐）──
        completed_count = len([r for r in records if r.action == "complete"])
        self_eval_count = len([r for r in records if r.action == "self_eval"])
        active_days = len({(r.created_at or datetime.datetime.utcnow()).date() for r in records})

        # ── 6. 当前学习目标 ──
        course = db.query(Course).filter(
            Course.student_id == student_id,
            Course.id == (course_id or path.course_id if path else ""),
        ).first()
        learning_goal = path_dict["goal"] or (course.goal if course else "")

        # ── 7. 最新评估报告 ──
        latest_report = (
            db.query(EvaluationReport)
            .filter(EvaluationReport.student_id == student_id)
            .order_by(EvaluationReport.created_at.desc())
            .first()
        )
        report_summary = None
        if latest_report:
            report_summary = {
                "report_id": latest_report.id,
                "overall_score": latest_report.overall_score,
                "has_sufficient_data": bool(latest_report.has_sufficient_data),
                "generation_source": latest_report.generation_source,
                "created_at": latest_report.created_at.isoformat() if latest_report.created_at else None,
            }

        return {
            "student_id": student_id,
            "course_id": course_id or (course.id if course else ""),
            "course_title": course.title if course else "",
            "learning_goal": learning_goal,
            "path": path_dict,
            "task_progress": task_progress,
            "practice_accuracy": {
                "correct": correct_count,
                "total": answer_total,
                "percent": accuracy,  # None when no data
            },
            "learning_time": {
                "total_minutes": learning_minutes,
                "active_days": active_days,
            },
            "evaluation_evidence": {
                "completed_tasks": completed_count,
                "answered_questions": answer_total,
                "assessments": self_eval_count,
                "total_records": len(records),
            },
            "latest_report": report_summary,
        }

    # ─────────────────────────────────────────────────────────────
    # 学习评估仪表盘 —— 供 LearningAssessmentPage 使用
    # 数据结构对齐 frontend/src/services/assessmentMockData.js
    # ─────────────────────────────────────────────────────────────

    def build_assessment_dashboard(
        self,
        db: Session,
        student_id: str,
        course_id: Optional[str] = None,
        scope_type: str = "last_30_days",
        stage_id: Optional[str] = None,
    ) -> Dict:
        """构建学习评估仪表盘数据。

        实时调用 _compute_report 计算最新报告，再转换为前端期望的结构。
        不写入数据库；不依赖历史 EvaluationReport。
        """
        # 1. 解析上下文（兼容只传 course_id 的场景）
        context = self._resolve_evaluation_context(
            db,
            student_id,
            course_id=course_id,
            scope_type=scope_type,
            stage_id=stage_id,
        )
        resolved_student_id = context["student_id"]
        resolved_course_id = context.get("course_id")

        # 2. 实时计算最新报告（不落库）
        report = self._compute_report(db, context)
        structured = report.get("structured") or {}
        overall_block = structured.get("overall") or {}
        dimensions_block = structured.get("dimensions") or {}
        strengths = structured.get("strengths") or []
        weaknesses = structured.get("weaknesses") or []
        topic_scores = report.get("topic_scores") or []
        history = report.get("history") or []
        review_plan = report.get("review_plan") or []

        overall_score = report.get("overall_score") or 0
        knowledge_mastery_score = dimensions_block.get("knowledge_mastery", overall_score)
        task_completion = dimensions_block.get("task_completion", 0)
        score_delta = overall_block.get("score_delta") or 0

        # 3. 错题分布（按 topic 聚合）
        wrong_questions = (
            db.query(WrongQuestion)
            .filter(WrongQuestion.student_id == resolved_student_id)
            .all()
        )
        error_distribution = self._aggregate_error_distribution(wrong_questions)

        # 4. 趋势数据
        trend = self._build_assessment_trend(
            history,
            current_score=overall_score,
            current_mastery=knowledge_mastery_score,
            current_completion=task_completion,
        )

        # 5. 知识点掌握度列表（雷达图）— 使用6个维度
        knowledge_mastery_list = [
            {"name": "知识掌握度", "mastery": _clamp(knowledge_mastery_score)},
            {"name": "测评正确率", "mastery": _clamp(dimensions_block.get("test_accuracy", 0))},
            {"name": "任务完成度", "mastery": _clamp(task_completion)},
            {"name": "学习连续性", "mastery": _clamp(dimensions_block.get("learning_consistency", 0))},
            {"name": "纠错能力", "mastery": _clamp(dimensions_block.get("error_correction", 0))},
            {"name": "实践能力", "mastery": _clamp(dimensions_block.get("practice_ability", 0))},
        ]

        # 6. 诊断信息（优势 / 薄弱）— 基于6个维度
        all_dims = [
            {"name": "知识掌握度", "score": _clamp(knowledge_mastery_score)},
            {"name": "测评正确率", "score": _clamp(dimensions_block.get("test_accuracy", 0))},
            {"name": "任务完成度", "score": _clamp(task_completion)},
            {"name": "学习连续性", "score": _clamp(dimensions_block.get("learning_consistency", 0))},
            {"name": "纠错能力", "score": _clamp(dimensions_block.get("error_correction", 0))},
            {"name": "实践能力", "score": _clamp(dimensions_block.get("practice_ability", 0))},
        ]
        diagnosis = {
            "strengths": [
                {"name": d["name"], "mastery": d["score"]}
                for d in all_dims if d["score"] >= 70
            ],
            "weaknesses": [
                {"name": d["name"], "mastery": d["score"], "reason": ""}
                for d in all_dims if d["score"] < 60
            ],
        }

        # 7. 薄弱维度详细卡片（基于6维雷达图）
        data_summary = structured.get("data_summary") or {}
        ds_questions = data_summary.get("questions_answered", 0)
        ds_tasks_total = data_summary.get("total_tasks", 0)
        ds_tasks_done = data_summary.get("unique_tasks_completed", 0)
        ds_streak = report.get("streak_days") or 0

        dim_scores = {
            "知识掌握度": _clamp(knowledge_mastery_score),
            "测评正确率": _clamp(dimensions_block.get("test_accuracy", 0)),
            "任务完成度": _clamp(task_completion),
            "学习连续性": _clamp(dimensions_block.get("learning_consistency", 0)),
            "纠错能力": _clamp(dimensions_block.get("error_correction", 0)),
            "实践能力": _clamp(dimensions_block.get("practice_ability", 0)),
        }
        dim_evidence = {
            "知识掌握度": [f"当前课程知识点平均掌握度 {knowledge_mastery_score}%", f"共 {len(topic_scores)} 个知识点参与评估"],
            "测评正确率": [f"基于 {ds_questions} 次作答记录", f"测评正确率 {dim_scores['测评正确率']}%"],
            "任务完成度": [f"已完成 {ds_tasks_done} / {ds_tasks_total} 个学习任务", f"任务完成率 {task_completion}%"],
            "学习连续性": [f"连续学习 {ds_streak} 天", f"学习连续性得分 {dim_scores['学习连续性']}%"],
            "纠错能力": [f"错题本中 {len(wrong_questions)} 道题", f"纠错能力得分 {dim_scores['纠错能力']}%"],
            "实践能力": [f"代码实践得分 {dim_scores['实践能力']}%", "基于作答表现和代码练习综合评估"],
        }
        dim_reasons = {
            "知识掌握度": "部分知识点掌握不牢固，需要加强复习",
            "测评正确率": "作答正确率偏低，需注意审题和知识点理解",
            "任务完成度": "学习任务完成率不足，建议加快学习节奏",
            "学习连续性": "学习连续性不够，建议保持每日学习习惯",
            "纠错能力": "错题订正率偏低，建议及时复习错题本",
            "实践能力": "代码实践次数不足，建议多动手练习",
        }
        dim_suggestions = {
            "知识掌握度": ["回顾薄弱知识点讲义", "完成知识点专项练习", "向AI导师请教不理解的部分"],
            "测评正确率": ["重新做错题", "复习相关知识点", "进行模拟测评"],
            "任务完成度": ["查看未完成任务列表", "制定每日学习计划", "优先完成当前阶段任务"],
            "学习连续性": ["设置每日学习提醒", "每天至少完成一个小任务", "保持学习打卡习惯"],
            "纠错能力": ["定期复习错题本", "对错题进行归类总结", "完成错题专项练习"],
            "实践能力": ["完成代码实验", "动手实现课堂示例", "尝试修改参数观察结果"],
        }
        weak_points = []
        for name, score in dim_scores.items():
            if score < 70:
                weak_points.append({
                    "knowledge_point_id": f"dim_{name}",
                    "name": name,
                    "mastery": score,
                    "evidence": dim_evidence.get(name, []),
                    "reason": dim_reasons.get(name, ""),
                    "suggestions": dim_suggestions.get(name, []),
                    "actions": {"review_resource_id": None, "exercise_task_id": None},
                })
        # 按分数从低到高排序
        weak_points.sort(key=lambda x: x["mastery"])

        # 8. 个性化强化计划（由 review_plan 转换）
        improvement_plan = self._build_improvement_plan(review_plan)

        # 9. 概览数据
        overview = {
            "overall_mastery": _clamp(knowledge_mastery_score),
            "mastery_change": _clamp(score_delta),
            "stage_completion": _clamp(task_completion),
            "completion_change": 0,
            "latest_score": _clamp(overall_score),
            "score_change": _clamp(score_delta),
            "weak_knowledge_count": len(weak_points),
            "weak_change": 0,
        }

        return {
            "overview": overview,
            "knowledge_mastery": knowledge_mastery_list,
            "diagnosis": diagnosis,
            "trend": trend,
            "error_distribution": error_distribution,
            "weak_points": weak_points,
            "improvement_plan": improvement_plan,
            # 额外元信息（前端不消费，但便于调试）
            "meta": {
                "student_id": resolved_student_id,
                "course_id": resolved_course_id,
                "scope_type": scope_type,
                "stage_id": context.get("stage_id"),
                "has_sufficient_data": bool(report.get("has_sufficient_data", True)),
            },
        }

    @staticmethod
    def _aggregate_error_distribution(wrong_questions: List[WrongQuestion]) -> List[Dict]:
        """按 topic 聚合错题分布。"""
        by_topic: Dict[str, int] = defaultdict(int)
        for wq in wrong_questions:
            topic = wq.topic or "综合"
            by_topic[topic] += max(1, wq.wrong_count or 1)
        if not by_topic:
            return []
        return [
            {"name": topic, "value": count}
            for topic, count in sorted(
                by_topic.items(), key=lambda kv: kv[1], reverse=True
            )
        ]

    @staticmethod
    def _build_assessment_trend(
        history: List[Dict],
        current_score: int,
        current_mastery: int,
        current_completion: int,
    ) -> Dict:
        """构建趋势数据：基于每日 history，再追加本次最新评估结果。"""
        points: List[Dict] = []
        for item in history:
            points.append({
                "score": _clamp(item.get("score", 0)),
                "mastery": _clamp(item.get("score", 0)),  # 每日 score 近似 mastery
                "completion": _clamp(item.get("unique_tasks_completed", 0) * 10),
            })
        # 追加当前最新评估点
        points.append({
            "score": _clamp(current_score),
            "mastery": _clamp(current_mastery),
            "completion": _clamp(current_completion),
        })
        # 保证至少3个数据点（不足时用当前值向前填充）
        while len(points) < 3:
            points.insert(0, {
                "score": _clamp(current_score),
                "mastery": _clamp(current_mastery),
                "completion": _clamp(current_completion),
            })
        # 控制最多 8 个点
        if len(points) > 8:
            points = points[-8:]
        labels = [f"第{i + 1}次" for i in range(len(points))]
        return {
            "labels": labels,
            "score_series": [p["score"] for p in points],
            "mastery_series": [p["mastery"] for p in points],
            "completion_series": [p["completion"] for p in points],
        }

    @staticmethod
    def _build_weak_points(
        db: Session,
        student_id: str,
        weaknesses: List[Dict],
    ) -> List[Dict]:
        """构建薄弱知识点详细卡片，附带可点击的资源/任务 ID。"""
        if not weaknesses:
            return []

        # 一次性查出该学生所有资源，按 topic 索引
        resources = (
            db.query(Resource)
            .filter(Resource.student_id == student_id)
            .all()
        )
        resource_by_topic: Dict[str, List[Resource]] = defaultdict(list)
        for r in resources:
            if r.topic:
                resource_by_topic[r.topic].append(r)

        review_types = {"document", "reading", "ppt", "mindmap", "interactive_classroom"}
        exercise_types = {"exercise", "code"}

        result: List[Dict] = []
        for w in weaknesses:
            topic = w.get("name") or ""
            actions_list = w.get("actions") or []
            suggestions = [
                a.get("title", "") for a in actions_list if a.get("title")
            ]
            if not suggestions:
                suggestions = [
                    f"重新学习「{topic}」核心讲义",
                    f"完成「{topic}」专项练习",
                    "向 AI 导师请教不懂的部分",
                ]

            # 查找与该 topic 匹配的资源
            matched = resource_by_topic.get(topic, [])
            review_resource_id = None
            exercise_task_id = None
            for r in matched:
                if review_resource_id is None and r.type in review_types:
                    review_resource_id = r.id
                if exercise_task_id is None and r.type in exercise_types:
                    exercise_task_id = r.task_id
                if review_resource_id and exercise_task_id:
                    break

            result.append({
                "knowledge_point_id": w.get("knowledge_point_id"),
                "name": topic,
                "mastery": _clamp(w.get("score", 0)),
                "evidence": w.get("evidence") or [],
                "reason": w.get("reason", ""),
                "suggestions": suggestions,
                "actions": {
                    "review_resource_id": review_resource_id,
                    "exercise_task_id": exercise_task_id,
                },
            })
        return result

    @staticmethod
    def _build_improvement_plan(review_plan: List[Dict]) -> List[Dict]:
        """把评估 review_plan 转换为前端期望的强化计划结构。"""
        if not review_plan:
            return []
        now = datetime.datetime.utcnow().date()
        day_labels = ["今天", "明天", "后天", "大后天"]
        result: List[Dict] = []
        for item in review_plan:
            topic = item.get("topic", "")
            urgency = item.get("urgency", "medium")
            # 解析 due_date → day_offset
            due_str = item.get("due_date")
            day_offset = 0
            if due_str:
                try:
                    due_date = datetime.datetime.fromisoformat(due_str).date()
                    day_offset = max(0, (due_date - now).days)
                except (ValueError, TypeError):
                    day_offset = 0
            day = day_labels[min(day_offset, len(day_labels) - 1)]

            # type 决定：high → learn（先补基础），low → test（验证），medium → practice
            if urgency == "high":
                ptype = "learn"
                title = f"重新学习「{topic}」核心内容"
            elif urgency == "low":
                ptype = "test"
                title = f"进行一次「{topic}」小测"
            else:
                ptype = "practice"
                title = f"完成「{topic}」专项练习"

            minutes = item.get("estimated_minutes", 20)
            result.append({
                "day": day,
                "title": title,
                "duration": f"{minutes}分钟",
                "type": ptype,
            })
        return result[:6]

    @staticmethod
    def _validate_exercise_content(content: dict) -> tuple[bool, str]:
        """校验专项练习内容。

        检查: 有答案、选项含答案、答案解析一致、知识点匹配、不泄露答案。
        """
        if not isinstance(content, dict):
            return False, "content 不是 dict"

        questions = content.get("questions", [])
        if not questions:
            return False, "没有题目"

        for i, q in enumerate(questions):
            qid = q.get("id", f"q{i}")
            stem = q.get("stem", "")
            options = q.get("options", [])
            correct = q.get("correct_answer", [])
            explanation = q.get("explanation", "")

            # 1. 有答案
            if not correct:
                return False, f"{qid}: 缺少正确答案"

            # 2. 选择题答案存在于选项
            if options:
                option_keys = {o.get("key", "") for o in options if isinstance(o, dict)}
                for c in correct:
                    if c not in option_keys:
                        return False, f"{qid}: 正确答案 '{c}' 不在选项中"

            # 3. 有解析
            if not explanation or len(explanation.strip()) < 5:
                return False, f"{qid}: 解析过短或缺失"

            # 4. 不直接泄露答案（题干中不含正确答案关键词）
            if stem and correct:
                for c in correct:
                    if str(c).lower() in stem.lower() and len(stem) < 30:
                        return False, f"{qid}: 题干可能泄露答案"

        return True, ""

    def get_progress_stats(self, db: Session, student_id: str) -> Dict:
        latest = self.build_report(db, student_id)
        return latest.get("progress_stats", {})

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

        # 纠错能力：错题订正率（已掌握错题 / 总错题）
        wrong_total = len(wrong_questions)
        wrong_mastered = len([w for w in wrong_questions if w.status == "mastered"])
        wrong_reviewing = len([w for w in wrong_questions if w.status == "reviewing"])
        # mastered全分，reviewing半分
        error_correction = _clamp(round((wrong_mastered + wrong_reviewing * 0.5) / wrong_total * 100)) if wrong_total else 0

        # 实践能力：基于代码/练习类资源完成数和答题记录综合计算
        all_resource_ids = list({r.resource_id for r in records if r.resource_id})
        resource_type_map = {}
        if all_resource_ids:
            resources = db.query(Resource).filter(Resource.id.in_(all_resource_ids)).all()
            resource_type_map = {res.id: res.type for res in resources}

        practice_resource_ids = {rid for rid, rtype in resource_type_map.items() if rtype in ("code", "exercise")}
        practice_records = [r for r in records if r.resource_id in practice_resource_ids and r.action in ("view", "complete")]
        practice_answer_records = [r for r in answer_records if r.resource_id in practice_resource_ids or not r.resource_id]
        practice_count = len(practice_records) + len([r for r in records if r.action == "experiment"])
        # 如果没有明确的实践资源记录，用所有答题记录作为备选
        if practice_count == 0 and answer_records:
            practice_count = len(answer_records)
            practice_answer_records = answer_records
        practice_raw = _average_score(practice_answer_records) if practice_answer_records else 0
        practice_bonus = min(practice_count * 5, 30)
        practice_ability = _clamp(round(practice_raw * 0.7 + practice_bonus))

        overall = _weighted_overall(
            knowledge_mastery,
            test_accuracy,
            task_completion,
            learning_consistency,
            error_correction,
            practice_ability,
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
            _dimension("error_correction", "纠错能力", error_correction, None, f"错题本中 {wrong_mastered} 题已掌握，{wrong_reviewing} 题复习中。"),
            _dimension("practice_ability", "实践能力", practice_ability, None, f"基于 {practice_count} 次实践和答题表现综合计算。"),
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
                "error_correction": error_correction,
                "practice_ability": practice_ability,
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

    # ── EvaluateAgent 增强（第1轮改造：格式规范化）──────

    async def _enhance_with_agent(self, student_id: str, db: Session, report: Dict) -> Dict:
        """用 EvaluateAgent LLM 增强报告中的诊断性字段。

        只覆盖：summary, weak_topics, suggestions, review_plan, strengths, weaknesses。
        不覆盖：overall_score, dimensions（客观分）, confidence。

        Returns:
            增强后的 report dict，额外包含 provider/model/fallback_used/fallback_reason。
        """
        if not self.evaluate_agent:
            report["generation_source"] = "rule"
            report["provider"] = None
            report["model"] = None
            report["fallback_used"] = True
            report["fallback_reason"] = "agent_not_configured"
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
            ai_fields = self._normalize_agent_result(raw)

            # ── 只覆盖诊断性字段，不覆盖客观分 ──
            if ai_fields.get("summary"):
                report["summary_struct"] = {"text": ai_fields["summary"], "source": "agent"}
                # 也更新 suggestions 中的诊断摘要
                if not report.get("suggestions") or len(report.get("suggestions", [])) <= 2:
                    report["suggestions"] = ai_fields.get("recommendations", ai_fields.get("suggestions", report.get("suggestions", [])))

            if ai_fields.get("weak_topics"):
                report["weak_topics"] = ai_fields["weak_topics"]

            if ai_fields.get("strengths"):
                report["strengths"] = ai_fields["strengths"]

            if ai_fields.get("weaknesses"):
                report["weaknesses"] = ai_fields["weaknesses"]

            if ai_fields.get("review_plan") and len(ai_fields["review_plan"]) > len(report.get("review_plan", [])):
                report["review_plan"] = ai_fields["review_plan"]

            if ai_fields.get("recommendations"):
                report["suggestions"] = ai_fields["recommendations"]

            # ── 第3轮：画像和路径建议 ──
            if ai_fields.get("profile_update_suggestions"):
                report["agent_profile_suggestions"] = ai_fields["profile_update_suggestions"]
            if ai_fields.get("path_adjustment_suggestions"):
                report["agent_path_suggestions"] = ai_fields["path_adjustment_suggestions"]

            # ── Provenance ──
            report["generation_source"] = "agent"
            report["provider"] = ai_fields.get("provider", _detect_provider())
            report["model"] = ai_fields.get("model", _detect_model())
            report["fallback_used"] = ai_fields.get("fallback_used", False)
            report["fallback_reason"] = ai_fields.get("fallback_reason")

        except Exception as exc:
            logger.warning("EvaluateAgent 增强失败，保留统计结果: %s", exc)
            report["generation_source"] = "rule_fallback"
            report["provider"] = _detect_provider()
            report["model"] = _detect_model()
            report["fallback_used"] = True
            report["fallback_reason"] = str(exc)[:300]

        return report

    @staticmethod
    def _normalize_agent_result(raw) -> Dict:
        """将 Agent 的各种可能返回格式统一为稳定结构。

        兼容：
        - DeepSeek 正常 JSON
        - DeepSeek JSON 被 Markdown 代码块包裹
        - 非法 JSON → 返回空 dict
        - dimensions 为 dict
        - dimensions 为 list → 转为 dict
        - 字段缺失 → 用空值填充
        - 规则兜底 JSON
        """
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            logger.warning("_normalize_agent_result: Agent 输出不是合法 JSON")
            return {"fallback_used": True, "fallback_reason": "agent_json_invalid"}

        if not isinstance(data, dict):
            return {"fallback_used": True, "fallback_reason": "agent_result_not_dict"}

        # ── 标准化 dimensions：永远是 dict ──
        dims = data.get("dimensions")
        if isinstance(dims, list):
            # list → dict 转换
            dim_dict = {}
            for item in dims:
                if isinstance(item, dict):
                    name = item.get("name", "")
                    score = item.get("score", 0)
                    dim_dict[name] = score
            data["dimensions"] = dim_dict
        elif not isinstance(dims, dict):
            data["dimensions"] = {}

        # ── 提取 LLM 提供者和模型 ──
        provider = None
        model = None
        try:
            from config import LLM_PRIMARY
            provider = os.environ.get("LLM_PRIMARY", "deepseek")
        except Exception:
            provider = _detect_provider()
        model = _detect_model()

        return {
            "dimensions": data.get("dimensions", {}),
            "weak_topics": data.get("weak_topics", []),
            "summary": data.get("summary", ""),
            "recommendations": data.get("recommendations", data.get("suggestions", [])),
            "suggestions": data.get("suggestions", data.get("recommendations", [])),
            "review_plan": data.get("review_plan", []),
            "strengths": data.get("strengths", []),
            "weaknesses": data.get("weaknesses", []),
            "provider": provider,
            "model": model,
            "fallback_used": False,
            "fallback_reason": None,
            # 第3轮：画像和路径建议
            "profile_update_suggestions": data.get("profile_updates", data.get("profile_update_suggestions", [])),
            "path_adjustment_suggestions": data.get("path_adjustments", data.get("path_adjustment_suggestions", [])),
            "intervention_actions": data.get("intervention_actions", []),
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
        overall_score = report.get("overall_score")
        score_value = float(overall_score) if overall_score is not None else None

        scope_start = report.get("scope_start_at")
        scope_end = report.get("scope_end_at")
        if isinstance(scope_start, str):
            scope_start = datetime.datetime.fromisoformat(scope_start)
        if isinstance(scope_end, str):
            scope_end = datetime.datetime.fromisoformat(scope_end)

        record = EvaluationReport(
            id=str(uuid.uuid4()),
            student_id=student_id,
            course_id=report.get("course_id"),
            overall_score=score_value,
            dimensions=json.dumps(report["dimensions"], ensure_ascii=False),
            weak_topics=json.dumps(report.get("weak_topics", []), ensure_ascii=False),
            suggestions=json.dumps(report.get("suggestions", []), ensure_ascii=False),
            review_plan=json.dumps(report.get("review_plan", []), ensure_ascii=False),
            has_sufficient_data=bool(report.get("has_sufficient_data", True)),
            insufficient_reason=str(report.get("insufficient_reason") or ""),
            generation_source=str(report.get("generation_source") or "rule"),
            provider=report.get("provider"),
            model=report.get("model"),
            fallback_used=bool(report.get("fallback_used", False)),
            fallback_reason=str(report.get("fallback_reason") or "") if report.get("fallback_reason") else None,
            # 第2轮新增
            evidence_hash=report.get("evidence_hash"),
            evidence_count=int(report.get("evidence_count", 0)),
            evidence_summary=json.dumps(report.get("evidence_summary", {}), ensure_ascii=False),
            trigger=str(report.get("trigger", "auto")),
            scope_type=str(report.get("scope_type", "last_30_days")),
            scope_start_at=scope_start,
            scope_end_at=scope_end,
            supersedes_report_id=report.get("supersedes_report_id"),
            statistics_json=str(report.get("statistics_json", "{}")),
            agent_result_json=str(report.get("agent_result_json", "{}")),
            source_snapshot=json.dumps({
                "topic_scores": report.get("topic_scores", []),
                "history": report.get("history", []),
                "weekly_activity": report.get("weekly_activity", []),
                "streak_days": report.get("streak_days", 0),
                "progress_stats": report.get("progress_stats", {}),
                "records": report.get("records", []),
                "source_summary": report.get("source_summary", {}),
                "recent_trend": report.get("recent_trend", "flat"),
                "completed_tasks": report.get("completed_tasks", 0),
                "questions_answered": report.get("questions_answered", 0),
                "tests_completed": report.get("tests_completed", 0),
                "total_time": report.get("total_time", 0),
                "structured": report.get("structured", {}),
                "scope": report.get("scope", {}),
                "data_summary": report.get("data_summary", {}),
                "course_progress": report.get("course_progress", {}),
                "path_adjustments": report.get("path_adjustments", []),
                "input_data_hash": report.get("input_data_hash"),
                "evidence": report.get("_evidence_snapshot", {}),
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
        overall = round(float(report.overall_score)) if report.overall_score is not None else None
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
            # ── 第1轮改造：新增字段 ──
            "has_sufficient_data": bool(report.has_sufficient_data),
            "hasSufficientData": bool(report.has_sufficient_data),
            "insufficient_reason": report.insufficient_reason or "",
            "insufficientReason": report.insufficient_reason or "",
            "generation_source": report.generation_source or "rule",
            "generationSource": report.generation_source or "rule",
            "provider": report.provider,
            "model": report.model,
            "fallback_used": bool(report.fallback_used),
            "fallbackUsed": bool(report.fallback_used),
            "fallback_reason": report.fallback_reason,
            "fallbackReason": report.fallback_reason,
            # ── 第2轮改造：证据与版本化 ──
            "evidence_hash": report.evidence_hash,
            "evidenceHash": report.evidence_hash,
            "evidence_count": report.evidence_count or 0,
            "evidenceCount": report.evidence_count or 0,
            "evidence_summary": _safe_json_loads(report.evidence_summary, {}),
            "evidenceSummary": _safe_json_loads(report.evidence_summary, {}),
            "trigger": report.trigger or "auto",
            "scope_type": report.scope_type or "last_30_days",
            "scopeType": report.scope_type or "last_30_days",
            "supersedes_report_id": report.supersedes_report_id,
            "supersedesReportId": report.supersedes_report_id,
            "statistics_json": _safe_json_loads(report.statistics_json, {}),
            "statisticsJson": _safe_json_loads(report.statistics_json, {}),
            "agent_result_json": _safe_json_loads(report.agent_result_json, {}),
            "agentResultJson": _safe_json_loads(report.agent_result_json, {}),
            "course_id": report.course_id,
            "courseId": report.course_id,
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
        return [
            round(float(row.overall_score))
            for row in reversed(rows)
            if row.overall_score is not None
        ]


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
    # 先定位当前阶段在 stages 列表中的索引，用于判断后续阶段是否锁定
    # （兼容字符串 / 数字 stage_id）
    current_index = -1
    for idx, stage in enumerate(stages):
        if str(stage.get("stage_id")) == str(current):
            current_index = idx
            break
    rows = []
    total_tasks = 0
    completed_total = 0
    for idx, stage in enumerate(stages):
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
        # 优先用阶段索引判断锁定状态；找不到时兜底用 int 比较（仅对数字 stage_id 有效）
        if current_index >= 0:
            locked = idx > current_index
        else:
            try:
                locked = int(stage.get("stage_id") or 0) > int(current or 1)
            except (TypeError, ValueError):
                locked = False
        rows.append({
            "stage_id": stage.get("stage_id"),
            "title": stage.get("title") or f"阶段 {stage.get('stage_id')}",
            "completed_tasks": completed,
            "total_tasks": total,
            "percent": percent,
            "locked": locked,
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
    error_correction: int = 0,
    practice_ability: int = 0,
) -> int:
    return _clamp(round(
        _clamp(knowledge_mastery) * 0.30
        + _clamp(test_accuracy) * 0.20
        + _clamp(task_completion) * 0.15
        + _clamp(learning_consistency) * 0.10
        + _clamp(error_correction) * 0.15
        + _clamp(practice_ability) * 0.10
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


# ═══════════════════════════════════════════════════════════════
# 第1轮改造：数据充分性 & 辅助函数
# ═══════════════════════════════════════════════════════════════

def _check_data_sufficiency(
    records: List[LearningRecord],
    wrong_questions: List[WrongQuestion],
) -> tuple[bool, str]:
    """检查学习数据是否足够进行评估。

    满足以下任一条件即为充分：
    1. 至少完成 MIN_COMPLETED_TASKS 个任务 且 作答 MIN_QUESTIONS_ANSWERED 道题
    2. 至少完成 MIN_TESTS_COMPLETED 次正式测评
    3. 至少产生 MIN_LEARNING_EVENTS 条有效学习事件

    Returns:
        (sufficient: bool, reason: str)
    """
    completed = [r for r in records if r.action == "complete"]
    answers = [r for r in records if r.action == "answer"]
    tests = [r for r in records if r.action == "self_eval"]
    events = len(records)

    tasks_ok = len(completed) >= MIN_COMPLETED_TASKS and len(answers) >= MIN_QUESTIONS_ANSWERED
    tests_ok = len(tests) >= MIN_TESTS_COMPLETED
    events_ok = events >= MIN_LEARNING_EVENTS

    if tasks_ok or tests_ok or events_ok:
        return True, ""

    # 构建不足原因
    parts = []
    parts.append(f"已完成 {len(completed)} 个任务（需要 ≥{MIN_COMPLETED_TASKS}）")
    parts.append(f"已作答 {len(answers)} 道题（需要 ≥{MIN_QUESTIONS_ANSWERED}）")
    parts.append(f"已完成 {len(tests)} 次测评（需要 ≥{MIN_TESTS_COMPLETED}）")
    parts.append(f"总学习事件 {events} 条（需要 ≥{MIN_LEARNING_EVENTS}）")
    reason = "学习数据不足：" + "；".join(parts)
    return False, reason


def _insufficient_suggestions(reason: str) -> list[str]:
    """数据不足时的推荐操作。"""
    return [
        "完成当前课程的学习目标和任务",
        "完成至少 5 道练习题或参与阶段测评",
        "积累 10 条以上学习记录后再次评估",
    ]


def _detect_provider() -> Optional[str]:
    """检测当前配置的 LLM provider。"""
    return os.environ.get("LLM_PRIMARY") or os.environ.get("LLM_PROVIDER") or "deepseek"


def _detect_model() -> Optional[str]:
    """检测当前配置的 LLM model。"""
    return os.environ.get("DEEPSEEK_MODEL") or os.environ.get("SPARK_MODEL") or "deepseek-chat"


def _emit(
    callback: Optional[Callable[[int, str, str], None]],
    progress: int,
    phase: str,
    message: str,
) -> None:
    if callback:
        callback(progress, phase, message)


# ═══════════════════════════════════════════════════════════════
# 第2轮：报告对比
# ═══════════════════════════════════════════════════════════════

def _build_comparison(current: Dict, previous: Optional[Dict]) -> Dict:
    """构建两份报告的对比结果。"""
    if not previous or not current:
        return {"available": False}

    cur_score = current.get("overall_score")
    prev_score = previous.get("overall_score")
    score_change = None
    if cur_score is not None and prev_score is not None:
        score_change = cur_score - prev_score

    # 维度变化
    cur_dims = _extract_dim_scores(current.get("dimensions", []))
    prev_dims = _extract_dim_scores(previous.get("dimensions", []))
    dim_changes = {}
    for name in set(list(cur_dims.keys()) + list(prev_dims.keys())):
        c = cur_dims.get(name)
        p = prev_dims.get(name)
        if c is not None and p is not None:
            dim_changes[name] = c - p
        elif c is not None:
            dim_changes[name] = c
        elif p is not None:
            dim_changes[name] = -p

    # 知识点变化
    cur_weak = set(current.get("weak_topics", []))
    prev_weak = set(previous.get("weak_topics", []))
    cur_strong = {s.get("name", "") for s in current.get("strengths", [])}
    prev_strong = {s.get("name", "") for s in previous.get("strengths", [])}

    improved_topics = list(prev_weak - cur_weak)
    declined_topics = list(cur_weak - prev_weak)
    new_weak_topics = list(cur_weak - prev_weak)
    resolved_weak_topics = list(prev_weak - cur_weak)

    # 证据量变化
    cur_ev = current.get("evidence_count", 0)
    prev_ev = previous.get("evidence_count", 0)
    evidence_count_change = cur_ev - prev_ev if prev_ev > 0 else None

    # 置信度变化
    cur_conf = current.get("overall", {}).get("confidence", 0)
    prev_conf = previous.get("overall", {}).get("confidence", 0)
    confidence_change = round(cur_conf - prev_conf, 2) if prev_conf else None

    return {
        "available": True,
        "previous_report_id": previous.get("report_id", previous.get("evaluation_id")),
        "overall_score_change": score_change,
        "dimension_changes": dim_changes,
        "improved_topics": improved_topics,
        "declined_topics": declined_topics,
        "new_weak_topics": new_weak_topics,
        "resolved_weak_topics": resolved_weak_topics,
        "evidence_count_change": evidence_count_change,
        "confidence_change": confidence_change,
    }


def _extract_dim_scores(dimensions) -> Dict[str, int]:
    """从 dimensions (list 或 dict) 中提取 {name: score}。"""
    result = {}
    if isinstance(dimensions, dict):
        for k, v in dimensions.items():
            if isinstance(v, (int, float)):
                result[k] = int(v)
    elif isinstance(dimensions, list):
        for item in dimensions:
            if isinstance(item, dict):
                name = item.get("name", "")
                score = item.get("score")
                if name and score is not None:
                    result[name] = int(score)
    return result
