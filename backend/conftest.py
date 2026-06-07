"""
pytest 全局 fixtures —— 测试数据库、TestClient、样例数据

用法:
    def test_something(test_client, sample_student):
        response = test_client.get(f"/api/profile/{sample_student['student_id']}")
        assert response.status_code == 200
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import app
from models import Base


@pytest.fixture(scope="function")
def test_db():
    """
    每次测试使用独立的内存数据库，测试完自动销毁。
    不污染开发数据库，测试之间完全隔离。
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def test_client():
    """
    FastAPI 测试客户端 —— 无需启动 uvicorn 即可测试接口。
    用法：test_client.get("/"), test_client.post("/api/tutor/chat", json={...})
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_student(test_db):
    """
    预置一个测试学生 + 画像，供 Agent 和 API 测试使用。
    返回 {"student_id": str, "db": Session}
    """
    from models.student import Student, StudentProfile

    sid = str(uuid.uuid4())
    student = Student(id=sid, nickname="测试学生")
    profile = StudentProfile(
        id=str(uuid.uuid4()),
        student_id=sid,
        knowledge_level="大二，机器学习入门，数学基础较弱",
        learning_goal="掌握深度学习基础算法",
        cognitive_style="视觉型学习者",
        weakness='["数学基础", "概率论"]',
        interest='["计算机视觉", "NLP"]',
    )
    test_db.add(student)
    test_db.add(profile)
    test_db.commit()
    return {"student_id": sid, "db": test_db}
