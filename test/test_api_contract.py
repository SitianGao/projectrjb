"""API contract tests for the backend captain-owned integration surface."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import app  # noqa: E402
from api.response import generic_exception_handler  # noqa: E402
from api import evaluate_api  # noqa: E402
from deps import task_service, tutor_service  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def assert_success_envelope(payload: dict):
    assert payload["success"] is True
    assert "data" in payload
    assert payload["message"]


def assert_error_envelope(payload: dict, code: str):
    assert payload["success"] is False
    assert payload["error"] is True
    assert payload["code"] == code
    assert payload["message"]


def parse_sse_events(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


def test_root_uses_success_envelope(client):
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert_success_envelope(payload)
    assert payload["data"]["status"] == "ok"


def test_resource_list_uses_success_envelope_and_compat_fields(client):
    response = client.get("/api/resource/list")

    assert response.status_code == 200
    payload = response.json()
    assert_success_envelope(payload)
    assert {"items", "total", "page", "page_size"} <= payload["data"].keys()
    assert payload["items"] == payload["data"]["items"]


def test_resource_plural_alias_matches_frontend_client(client):
    response = client.get("/api/resources/list")

    assert response.status_code == 200
    payload = response.json()
    assert_success_envelope(payload)
    assert {"items", "total", "page", "page_size"} <= payload["data"].keys()


def test_tutor_session_creation_uses_success_envelope_and_compat_fields(client):
    response = client.post(
        "/api/tutor/sessions",
        json={"student_id": "contract-student", "title": "合同测试会话"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert_success_envelope(payload)
    assert payload["data"]["session_id"]
    assert payload["session_id"] == payload["data"]["session_id"]


def test_tutor_chat_stream_uses_day8_sse_contract(monkeypatch, client):
    class FakeRetriever:
        def retrieve(self, query, top_k=3, min_similarity=0.3):
            return [
                {
                    "title": "二次函数知识点",
                    "source": "math.md",
                    "content": "二次函数顶点式是 y=a(x-h)^2+k。",
                    "similarity": 0.91,
                }
            ]

    class FakeTutorAgent:
        async def tutor(self, question, context=None, explanation_style="auto", profile=None):
            return json.dumps({
                "answer": "顶点式可以直接看出顶点坐标。",
                "explanation_style": "analogy",
                "references": [],
                "diagrams": ["graph TD\nA[顶点式] --> B[顶点坐标]"],
            }, ensure_ascii=False)

    monkeypatch.setattr(tutor_service, "retriever", FakeRetriever())
    monkeypatch.setattr(tutor_service, "tutor_agent", FakeTutorAgent())

    response = client.post(
        "/api/tutor/chat",
        json={
            "student_id": "contract-student",
            "message": "解释二次函数顶点式",
            "explanation_style": "analogy",
            "top_k": 1,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse_events(response.text)
    event_types = [event["type"] for event in events]
    assert {"start", "delta", "data", "done"} <= set(event_types)

    data_event = next(event for event in events if event["type"] == "data")
    payload = data_event["data"]
    assert payload["answer"] == "顶点式可以直接看出顶点坐标。"
    assert payload["explanation_style"] == "analogy"
    assert payload["diagrams"]
    assert payload["references"][0]["title"] == "二次函数知识点"
    assert payload["references"][0]["source"] == "math.md"


def test_tutor_ask_stream_keeps_compatibility(monkeypatch, client):
    class FakeTutorAgent:
        async def tutor(self, question, context=None, explanation_style="auto", profile=None):
            return json.dumps({
                "answer": "兼容接口仍然可用。",
                "explanation_style": "auto",
                "references": [],
                "diagrams": [],
            }, ensure_ascii=False)

    monkeypatch.setattr(tutor_service, "retriever", None)
    monkeypatch.setattr(tutor_service, "tutor_agent", FakeTutorAgent())

    response = client.post(
        "/api/tutor/ask/stream",
        json={"student_id": "contract-student", "message": "兼容测试"},
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert any(event["type"] == "data" for event in events)
    assert events[-1]["type"] == "done"


def test_evaluate_report_uses_success_envelope(monkeypatch, client):
    def fake_report(db, student_id):
        return {
            "student_id": student_id,
            "overall_score": 88,
            "dimensions": [],
            "weak_topics": [],
            "suggestions": [],
            "review_plan": [],
        }

    monkeypatch.setattr(evaluate_api.evaluate_service, "build_report", fake_report)
    response = client.get("/api/evaluate/report/contract-student")

    assert response.status_code == 200
    payload = response.json()
    assert_success_envelope(payload)
    assert payload["data"]["overall_score"] == 88
    assert payload["overall_score"] == 88


def test_day9_evaluate_record_start_and_saved_report(client):
    student_id = f"contract-day9-{uuid.uuid4()}"
    records = [
        {
            "student_id": student_id,
            "action": "complete",
            "topic": "线性回归",
            "score": 88,
            "time_spent": 1800,
        },
        {
            "student_id": student_id,
            "action": "answer",
            "topic": "梯度下降",
            "score": 55,
            "time_spent": 1500,
        },
    ]

    for record in records:
        response = client.post("/api/evaluate/record", json=record)
        assert response.status_code == 200
        payload = response.json()
        assert_success_envelope(payload)
        assert payload["data"]["topic"] == record["topic"]

    start_response = client.post("/api/evaluate/start", json={"student_id": student_id})
    assert start_response.status_code == 200
    start_payload = start_response.json()
    assert_success_envelope(start_payload)
    report = start_payload["data"]
    required = {"overall_score", "dimensions", "weak_topics", "suggestions", "review_plan"}
    assert required <= report.keys()
    assert report["report_id"]
    assert report["overall_score"] == 72
    assert "梯度下降" in report["weak_topics"]
    assert report["review_plan"][0]["topic"] == "梯度下降"
    assert "streak_days" in report
    assert "weekly_activity" in report
    assert "streak_days" in report["progress_stats"]
    assert "weekly_activity" in report["progress_stats"]
    assert len(report["weekly_activity"]) == 7

    saved_response = client.get(f"/api/evaluate/report/{student_id}")
    assert saved_response.status_code == 200
    saved_payload = saved_response.json()
    assert_success_envelope(saved_payload)
    assert saved_payload["data"]["report_id"] == report["report_id"]
    assert saved_payload["data"]["suggestions"]


def test_missing_profile_uses_error_envelope(client):
    response = client.get("/api/profile/__missing_contract_student__")

    assert response.status_code == 404
    assert_error_envelope(response.json(), "PROFILE_NOT_FOUND")


def test_validation_error_uses_error_envelope(client):
    response = client.post("/api/resource/generate", json={})

    assert response.status_code == 422
    assert_error_envelope(response.json(), "VALIDATION_ERROR")


def test_unhandled_exception_uses_error_envelope():
    from fastapi import FastAPI

    probe_app = FastAPI()
    probe_app.add_exception_handler(Exception, generic_exception_handler)

    @probe_app.get("/boom")
    async def boom():
        raise RuntimeError("boom")

    with TestClient(probe_app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/boom")

    assert response.status_code == 500
    assert_error_envelope(response.json(), "INTERNAL_SERVER_ERROR")


def test_task_status_error_and_task_id_prefix(client):
    created = task_service.create("合同测试任务")
    assert created["task_id"].startswith("task_")

    success_response = client.get(f"/api/task/{created['task_id']}/status")
    assert success_response.status_code == 200
    success_payload = success_response.json()
    assert_success_envelope(success_payload)
    assert success_payload["data"]["task_id"] == created["task_id"]

    missing_response = client.get("/api/task/task_missing/status")
    assert missing_response.status_code == 404
    assert_error_envelope(missing_response.json(), "TASK_NOT_FOUND")


def test_openapi_exposes_design_main_paths(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    expected_paths = {
        "/api/profile/chat",
        "/api/planner/generate",
        "/api/resource/generate",
        "/api/resource/list",
        "/api/tutor/chat",
        "/api/evaluate/start",
        "/api/evaluate/report/{student_id}",
        "/api/evaluate/record",
        "/api/task/{task_id}/status",
    }
    assert expected_paths <= paths.keys()
