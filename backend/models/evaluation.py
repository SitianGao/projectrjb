"""学习记录与评估报告表。"""
import datetime

from sqlalchemy import Boolean, Column, String, Integer, Float, DateTime, ForeignKey, Text

from . import Base


class LearningRecord(Base):
    __tablename__ = "learning_records"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    resource_id = Column(String(36), ForeignKey("resources.id"))

    action = Column(String(30), nullable=False)  # view|complete|answer|ask
    topic = Column(String(100))
    score = Column(Float)
    time_spent = Column(Integer)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    course_id = Column(String(36), index=True)

    overall_score = Column(Float, nullable=True)   # NULL when insufficient data
    dimensions = Column(Text, nullable=False, default="[]")
    weak_topics = Column(Text, nullable=False, default="[]")
    suggestions = Column(Text, nullable=False, default="[]")
    review_plan = Column(Text, nullable=False, default="[]")
    source_snapshot = Column(Text, nullable=False, default="{}")

    # ── Data sufficiency ──
    has_sufficient_data = Column(Boolean, nullable=False, default=False)
    insufficient_reason = Column(Text, default="")

    # ── Provenance tracking ──
    generation_source = Column(String(30), default="rule")  # rule | agent | rule_fallback
    provider = Column(String(50))
    model = Column(String(100))
    fallback_used = Column(Boolean, nullable=False, default=False)
    fallback_reason = Column(Text)

    # ── 第2轮: 证据与版本化 ──
    evidence_hash = Column(String(64))
    evidence_count = Column(Integer, default=0)
    evidence_summary = Column(Text, default="{}")
    trigger = Column(String(20), default="auto")    # auto | manual | manual_force
    scope_type = Column(String(30), default="last_30_days")
    scope_start_at = Column(DateTime)
    scope_end_at = Column(DateTime)
    supersedes_report_id = Column(String(36))
    statistics_json = Column(Text, default="{}")
    agent_result_json = Column(Text, default="{}")

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )


class WrongQuestion(Base):
    """错题本表 —— 记录学生的错题及答案分析。"""
    __tablename__ = "wrong_questions"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    resource_id = Column(String(36), ForeignKey("resources.id"))
    question_id = Column(String(36), nullable=False)
    topic = Column(String(200))
    question = Column(Text)
    question_text = Column(Text)
    options = Column(Text, default="[]")
    user_answer = Column(Text)
    correct_answer = Column(Text)
    explanation = Column(Text)
    difficulty = Column(String(20))
    tags = Column(Text, default="[]")
    wrong_count = Column(Integer, default=1)
    correct_streak = Column(Integer, default=0)
    status = Column(String(20), default="unmastered")
    last_wrong_at = Column(DateTime, default=datetime.datetime.utcnow)
    next_review_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PathAdjustmentLog(Base):
    """路径调整记录 —— 追踪每次评估触发的路径变更。"""
    __tablename__ = "path_adjustment_logs"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True)
    course_id = Column(String(36), index=True)
    learning_path_id = Column(String(36))
    source_evaluation_id = Column(String(36), index=True)
    adjustment_key = Column(String(128))
    action = Column(String(50), nullable=False)
    knowledge_point = Column(String(200))
    target_stage_id = Column(String(64))
    target_task_id = Column(String(100))
    suggested_resource_type = Column(String(30))
    before_state = Column(Text, default="{}")
    after_state = Column(Text, default="{}")
    reason = Column(Text)
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="suggested")
    applied_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ProfileUpdateLog(Base):
    """画像更新记录 —— 追踪每次评估触发的画像变更。"""
    __tablename__ = "profile_update_logs"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True)
    course_id = Column(String(36), index=True)
    student_id = Column(String(36), nullable=False, index=True)
    source_evaluation_id = Column(String(36), index=True)
    field = Column(String(50), nullable=False)
    before_value = Column(Text)
    after_value = Column(Text)
    reason = Column(Text)
    confidence = Column(Float, default=0.0)
    evidence_refs = Column(Text, default="[]")
    status = Column(String(20), default="suggested")
    applied_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
