"""学习记录与评估报告表。"""
import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text

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

    overall_score = Column(Float, nullable=False, default=0.0)
    dimensions = Column(Text, nullable=False, default="[]")
    weak_topics = Column(Text, nullable=False, default="[]")
    suggestions = Column(Text, nullable=False, default="[]")
    review_plan = Column(Text, nullable=False, default="[]")
    source_snapshot = Column(Text, nullable=False, default="{}")

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
