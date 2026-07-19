"""学习路径真实性、课程隔离和任务进度回归测试。"""

from __future__ import annotations

import asyncio
import pathlib
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from agents.planner_agent import PlannerAgent  # noqa: E402
from api.response import ApiError  # noqa: E402
from core.agent_context import AgentContext  # noqa: E402
from models import Base  # noqa: E402
from models.auth import Course, User  # noqa: E402
from models.learning_path import LearningStage, LearningTask  # noqa: E402
from models.student import Student  # noqa: E402
from services.course_learning_service import CourseLearningService  # noqa: E402
from services.planner_service import PlannerService  # noqa: E402


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _seed_scope(db, *, user_id="demo_student", course_id="ai_deep_learning_demo"):
    student_id = f"{course_id}-student"
    user = User(
        id=user_id,
        username=user_id,
        password_hash="test-only",
        name="演示同学",
    )
    db.add(user)
    db.add(Student(id=student_id, nickname="演示同学"))
    db.add(Course(
        id=course_id,
        user_id=user_id,
        student_id=student_id,
        title="人工智能与深度学习",
        goal="完成图像分类项目",
    ))
    db.commit()
    return user, student_id


def _path_data():
    return {
        "goal": "完成图像分类项目",
        "current_stage": 1,
        "stages": [
            {
                "stage_id": "stage_basics",
                "order": 1,
                "title": "机器学习基础",
                "status": "active",
                "learning_objectives": ["理解监督学习"],
                "topics": ["监督学习"],
                "estimated_days": 2,
                "tasks": [
                    {
                        "task_id": "task_goal",
                        "task_type": "objective",
                        "title": "学习目标",
                        "estimated_minutes": 10,
                        "status": "active",
                    },
                    {
                        "task_id": "task_document",
                        "task_type": "document",
                        "title": "核心讲义",
                        "estimated_minutes": 30,
                        "status": "not_started",
                        "prerequisite_task_ids": ["task_goal"],
                    },
                ],
            }
        ],
    }


def test_path_is_transactionally_persisted_with_normalized_entities():
    db = _session()
    user, student_id = _seed_scope(db)
    planner = PlannerService(None, None, None)
    path = planner.save_path(
        db,
        student_id,
        _path_data(),
        user_id=user.id,
        course_id="ai_deep_learning_demo",
        generation_metadata={
            "generation_source": "agent",
            "generated_by": "PlannerAgent",
            "provider": "spark",
            "model": "4.0Ultra",
            "agent_run_id": "run_test",
            "profile_version": 3,
            "fallback_used": False,
        },
    )

    assert path.generation_source == "agent"
    assert db.query(LearningStage).filter_by(path_id=path.id).count() == 1
    assert db.query(LearningTask).filter_by(path_id=path.id).count() == 2


def test_task_completion_is_idempotent_and_survives_reload():
    db = _session()
    user, student_id = _seed_scope(db)
    planner = PlannerService(None, None, None)
    planner.save_path(
        db,
        student_id,
        _path_data(),
        user_id=user.id,
        course_id="ai_deep_learning_demo",
        generation_metadata={"generation_source": "seed"},
    )
    service = CourseLearningService(planner)

    first = service.complete_task(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
        task_id="task_goal",
    )
    second = service.complete_task(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
        task_id="task_goal",
    )
    reloaded = service.get_learning_context(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
        task_id="task_document",
    )

    assert first["idempotent"] is False
    assert second["idempotent"] is True
    assert reloaded["progress"] == {"completed": 1, "total": 2, "percent": 50}
    assert reloaded["current_task"]["type_label"] == "核心讲义"


