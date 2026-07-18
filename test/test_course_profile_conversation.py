import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agents.schemas import CourseProfile, KnowledgeFoundation, ProfileOutput, WeakPoint
from agents.profile_agent import ProfileAgent
from models import Base
from models.auth import Course, User
from models.student import Student
from services.course_profile_conversation_service import (
    CourseProfileConversationService,
    build_profile_state,
)


class FakeUser:
    id = "user-01"


class FakeProfileService:
    def __init__(self):
        self.saved = None

    def get_profile(self, db, student_id):
        return self.saved

    def save_profile(self, db, student_id, profile_data, increment_version=True):
        self.saved = profile_data
        return profile_data


class FakeProfileAgent:
    def __init__(self):
        self.calls = 0
        self.llm = type("FakeLLM", (), {
            "primary": "deepseek",
            "last_usage": type("Usage", (), {
                "provider": "deepseek",
                "model": "deepseek-chat",
            })(),
        })()

    async def build_profile_v2(self, *, context, message, history, current_profile):
        self.calls += 1
        return ProfileOutput(
            profile=CourseProfile(
                user_id=context.user_id,
                course_id=context.course_id,
                knowledge_foundation=KnowledgeFoundation(
                    python=86,
                    linear_algebra=42,
                    calculus=45,
                    machine_learning=50,
                    deep_learning=40,
                ),
                learning_goal="六周内完成猫狗图像分类项目",
                learning_history=["软件工程专业背景", "具备 Python 编程经验"],
                cognitive_style="案例驱动 + 实践驱动",
                preferred_resources=["mindmap", "document", "code"],
                assessment_preference="项目式评估",
                weak_points=[
                    WeakPoint(knowledge_point_id="python", name="Python", score=55),
                    WeakPoint(knowledge_point_id="linear_algebra", name="线性代数", score=42),
                ],
                interest_directions=["计算机视觉"],
                weekly_available_hours=5,
                target_duration_weeks=6,
            ),
            profile_patch={"learning_goal": "六周内完成猫狗图像分类项目"},
            completeness=0.9,
            confidence=0.88,
            missing_dimensions=[],
            next_questions=[],
            assistant_reply="我已经提炼出你的学习目标、基础和偏好，可以确认画像。",
            can_start_journey=True,
            sources=["dialogue"],
        )

    @staticmethod
    def _normalize_profile_output(context, result, current_profile=None):
        return ProfileAgent._normalize_profile_output(context, result, current_profile)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(User(id="user-01", username="student", password_hash="hash"))
    db.add(Student(id="student-01", nickname="测试学生"))
    db.add(Course(id="course-01", user_id="user-01", student_id="student-01", title="测试课程"))
    db.commit()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.asyncio
async def test_profile_message_idempotency_prevents_duplicate_agent_calls(db_session):
    agent = FakeProfileAgent()
    service = CourseProfileConversationService(agent, FakeProfileService())

    first = await service.process_message(
        db_session,
        user=FakeUser(),
        course_id="course-01",
        conversation_id="conv-01",
        client_message_id="client-01",
        message="我 Python 基础较好，但线性代数薄弱。",
    )
    second = await service.process_message(
        db_session,
        user=FakeUser(),
        course_id="course-01",
        conversation_id="conv-01",
        client_message_id="client-01",
        message="我 Python 基础较好，但线性代数薄弱。",
    )

    assert agent.calls == 1
    assert second.message_id == first.message_id
    assert second.agent_run.provider == "deepseek"
    assert "Python" not in str(second.profile.get("weak_points"))


def test_can_confirm_requires_required_dimensions_even_when_completeness_is_high():
    course = Course(id="course-01", user_id="user-01", student_id="student-01", title="测试课程")
    state = build_profile_state(course, {
        "learning_goal": "完成图像分类项目",
        "knowledge_foundation": {"python": 85, "linear_algebra": 50, "calculus": 50},
        "weak_points": ["线性代数"],
        "cognitive_style": "案例驱动",
        "preferred_resources": ["document", "code"],
        "weekly_available_hours": 5,
        "target_duration_weeks": 6,
        "completeness": 0.95,
    })

    assert state["can_confirm"] is False
    assert "测评偏好" in [item["label"] for item in state["missing_required_dimensions"]]
