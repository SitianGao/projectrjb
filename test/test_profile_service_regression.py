"""队长负责范围：画像持久化与学习路径解锁规则回归测试。"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config import PROFILE_READY_THRESHOLD  # noqa: E402
from models import Base  # noqa: E402
from models.student import Student, StudentProfile  # noqa: E402
from services.planner_service import PlannerService  # noqa: E402
from services.profile_service import ProfileService  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _add_profile(db, student_id: str, version: int, completeness: float):
    db.add(
        StudentProfile(
            id=str(uuid.uuid4()),
            student_id=student_id,
            version=version,
            knowledge_level="软件工程入门",
            learning_goal="完成一个 Python 工具项目",
            cognitive_style="动手型",
            pace_preference="中速均衡型",
            weakness='["变量作用域"]',
            interest='["工具开发"]',
            completeness=completeness,
        )
    )


def _seed_regressed_profile(db, student_id: str = "profile-regression") -> str:
    db.add(Student(id=student_id, nickname="画像回归测试"))
    _add_profile(db, student_id, version=1, completeness=0.86)
    _add_profile(db, student_id, version=2, completeness=0.75)
    db.commit()
    return student_id


def test_get_profile_uses_historical_highest_completeness(db):
    student_id = _seed_regressed_profile(db)
    service = ProfileService(profile_agent=None, db_session_factory=None)

    profile = service.get_profile(db, student_id)

    assert profile["version"] == 2
    assert profile["completeness"] == pytest.approx(0.86)


def test_save_profile_never_drops_below_historical_highest(db):
    student_id = _seed_regressed_profile(db)
    service = ProfileService(profile_agent=None, db_session_factory=None)

    saved = service.save_profile(
        db,
        student_id,
        {
            "profile": {"learning_goal": "继续完成 Python 工具项目"},
            "completeness": 0.60,
        },
    )

    assert saved.version == 3
    assert saved.completeness == pytest.approx(0.86)


async def test_chat_stream_rewrites_lower_agent_score_to_historical_highest(db):
    student_id = _seed_regressed_profile(db)

    class LowerScoreAgent:
        async def chat(self, **kwargs):
            result = {
                "student_id": student_id,
                "profile": {"learning_goal": "完成一个 Python 工具项目"},
                "completeness": 0.60,
                "next_questions": ["你还希望重点练习什么？"],
            }
            yield f"data: {json.dumps({'type': 'profile_update', 'profile': result}, ensure_ascii=False)}\n\n"
            yield 'data: {"type":"done"}\n\n'

    service = ProfileService(LowerScoreAgent(), db_session_factory=None)
    events = [
        event
        async for event in service.chat_stream(
            db=db,
            student_id=student_id,
            message="继续",
        )
    ]

    update = next(
        json.loads(event.removeprefix("data:").strip())
        for event in events
        if '"profile_update"' in event
    )
    latest = (
        db.query(StudentProfile)
        .filter(StudentProfile.student_id == student_id)
        .order_by(StudentProfile.version.desc())
        .first()
    )
    assert update["profile"]["completeness"] == pytest.approx(0.86)
    assert latest.version == 3
    assert latest.completeness == pytest.approx(0.86)


async def test_planner_uses_shared_85_percent_threshold(db):
    assert PROFILE_READY_THRESHOLD == pytest.approx(0.85)

    class FixedProfileService:
        def __init__(self, completeness):
            self.completeness = completeness

        def get_profile(self, _db, student_id):
            return {
                "student_id": student_id,
                "learning_goal": "完成 Python 项目",
                "completeness": self.completeness,
            }

    below = PlannerService(None, None, FixedProfileService(0.84))
    events = [
        event
        async for event in below.generate_stream(db, "below-threshold")
    ]
    payloads = [
        json.loads(event.removeprefix("data:").strip())
        for event in events
    ]

    assert any(payload.get("type") == "error" for payload in payloads)
    assert any("85%" in payload.get("message", "") for payload in payloads)


async def test_historical_highest_completeness_unlocks_planner(db):
    student_id = _seed_regressed_profile(db, "planner-history-unlock")
    profile_service = ProfileService(profile_agent=None, db_session_factory=None)

    class FixedPlannerAgent:
        async def generate_plan(self, profile, goal_override):
            return {
                "goal": goal_override,
                "stages": [
                    {
                        "stage_id": 1,
                        "title": "Python 基础巩固",
                        "topics": ["变量作用域"],
                        "tasks": ["完成作用域练习"],
                    }
                ],
                "current_stage": 1,
                "estimated_days": 1,
            }

    planner = PlannerService(FixedPlannerAgent(), None, profile_service)
    result = await planner.build_path(db, student_id)

    assert result["student_id"] == student_id
    assert result["goal"] == "完成一个 Python 工具项目"
    assert len(result["stages"]) == 1