def test_learning_state_separates_course_name_goal_and_completed_state():
    db = _session()
    user, student_id = _seed_scope(db)
    planner = PlannerService(None, None, None)
    path = planner.save_path(
        db,
        student_id,
        _path_data(),
        user_id=user.id,
        course_id="ai_deep_learning_demo",
        generation_metadata={"generation_source": "seed"},
    )
    for task in db.query(LearningTask).filter_by(path_id=path.id).all():
        task.status = "completed"
    for stage in db.query(LearningStage).filter_by(path_id=path.id).all():
        stage.status = "completed"
    path.status = "completed"
    db.commit()

    service = CourseLearningService(planner)
    state = service.resolve_active_learning_state(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
    )
    context = service.get_learning_context(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
    )

    assert state["course"]["course_name"] == "人工智能与深度学习"
    assert state["learning_goal"] == "完成图像分类项目"
    assert state["course"]["course_name"] != state["learning_goal"]
    assert state["progress"]["completed_tasks"] == 2
    assert state["progress"]["total_tasks"] == 2
    assert state["progress"]["percent"] == 100
    assert state["course_status"] == "completed"
    assert state["current_task"] is None
    assert state["next_task"] is None
    assert state["continue_target"]["route"] == "/course/ai_deep_learning_demo/path"
    assert context["course_status"] == "completed"
    assert context["current_task"] is None


def test_course_scope_blocks_another_user():
    db = _session()
    user, student_id = _seed_scope(db)
    planner = PlannerService(None, None, None)
    planner.save_path(
        db,
        student_id,
        _path_data(),
        user_id=user.id,
        course_id="ai_deep_learning_demo",
        generation_metadata={"generation_source": "seed"},
    )
    other = User(
        id="other_user",
        username="other_user",
        password_hash="test-only",
        name="其他用户",
    )
    db.add(other)
    db.commit()

    with pytest.raises(ApiError) as exc:
        CourseLearningService(planner).get_learning_context(
            db,
            user=other,
            course_id="ai_deep_learning_demo",
        )
    assert exc.value.status_code == 404

    db.add(Student(id="second-course-student", nickname="演示同学"))
    db.add(Course(
        id="second_course",
        user_id=user.id,
        student_id="second-course-student",
        title="自然语言处理",
        goal="完成文本分类项目",
    ))
    db.commit()
    with pytest.raises(ApiError) as switched:
        CourseLearningService(planner).get_learning_context(
            db,
            user=user,
            course_id="second_course",
        )
    assert switched.value.status_code == 404


def test_seed_and_internal_task_type_are_reported_truthfully():
    db = _session()
    user, student_id = _seed_scope(db)
    planner = PlannerService(None, None, None)
    planner.save_path(
        db,
        student_id,
        _path_data(),
        user_id=user.id,
        course_id="ai_deep_learning_demo",
        generation_metadata={"generation_source": "seed"},
    )
    context = CourseLearningService(planner).get_learning_context(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
        task_id="task_goal",
    )
    assert context["generation"]["generation_source"] == "seed"
    assert context["current_task"]["task_type"] == "objective"
    assert context["current_task"]["type_label"] == "学习目标"


def test_different_profiles_produce_different_rule_paths():
    agent = PlannerAgent(None)
    context = AgentContext(user_id="demo_student", course_id="ai_deep_learning_demo")
    image_path = agent._rule_based_plan_v2(
        context=context,
        profile={
            "learning_goal": "完成图像分类项目",
            "knowledge_level": "初级",
            "weakness": ["数学基础", "机器学习基础"],
            "interest": ["CNN"],
        },
    )
    advanced_image_path = agent._rule_based_plan_v2(
        context=context,
        profile={
            "learning_goal": "完成图像分类项目",
            "knowledge_level": "高级",
            "weakness": ["CNN"],
            "interest": ["图像分类"],
        },
    )
    nlp_path = agent._rule_based_plan_v2(
        context=context,
        profile={
            "learning_goal": "完成自然语言处理和文本分类项目",
            "knowledge_level": "中级",
            "weakness": ["Transformer"],
            "interest": ["文本分类"],
        },
    )
    image_signature = [
        (stage.title, stage.learning_objectives, [task.task_type for task in stage.tasks])
        for stage in image_path.stages
    ]
    advanced_image_signature = [
        (stage.title, stage.learning_objectives, [task.task_type for task in stage.tasks])
        for stage in advanced_image_path.stages
    ]
    nlp_signature = [
        (stage.title, stage.learning_objectives, [task.task_type for task in stage.tasks])
        for stage in nlp_path.stages
    ]
    assert image_signature != advanced_image_signature
    assert image_signature != nlp_signature
    assert len(advanced_image_path.stages) < len(image_path.stages)


