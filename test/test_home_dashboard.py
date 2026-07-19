"""首页 Dashboard 的课程绑定、实时统计和作用域回归测试。"""

from __future__ import annotations

import datetime
import pathlib
import sys
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from models import Base  # noqa: E402
from models.auth import Course, User  # noqa: E402
from models.evaluation import LearningRecord  # noqa: E402
from models.student import Student  # noqa: E402
from models.study_session import StudySession  # noqa: E402
from services.course_learning_service import CourseLearningService  # noqa: E402
from services.planner_service import PlannerService  # noqa: E402


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _seed_course(
    db,
    *,
    user_id="demo_student",
    course_id="ai_deep_learning_demo",
    title="人工智能与深度学习",
    goal="掌握 Transformer 注意力机制",
):
    student_id = f"{course_id}-student"
    user = User(
        id=user_id,
        username=user_id,
        password_hash="test-only",
        name="演示同学",
    )
    db.add(user)
    db.add(Student(id=student_id, nickname=user.name))
    db.add(Course(
        id=course_id,
        user_id=user.id,
        student_id=student_id,
        title=title,
        goal=goal,
    ))
    db.commit()
    return user, student_id


def _path_data(total=25, completed=9, *, title="深度学习基础与神经网络入门"):
    tasks = []
    for index in range(total):
        status = (
            "completed"
            if index < completed
            else "active"
            if index == completed
            else "not_started"
        )
        tasks.append({
            "task_id": f"task_{index + 1}",
            "task_type": "document" if index == completed else "exercise",
            "title": f"学习任务 {index + 1}",
            "status": status,
            "estimated_minutes": 20,
            "prerequisite_task_ids": [],
        })
    return {
        "goal": "掌握 Transformer 注意力机制",
        "current_stage": 1,
        "stages": [{
            "stage_id": "stage_deep_learning",
            "order": 1,
            "title": title,
            "status": "active",
            "learning_objectives": ["理解神经网络核心机制"],
            "topics": ["神经网络", "Transformer"],
            "estimated_days": 7,
            "tasks": tasks,
        }],
    }


def _service_with_path(db, user, student_id, *, total=25, completed=9):
    planner = PlannerService(None, None, None)
    path = planner.save_path(
        db,
        student_id,
        _path_data(total, completed),
        user_id=user.id,
        course_id="ai_deep_learning_demo",
        generation_metadata={"generation_source": "test"},
    )
    return CourseLearningService(planner), planner, path


def test_course_name_goal_and_progress_share_one_dashboard_source():
    db = _session()
    user, student_id = _seed_course(db)
    service, _, _ = _service_with_path(db, user, student_id)

    dashboard = service.get_home_dashboard(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
    )

    assert dashboard["course"]["course_name"] == "人工智能与深度学习"
    assert dashboard["learning_context"]["learning_goal"] == "掌握 Transformer 注意力机制"
    assert dashboard["learning_context"]["current_stage_title"] == "深度学习基础与神经网络入门"
    assert dashboard["statistics"]["completed_tasks"] == 9
    assert dashboard["statistics"]["total_tasks"] == 25
    assert dashboard["statistics"]["progress_percent"] == 36
    assert dashboard["progress"]["percentage"] == 36
    assert dashboard["statistics"]["accuracy_rate"] is None
    assert dashboard["continue_target"]["route"].endswith("/learn/task_10")


def test_empty_path_stats_are_zero_and_accuracy_is_null():
    db = _session()
    user, student_id = _seed_course(db)
    service, _, _ = _service_with_path(db, user, student_id, total=0, completed=0)

    dashboard = service.get_home_dashboard(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
    )

    assert dashboard["statistics"]["progress_percent"] == 0
    assert dashboard["statistics"]["completed_tasks"] == 0
    assert dashboard["statistics"]["total_tasks"] == 0
    assert dashboard["statistics"]["accuracy_rate"] is None


def test_task_answer_session_and_streak_update_realtime():
    db = _session()
    user, student_id = _seed_course(db)
    service, _, path = _service_with_path(db, user, student_id, total=4, completed=1)

    completion = service.complete_task(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
        task_id="task_2",
    )
    assert completion["idempotent"] is False

    today = datetime.datetime.utcnow()
    db.add_all([
        LearningRecord(
            id=str(uuid.uuid4()),
            student_id=student_id,
            action="answer",
            score=100,
            time_spent=0,
            created_at=today,
        ),
        LearningRecord(
            id=str(uuid.uuid4()),
            student_id=student_id,
            action="answer",
            score=0,
            time_spent=0,
            created_at=today - datetime.timedelta(days=1),
        ),
    ])
    db.commit()

    started = service.start_study_session(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
        task_id="task_3",
    )
    duplicate = service.start_study_session(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
        task_id="task_3",
    )
    assert duplicate["session_id"] == started["session_id"]
    assert duplicate["reused"] is True

    session = db.query(StudySession).filter_by(id=started["session_id"]).one()
    session.started_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=125)
    db.commit()
    closed = service.close_study_session(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
        session_id=session.id,
    )
    assert closed["status"] == "completed"

    dashboard = service.get_home_dashboard(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
    )
    assert dashboard["statistics"]["completed_tasks"] == 2
    assert dashboard["statistics"]["progress_percent"] == 50
    assert dashboard["statistics"]["accuracy_rate"] == 50
    assert dashboard["statistics"]["study_minutes"] == 2
    assert dashboard["statistics"]["streak_days"] == 2
    assert dashboard["course"]["course_id"] == path.course_id


def test_course_scope_and_new_active_path_do_not_mix_old_data():
    db = _session()
    user, student_id = _seed_course(db)
    service, planner, old_path = _service_with_path(db, user, student_id, total=25, completed=9)
    other, other_student_id = _seed_course(
        db,
        user_id="student123",
        course_id="other_course",
        title="离散数学",
        goal="掌握图论",
    )
    other_planner = PlannerService(None, None, None)
    other_planner.save_path(
        db,
        other_student_id,
        _path_data(10, 10, title="图论基础"),
        user_id=other.id,
        course_id="other_course",
        generation_metadata={"generation_source": "test"},
    )
    db.add(LearningRecord(
        id=str(uuid.uuid4()),
        student_id=other_student_id,
        action="answer",
        score=100,
        time_spent=7200,
    ))
    db.commit()

    planner.save_path(
        db,
        student_id,
        _path_data(3, 1, title="调整后的学习阶段"),
        user_id=user.id,
        course_id="ai_deep_learning_demo",
        generation_metadata={"generation_source": "agent"},
    )
    db.refresh(old_path)
    dashboard = service.get_home_dashboard(
        db,
        user=user,
        course_id="ai_deep_learning_demo",
    )

    assert old_path.status == "superseded"
    assert dashboard["statistics"]["total_tasks"] == 3
    assert dashboard["statistics"]["completed_tasks"] == 1
    assert dashboard["statistics"]["progress_percent"] == 33
    assert dashboard["statistics"]["study_minutes"] == 0
    assert dashboard["statistics"]["accuracy_rate"] is None


def test_frontend_has_no_fixed_dashboard_values_and_refreshes_on_return():
    home_source = (ROOT / "frontend" / "src" / "pages" / "HomePage.jsx").read_text(
        encoding="utf-8"
    )
    assert "const progress = 36" not in home_source
    assert "const studyMinutes = 182" not in home_source
    assert "9/25" not in home_source
    assert "HOME_DASHBOARD_INVALIDATE_EVENT" in home_source
    assert "window.addEventListener('focus'" in home_source
    assert "continue_target?.route" in home_source
