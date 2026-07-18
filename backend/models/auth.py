"""真实用户、登录令牌与课程上下文模型。"""

import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from . import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(80), nullable=False, unique=True, index=True)
    password_hash = Column(String(300), nullable=False)
    name = Column(String(100))
    email = Column(String(200))
    phone = Column(String(30))
    bio = Column(Text)
    avatar = Column(String(500))
    active_course_id = Column(String(36))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    token_hash = Column(String(64), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Course(Base):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    # 每门课程拥有独立 student_id，复用现有画像/路径/资源外键并实现完整隔离。
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    goal = Column(Text)
    status = Column(String(30), default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
