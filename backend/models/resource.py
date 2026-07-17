"""学习资源表"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from . import Base
import datetime


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    path_id = Column(String(36), ForeignKey("learning_paths.id"))
    # 稳定关联到路径中的具体阶段，避免仅靠 topic 模糊匹配造成串关。
    stage_id = Column(Integer)

    type = Column(String(30), nullable=False)    # document|mindmap|exercise|code|reading|ppt
    title = Column(String(200), nullable=False)
    content = Column(Text)
    topic = Column(String(100))
    difficulty = Column(String(20))
    is_review = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
