"""Day 11 fixed-student E2E flow tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app  # noqa: E402
from api import resource_api  # noqa: E402
from database import SessionLocal  # noqa: E402
from deps import tutor_service  # noqa: E402
from test.support.demo_data import DAY11_STUDENT_ID, ensure_demo_student  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        db = SessionLocal()
        try:
            ensure_demo_student(db)
        finally:
            db.close()
        yield test_client


def assert_success_envelope(payload: dict):
    assert payload["success"] is True
    assert "data" in payload
    assert payload["message"]


def parse_sse_events(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


def test_day11_fixed_student_profile_to_evaluation_flow(monkeypatch, client):
    monkeypatch.setattr(resource_api.resource_service, "resource_agent", None)

    class FakeRetriever:
        def retrieve(self, query, top_k=3, min_similarity=0.3):
            return [
                {
                    "title": "梯度下降复习卡",
                    "source": "day11.md",
                    "content": "梯度下降通过损失函数梯度更新参数。",
                    "similarity": 0.96,
                }
            ]

    class FakeTutorAgent:
        async def tutor(self, question, context=None, explanation_style="auto", profile=None):
            return json.dumps({
                "answer": "梯度下降就是沿着损失下降最快的方向逐步更新参数。",
                "explanation_style": "analogy",
                "references": [],
                "diagrams": [],
            }, ensure_ascii=False)

    monkeypatch.setattr(tutor_service, "retriever", FakeRetriever())
    monkeypatch.setattr(tutor_service, "tutor_agent", FakeTutorAgent())

    health_response = client.get("/api/health")
    assert health_response.status_code == 200
    assert_success_envelope(health_response.json())

    profile_response = client.get(f"/api/profile/{DAY11_STUDENT_ID}")
    assert profile_response.status_code == 200
    profile_payload = profile_response.json()
    assert_success_envelope(profile_payload)
    assert profile_payload["data"]["student_id"] == DAY11_STUDENT_ID
    assert profile_payload["data"]["weakness"]

    path_response = client.get(f"/api/planner/{DAY11_STUDENT_ID}")
    assert path_response.status_code == 200
    path_payload = path_response.json()
    assert_success_envelope(path_payload)
    path = path_payload["data"]
    assert path["student_id"] == DAY11_STUDENT_ID
    assert path["stages"]

    resource_response = client.post(
        "/api/resource/generate",
        json={
            "student_id": DAY11_STUDENT_ID,
            "topic": "梯度下降",
            "types": ["document", "exercise"],
            "difficulty": "中级",
            "count": 1,
            "path_id": path["id"],
        },
    )
    assert resource_response.status_code == 200
    resource_payload = resource_response.json()
    assert_success_envelope(resource_payload)
    task_id = resource_payload["data"]["task_id"]

    task_response = client.get(f"/api/task/{task_id}/status")
    assert task_response.status_code == 200
    task_payload = task_response.json()
    assert_success_envelope(task_payload)
    assert task_payload["data"]["status"] == "done"
    assert task_payload["data"]["result"]["total"] >= 1

    resource_list_response = client.get(f"/api/resource/list?student_id={DAY11_STUDENT_ID}")
    assert resource_list_response.status_code == 200
    resource_list_payload = resource_list_response.json()
    assert_success_envelope(resource_list_payload)
    assert resource_list_payload["data"]["total"] >= 1
    resource_id = resource_list_payload["data"]["items"][0]["id"]

    tutor_response = client.post(
        "/api/tutor/chat",
        json={
            "student_id": DAY11_STUDENT_ID,
            "message": "请用类比法解释梯度下降",
            "explanation_style": "analogy",
            "top_k": 1,
        },
    )
    assert tutor_response.status_code == 200
    tutor_events = parse_sse_events(tutor_response.text)
    data_event = next(event for event in tutor_events if event["type"] == "data")
    assert "梯度下降" in data_event["data"]["answer"]
    assert data_event["data"]["references"][0]["source"] == "day11.md"
    assert tutor_events[-1]["type"] == "done"

    record_response = client.post(
        "/api/evaluate/record",
        json={
            "student_id": DAY11_STUDENT_ID,
            "resource_id": resource_id,
            "action": "answer",
            "topic": "梯度下降",
            "score": 76,
            "time_spent": 1800,
        },
    )
    assert record_response.status_code == 200
    assert_success_envelope(record_response.json())

    evaluation_response = client.post("/api/evaluate/start", json={"student_id": DAY11_STUDENT_ID})
    assert evaluation_response.status_code == 200
    evaluation_payload = evaluation_response.json()
    assert_success_envelope(evaluation_payload)
    report = evaluation_payload["data"]
    assert report["student_id"] == DAY11_STUDENT_ID
    assert "overall_score" in report
    assert report["dimensions"]
    assert "streak_days" in report
    assert "weekly_activity" in report

    saved_report_response = client.get(f"/api/evaluate/report/{DAY11_STUDENT_ID}")
    assert saved_report_response.status_code == 200
    saved_report_payload = saved_report_response.json()
    assert_success_envelope(saved_report_payload)
    assert saved_report_payload["data"]["report_id"] == report["report_id"]
