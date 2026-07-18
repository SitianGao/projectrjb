"""互动课堂模型。"""

import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, UniqueConstraint

from . import Base


class InteractiveClassroom(Base):
    __tablename__ = "interactive_classrooms"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    course_id = Column(String(64), nullable=False, index=True)
    student_id = Column(String(36), nullable=False, index=True)
    stage_id = Column(String(64), nullable=False, index=True)
    task_id = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(36), nullable=True)
    title = Column(String(200), nullable=False)
    topic = Column(String(120), nullable=False)
    difficulty = Column(String(30), default="medium")
    status = Column(String(30), default="completed")
    version = Column(Integer, default=1)
    estimated_minutes = Column(Integer, default=25)
    learning_goal_ids = Column(Text, default="[]")
    knowledge_point_ids = Column(Text, default="[]")
    generation_brief = Column(Text, default="{}")
    scenes = Column(Text, default="[]")
    validation_status = Column(String(30), default="validated")
    source_ids = Column(Text, default="[]")
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ClassroomSession(Base):
    __tablename__ = "classroom_sessions"
    __table_args__ = (
        UniqueConstraint("classroom_id", "user_id", "task_id", name="uq_classroom_user_task"),
    )

    id = Column(String(64), primary_key=True)
    classroom_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    course_id = Column(String(64), nullable=False, index=True)
    student_id = Column(String(36), nullable=False, index=True)
    stage_id = Column(String(64), nullable=False)
    task_id = Column(String(100), nullable=False)
    status = Column(String(30), default="in_progress")
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime)
    actual_learning_minutes = Column(Integer, default=0)
    completed_scene_count = Column(Integer, default=0)
    total_scene_count = Column(Integer, default=0)
    viewed_slide_count = Column(Integer, default=0)
    whiteboard_interaction_count = Column(Integer, default=0)
    simulation_interaction_count = Column(Integer, default=0)
    discussion_interaction_count = Column(Integer, default=0)
    tutor_question_count = Column(Integer, default=0)
    quiz_score = Column(Float, default=0.0)
    quiz_accuracy = Column(Float, default=0.0)
    evidence = Column(Text, default="{}")
    tutor_summary = Column(Text, default="")
    evaluation_result = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ClassroomSceneProgress(Base):
    __tablename__ = "classroom_scene_progress"
    __table_args__ = (
        UniqueConstraint("session_id", "scene_id", name="uq_classroom_session_scene"),
    )

    id = Column(String(64), primary_key=True)
    session_id = Column(String(64), nullable=False, index=True)
    classroom_id = Column(String(64), nullable=False, index=True)
    scene_id = Column(String(100), nullable=False)
    status = Column(String(30), default="not_started")
    progress = Column(Float, default=0.0)
    interactions = Column(Text, default="[]")
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ClassroomQuizAttempt(Base):
    __tablename__ = "classroom_quiz_attempts"

    id = Column(String(64), primary_key=True)
    session_id = Column(String(64), nullable=False, index=True)
    classroom_id = Column(String(64), nullable=False, index=True)
    scene_id = Column(String(100), nullable=False)
    question_id = Column(String(100), nullable=False)
    user_answer = Column(Text)
    correct_answer = Column(Text)
    is_correct = Column(Integer, default=0)
    hint_level = Column(Integer, default=1)
    knowledge_point_ids = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
