"""学习资源及用户资源状态表。"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from . import Base
import datetime


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (
        Index(
            "ix_resources_context_lookup",
            "student_id",
            "task_id",
            "type",
            "difficulty",
            "generation_version",
        ),
    )

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id"), index=True)
    path_id = Column(String(36), ForeignKey("learning_paths.id"))
    # 资源直接绑定任务，stage_id 仅用于阶段筛选和旧数据兼容。
    stage_id = Column(String(64))
    task_id = Column(String(100), index=True)
    parent_resource_id = Column(String(36), ForeignKey("resources.id"), index=True)

    type = Column(String(30), nullable=False)    # document|mindmap|exercise|code|reading|ppt|interactive_classroom
    title = Column(String(200), nullable=False)
    content = Column(Text)
    topic = Column(String(100))
    difficulty = Column(String(20))
    is_review = Column(Boolean, default=False)
    source_refs = Column(Text, default="[]")
    artifact_url = Column(String(500))
    mime_type = Column(String(100))
    trigger_source = Column(String(40), default="manual")
    trigger_context = Column(Text, default="{}")
    variant_type = Column(String(50))
    generation_version = Column(String(30), default="1")
    generation_status = Column(String(20), default="ready")
    generation_source = Column(String(30), default="agent")
    fallback_type = Column(String(50))
    idempotency_key = Column(String(64), index=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ResourceUserState(Base):
    __tablename__ = "resource_user_states"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "resource_id",
            name="uq_resource_user_state_user_resource",
        ),
    )

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    resource_id = Column(
        String(36),
        ForeignKey("resources.id"),
        nullable=False,
        index=True,
    )
    is_favorite = Column(Boolean, default=False, nullable=False)
    learning_status = Column(String(20), default="not_started", nullable=False)
    opened_count = Column(Integer, default=0, nullable=False)
    last_opened_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
