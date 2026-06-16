"""API contract tests for the backend captain-owned integration surface."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import app  # noqa: E402
from api import evaluate_api  # noqa: E402
from deps import task_service  # noqa: E402


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


def test_missing_profile_uses_error_envelope(client):
    response = client.get("/api/profile/__missing_contract_student__")

    assert response.status_code == 404
    assert_error_envelope(response.json(), "PROFILE_NOT_FOUND")


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
