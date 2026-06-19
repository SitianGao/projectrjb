"""Day 10 API error contract tests."""

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
from api import evaluate_api, resource_api  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


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


def test_health_check_uses_success_envelope(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["database"] == "ok"


def test_json_error_endpoints_return_code_and_message(client):
    cases = [
        ("get", "/api/profile/__missing_day10_profile__", None, 404, "PROFILE_NOT_FOUND"),
        ("get", "/api/planner/__missing_day10_path__", None, 404, "PATH_NOT_FOUND"),
        ("get", "/api/resource/__missing_day10_resource__", None, 404, "RESOURCE_NOT_FOUND"),
        ("post", "/api/resource/__missing_day10_resource__/bookmark", None, 404, "RESOURCE_NOT_FOUND"),
        ("get", "/api/task/task_missing_day10/status", None, 404, "TASK_NOT_FOUND"),
        ("put", "/api/profile/day10-empty-update", {}, 400, "PROFILE_UPDATE_EMPTY"),
    ]

    for method, url, body, status_code, code in cases:
        response = getattr(client, method)(url, json=body) if body is not None else getattr(client, method)(url)
        assert response.status_code == status_code
        assert_error_envelope(response.json(), code)


def test_validation_error_returns_unified_error(client):
    response = client.post("/api/resource/generate", json={})

    assert response.status_code == 422
    assert_error_envelope(response.json(), "VALIDATION_ERROR")


def test_planner_sse_missing_profile_returns_code_and_message(client):
    response = client.post(
        "/api/planner/generate",
        json={"student_id": "__day10_no_profile_student__", "goal": "测试路径"},
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    error_event = next(event for event in events if event["type"] == "error")
    assert error_event["code"] == "PROFILE_NOT_FOUND"
    assert error_event["message"]
    assert events[-1]["type"] == "done"


def test_resource_sse_failure_returns_code_and_message(monkeypatch, client):
    async def failing_generate_stream(**kwargs):
        raise RuntimeError("resource boom")
        yield ""

    monkeypatch.setattr(resource_api.resource_service, "generate_stream", failing_generate_stream)
    response = client.post(
        "/api/resource/generate/stream",
        json={
            "student_id": "day10-resource-error",
            "topic": "错误测试",
            "types": ["document"],
            "difficulty": "初级",
            "count": 1,
        },
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    error_event = next(event for event in events if event["type"] == "error")
    assert error_event["code"] == "RESOURCE_GENERATE_FAILED"
    assert error_event["message"]
    assert events[-1]["type"] == "done"


def test_evaluate_sse_failure_returns_code_and_message(monkeypatch, client):
    async def failing_start_evaluation_async(db, student_id):
        raise RuntimeError("evaluate boom")

    monkeypatch.setattr(evaluate_api.evaluate_service, "start_evaluation_async", failing_start_evaluation_async)
    response = client.post("/api/evaluate/generate/stream", json={"student_id": "day10-evaluate-error"})

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    error_event = next(event for event in events if event["type"] == "error")
    assert error_event["code"] == "EVALUATE_FAILED"
    assert error_event["message"]
    assert events[-1]["type"] == "done"


def test_openapi_contains_day10_error_examples(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/health" in paths
    profile_404 = paths["/api/profile/{student_id}"]["get"]["responses"]["404"]
    example = profile_404["content"]["application/json"]["example"]
    assert example["code"] == "PROFILE_NOT_FOUND"
