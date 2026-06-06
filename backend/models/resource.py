"""学习资源表"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    path_id = Column(String(36), ForeignKey("learning_paths.id"))

    type = Column(String(30), nullable=False)    # document|mindmap|exercise|code|reading|ppt
    title = Column(String(200), nullable=False)
    content = Column(Text)
    topic = Column(String(100))
    difficulty = Column(String(20))
    is_review = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
