"""学习记录 & 评估表"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()


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
