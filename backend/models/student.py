"""学生 & 画像表"""
import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from . import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(String(36), primary_key=True)
    nickname = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    version = Column(Integer, default=1)

    knowledge_level = Column(Text)
    learning_goal = Column(Text)
    learning_history = Column(Text)    # JSON
    cognitive_style = Column(Text)
    pace_preference = Column(Text)     # 学习节奏偏好
    weakness = Column(Text)            # JSON
    interest = Column(Text)            # JSON
    chat_history = Column(Text)        # JSON
    memory_strength = Column(Text)     # JSON, 创新点：遗忘曲线
    completeness = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class CourseProfileConversationMessage(Base):
    __tablename__ = "course_profile_conversation_messages"
    __table_args__ = (
        UniqueConstraint("conversation_id", "client_message_id", name="uq_profile_conversation_client_message"),
    )

    id = Column(String(36), primary_key=True)
    conversation_id = Column(String(80), nullable=False, index=True)
    client_message_id = Column(String(80), nullable=False)
    user_id = Column(String(36), nullable=False, index=True)
    course_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    assistant_content = Column(Text)
    response_json = Column(Text)
    agent_run_json = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
