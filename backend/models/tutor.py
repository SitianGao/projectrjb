"""Tutor 会话和消息持久化模型。"""

import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from . import Base


class TutorSession(Base):
    """辅导会话。"""
    __tablename__ = "tutor_sessions"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    title = Column(String(200), default="新的辅导会话")
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class TutorMessage(Base):
    """辅导对话消息。"""
    __tablename__ = "tutor_messages"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("tutor_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    references = Column(Text)  # JSON: RAG 引用
    explanation_style = Column(String(30))  # auto / analogy / formula / visual / story
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
