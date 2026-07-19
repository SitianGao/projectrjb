"""课程学习会话模型。"""

import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from . import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=False, index=True)
    path_id = Column(String(36), ForeignKey("learning_paths.id"), nullable=False, index=True)
    stage_id = Column(String(64), nullable=True, index=True)
    task_id = Column(String(100), nullable=True, index=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
