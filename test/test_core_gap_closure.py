"""五项核心能力差距的新增回归测试。"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base
from services.adaptation_service import AdaptationService
from services.auth_service import AuthService
from services import artifact_service as artifact_module
from services.planner_service import PlannerService
from services.resource_service import ResourceService
from models.learning_path import LearningPath
from models.resource import Resource
from models.student import Student
import json


def test_users_and_courses_receive_isolated_student_ids():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        service = AuthService()
        first = service.register(db, "learner_one", "password1")
        second = service.register(db, "learner_two", "password2")
        first_student = first["user"]["student_id"]
        second_student = second["user"]["student_id"]
        assert first_student != second_student

        user = service.authenticate(db, first["token"])
        updated = service.create_course(db, user, "第二门课程", "学习数据库")
        assert updated["student_id"] not in {first_student, second_student}
        assert len(updated["courses"]) == 2
        active_id = updated["active_course"]["id"]
        renamed = service.update_course(
            db,
            user,
            active_id,
            title="数据库系统课程",
            goal="掌握数据库设计与 SQL",
        )
        assert renamed["active_course"]["title"] == "数据库系统课程"
        assert renamed["active_course"]["goal"] == "掌握数据库设计与 SQL"
    finally:
        db.close()
        engine.dispose()


def test_ppt_resource_is_a_real_downloadable_file(tmp_path, monkeypatch):
    monkeypatch.setattr(artifact_module, "GENERATED_RESOURCE_DIR", tmp_path)
    url, mime_type = artifact_module.artifact_service.create(
        "ppt-test",
        "ppt",
        "梯度下降课件",
        "Slide 1: 核心概念\n- 定义\n- 示例\nSlide 2: 小结\n- 复习要点",
    )
    output = Path(tmp_path, "ppt-test.pptx")
    assert url == "/generated/ppt-test.pptx"
    assert mime_type.startswith("application/")
    assert output.exists() and output.stat().st_size > 10_000


async def test_evaluation_feedback_replans_and_generates_review_resources():
    calls = {"planner": [], "resource": []}

    class Evaluate:
        async def start_evaluation_async(self, db, student_id):
            return {
                "weak_topics": ["梯度下降"],
                "review_plan": [{
                    "topic": "梯度下降",
                    "urgency": "high",
                    "recommended_resources": ["document", "exercise"],
                }],
            }

    class Planner:
        def get_current_path(self, db, student_id):
            return {"id": "old-path", "goal": "机器学习", "stages": [{}]}

        async def build_path(self, **kwargs):
            calls["planner"].append(kwargs)
            return {"id": "new-path", "goal": "机器学习", "stages": [{}]}

    class Resource:
        async def generate_resources(self, **kwargs):
            calls["resource"].append(kwargs)
            return {"items": [{"id": "review-resource", "is_review": True}]}

    result = await AdaptationService(Evaluate(), Planner(), Resource()).adapt(None, "student")

    assert result["adapted"] is True
    assert calls["planner"][0]["evaluation_feedback"]["weak_topics"] == ["梯度下降"]
    assert calls["resource"][0]["path_id"] == "new-path"
    assert calls["resource"][0]["is_review"] is True


def test_frontend_path_history_adapter_archives_without_deleting_evidence():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        student_id = "frontend-course-student"
        db.add(Student(id=student_id, nickname="前端联调"))
        old = LearningPath(
            id="path-v1",
            student_id=student_id,
            version=1,
            goal="机器学习",
            stages=json.dumps([{"stage_id": 1, "title": "基础", "tasks": []}]),
            current_stage=1,
            status="superseded",
        )
        current = LearningPath(
            id="path-v2",
            student_id=student_id,
            version=2,
            goal="机器学习",
            stages=json.dumps([{"stage_id": 1, "title": "进阶", "tasks": []}]),
            current_stage=1,
            status="active",
        )
        db.add_all([old, current])
        db.commit()

        service = PlannerService(None, None, None)
        assert service.get_path_by_id(db, student_id, "path-v2")["version"] == 2
        assert service.archive_path(db, student_id, "path-v2") is True
        assert db.query(LearningPath).filter_by(id="path-v2").first().status == "archived"
        assert db.query(LearningPath).filter_by(id="path-v1").first().status == "active"
        assert [item["id"] for item in service.get_path_history(db, student_id)] == ["path-v1"]
    finally:
        db.close()
        engine.dispose()


async def test_resources_bind_to_exact_path_stage_and_keep_markdown_sources():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    calls = []

    class Profile:
        def get_or_create_student(self, db, student_id):
            return db.query(Student).filter_by(id=student_id).first()

        def get_profile(self, db, student_id):
            return {"student_id": student_id, "learning_goal": "掌握机器学习"}

    class Retriever:
        def retrieve(self, query, top_k, min_similarity):
            return [{
                "title": "梯度下降核心知识点",
                "source": "gradient_descent.md",
                "content": "# 梯度下降\n\n学习率控制每次参数更新的步长。",
                "similarity": 0.91,
            }]

    class Agent:
        async def generate_resources(self, **kwargs):
            calls.append(kwargs)
            return {
                "resources": [{
                    "type": "document",
                    "title": "梯度下降讲义",
                    "topic": "Agent 改写后的主题",
                    "difficulty": "中级",
                    "content": "基于知识库讲解梯度下降与学习率。",
                }]
            }

    try:
        student_id = "stage-resource-student"
        db.add(Student(id=student_id, nickname="阶段资源测试"))
        db.add(LearningPath(
            id="stage-resource-path",
            student_id=student_id,
            version=1,
            goal="掌握机器学习",
            stages=json.dumps([
                {"stage_id": 1, "title": "线性回归", "topics": ["线性回归"]},
                {"stage_id": 2, "title": "梯度下降", "topics": ["梯度下降", "学习率"]},
            ], ensure_ascii=False),
            current_stage=1,
            status="active",
        ))
        db.commit()

        result = await ResourceService(Agent(), Profile(), Retriever()).generate_resources(
            db=db,
            student_id=student_id,
            topic="梯度下降",
            path_id="stage-resource-path",
            stage_id=2,
            types=["document"],
        )

        saved = db.query(Resource).filter_by(id=result["items"][0]["id"]).one()
        assert saved.path_id == "stage-resource-path"
        assert saved.stage_id == "2"
        assert result["items"][0]["source_refs"][0]["source"] == "gradient_descent.md"
        assert calls[0]["stage_info"]["title"] == "梯度下降"
        assert any("梯度下降核心知识点" in item for item in calls[0]["knowledge_context"])
    finally:
        db.close()
        engine.dispose()
