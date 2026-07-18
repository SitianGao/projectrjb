"""学习路径、阶段、任务和 Agent 运行记录。"""

import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from . import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    course_id = Column(String(36), ForeignKey("courses.id"), index=True)
    version = Column(Integer, default=1)

    goal = Column(Text)
    stages = Column(Text)  # 兼容旧接口的只读 JSON 快照
    current_stage = Column(Integer, default=1)
    current_stage_id = Column(String(64))
    estimated_days = Column(Integer)
    status = Column(String(20), default="active")

    generation_source = Column(String(30), default="legacy")
    generated_by = Column(String(80))
    provider = Column(String(50))
    model = Column(String(100))
    agent_run_id = Column(String(64))
    profile_version = Column(Integer)
    fallback_used = Column(Boolean, default=False)
    fallback_type = Column(String(50))
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class LearningStage(Base):
    __tablename__ = "learning_stages"
    __table_args__ = (
        UniqueConstraint("path_id", "stage_id", name="uq_learning_stage_path_stage"),
    )

    id = Column(String(36), primary_key=True)
    path_id = Column(String(36), ForeignKey("learning_paths.id"), nullable=False, index=True)
    stage_id = Column(String(64), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    order = Column(Integer, nullable=False)
    status = Column(String(20), default="locked")
    learning_objectives = Column(Text, default="[]")
    knowledge_point_ids = Column(Text, default="[]")
    topics = Column(Text, default="[]")
    unlock_conditions = Column(Text, default="[]")
    resource_blueprint = Column(Text, default="[]")
    estimated_days = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class LearningTask(Base):
    __tablename__ = "learning_tasks"
    __table_args__ = (
        UniqueConstraint("path_id", "task_id", name="uq_learning_task_path_task"),
    )

    id = Column(String(36), primary_key=True)
    path_id = Column(String(36), ForeignKey("learning_paths.id"), nullable=False, index=True)
    stage_row_id = Column(String(36), ForeignKey("learning_stages.id"), nullable=False, index=True)
    stage_id = Column(String(64), nullable=False, index=True)
    task_id = Column(String(100), nullable=False, index=True)
    task_type = Column(String(40), nullable=False)
    title = Column(String(240), nullable=False)
    description = Column(Text)
    content = Column(Text)
    order = Column(Integer, nullable=False)
    estimated_minutes = Column(Integer, default=20)
    difficulty = Column(String(30), default="初级")
    status = Column(String(20), default="not_started")
    prerequisite_task_ids = Column(Text, default="[]")
    resource_id = Column(String(36), ForeignKey("resources.id"))
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(64), primary_key=True)
    agent_name = Column(String(80), nullable=False, index=True)
    user_id = Column(String(36), index=True)
    course_id = Column(String(36), index=True)
    stage_id = Column(String(64), index=True)
    task_id = Column(String(100), index=True)
    provider = Column(String(50))
    model = Column(String(100))
    request_id = Column(String(100))
    status = Column(String(20), nullable=False, default="started")
    duration_ms = Column(Integer, default=0)
    fallback_used = Column(Boolean, default=False)
    fallback_type = Column(String(50))
    fallback_reason = Column(Text)
    knowledge_hit_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime)
    error_code = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
