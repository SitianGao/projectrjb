"""
数据库模型层 —— SQLAlchemy ORM

所有表共享同一个 Base，确保外键关系正确解析。
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 延迟导入模型类，避免循环引用
from .student import Student, StudentProfile
from .learning_path import LearningPath
from .resource import Resource
from .evaluation import EvaluationReport, LearningRecord, WrongQuestion
from .auth import User, AuthToken, Course

__all__ = [
    "Base",
    "Student",
    "StudentProfile",
    "LearningPath",
    "Resource",
    "EvaluationReport",
    "LearningRecord",
    "WrongQuestion",
    "User",
    "AuthToken",
    "Course",
]