def test_strict_mode_does_not_fall_back_to_rule_template(monkeypatch):
    import agents.planner_agent as planner_module

    class FailingLLM:
        last_usage = None

        async def chat(self, **_kwargs):
            raise RuntimeError("spark unavailable")

    monkeypatch.setattr(planner_module, "LLM_STRICT_MODE", True)
    agent = PlannerAgent(FailingLLM())
    context = AgentContext(user_id="demo_student", course_id="ai_deep_learning_demo")

    with pytest.raises(Exception):
        asyncio.run(agent.generate_plan_v2(
            context=context,
            profile={"learning_goal": "完成图像分类项目"},
        ))
    assert agent.last_generation_metadata == {}


def test_learning_page_has_no_fixed_path_or_fake_completion_timer():
    source = (ROOT / "frontend" / "src" / "pages" / "StudyHomePage.jsx").read_text(
        encoding="utf-8"
    )
    assert "buildStageLearningTasks" not in source
    assert "setTaskOverrides" not in source
    assert "await new Promise" not in source
    assert "completeCourseTask" in source


def test_demo_course_api_is_authenticated_scoped_and_refreshable():
    from app import app

    with TestClient(app) as client:
        login = client.post(
            "/api/auth/login",
            json={"username": "demo_student", "password": "demo123"},
        )
        assert login.status_code == 200
        token = login.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        first = client.get(
            "/api/courses/ai_deep_learning_demo/learn",
            headers=headers,
        )
        path_overview = client.get(
            "/api/courses/ai_deep_learning_demo/learning-path",
            headers=headers,
        )
        refreshed = client.get(
            "/api/courses/ai_deep_learning_demo/learn",
            headers=headers,
        )
        source = client.get(
            "/api/courses/ai_deep_learning_demo/learning-path/generation",
            headers=headers,
        )
        idempotent = client.post(
            "/api/courses/ai_deep_learning_demo/tasks/task_gd_goal/complete",
            headers=headers,
        )

        learning_state = client.get(
            "/api/courses/ai_deep_learning_demo/learning-state",
            headers=headers,
        )

        assert first.status_code == 200
        assert path_overview.status_code == 200
        assert refreshed.status_code == 200
        assert learning_state.status_code == 200
        assert login.json()["data"]["user"]["is_demo"] is True
        assert first.json()["data"]["course"]["name"] == "人工智能与深度学习"
        assert first.json()["data"]["course"]["goal"] == "掌握 Transformer 注意力机制"
        assert first.json()["data"]["course_status"] == "completed"
        assert first.json()["data"]["current_task"] is None
        assert refreshed.json()["data"]["progress"] == first.json()["data"]["progress"]
        assert path_overview.json()["data"]["progress"] == first.json()["data"]["path_progress"]
        assert learning_state.json()["data"]["progress"]["percent"] == 100
        assert learning_state.json()["data"]["current_task"] is None
        assert learning_state.json()["data"]["next_task"] is None
        assert source.json()["data"]["generation_source"] in {"agent", "seed"}
        assert idempotent.status_code == 409
        assert idempotent.json()["code"] == "COURSE_ALREADY_COMPLETED"

        admin_login = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        admin_token = admin_login.json()["data"]["token"]
        forbidden_scope = client.get(
            "/api/courses/ai_deep_learning_demo/learn",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert forbidden_scope.status_code == 404
