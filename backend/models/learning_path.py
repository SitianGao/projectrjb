"""学习路径表"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    version = Column(Integer, default=1)

    goal = Column(Text)
    stages = Column(Text)                  # JSON
    current_stage = Column(Integer, default=1)
    status = Column(String(20), default="active")

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
