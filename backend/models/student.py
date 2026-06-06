"""学生 & 画像表"""
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()


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
    version = Column(Float, default=1)

    knowledge_level = Column(Text)
    learning_goal = Column(Text)
    learning_history = Column(Text)    # JSON
    cognitive_style = Column(Text)
    weakness = Column(Text)            # JSON
    interest = Column(Text)            # JSON
    chat_history = Column(Text)        # JSON
    memory_strength = Column(Text)     # JSON, 创新点：遗忘曲线
    completeness = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
