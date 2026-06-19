"""Resource service and ResourceAgent contract regression tests."""

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
from api import resource_api  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def parse_sse_events(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


def test_resource_generate_uses_resource_agent_generate_resources(monkeypatch, client):
    calls = []

    class FakeResourceAgent:
        async def generate_resources(
            self,
            topic,
            resource_types=None,
            difficulty="中级",
            profile=None,
            knowledge_context=None,
        ):
            calls.append({
                "topic": topic,
                "resource_types": resource_types,
                "difficulty": difficulty,
                "profile": profile,
            })
            return json.dumps({
                "resources": [
                    {
                        "type": "document",
                        "title": f"{topic} Agent 讲义",
                        "topic": topic,
                        "difficulty": difficulty,
                        "content": "Agent JSON 字符串结果",
                    }
                ]
            }, ensure_ascii=False)

    monkeypatch.setattr(resource_api.resource_service, "resource_agent", FakeResourceAgent())

    response = client.post(
        "/api/resource/generate",
        json={
            "student_id": f"resource-contract-{uuid.uuid4()}",
            "topic": "资源合同测试",
            "types": ["document"],
            "difficulty": "初级",
            "count": 1,
        },
    )

    assert response.status_code == 200
    task_id = response.json()["data"]["task_id"]
    status_payload = client.get(f"/api/task/{task_id}/status").json()["data"]
    assert status_payload["status"] == "done"
    assert status_payload["error"] is None
    assert status_payload["result"]["total"] == 1
    assert status_payload["result"]["items"][0]["content"] == "Agent JSON 字符串结果"
    assert calls[0]["resource_types"] == ["document"]
    assert calls[0]["difficulty"] == "初级"


def test_resource_generate_falls_back_when_agent_returns_invalid_json(monkeypatch, client):
    class InvalidJsonResourceAgent:
        async def generate_resources(self, **kwargs):
            return "这不是 JSON"

    monkeypatch.setattr(resource_api.resource_service, "resource_agent", InvalidJsonResourceAgent())

    response = client.post(
        "/api/resource/generate",
        json={
            "student_id": f"resource-fallback-{uuid.uuid4()}",
            "topic": "非法 JSON 兜底",
            "types": ["document"],
            "difficulty": "中级",
            "count": 1,
        },
    )

    assert response.status_code == 200
    task_id = response.json()["data"]["task_id"]
    status_payload = client.get(f"/api/task/{task_id}/status").json()["data"]
    assert status_payload["status"] == "done"
    assert status_payload["error"] is None
    assert status_payload["result"]["total"] == 1
    assert status_payload["result"]["items"][0]["topic"] == "非法 JSON 兜底"
    assert "学习讲义" in status_payload["result"]["items"][0]["content"]


def test_resource_stream_uses_generate_resources_not_missing_generate_stream(monkeypatch, client):
    class StreamCompatResourceAgent:
        async def generate_resources(self, topic, resource_types=None, difficulty="中级", profile=None):
            return json.dumps({
                "resources": [
                    {
                        "type": "exercise",
                        "title": f"{topic} 练习",
                        "topic": topic,
                        "difficulty": difficulty,
                        "content": "[]",
                    }
                ]
            }, ensure_ascii=False)

    monkeypatch.setattr(resource_api.resource_service, "resource_agent", StreamCompatResourceAgent())

    response = client.post(
        "/api/resource/generate/stream",
        json={
            "student_id": f"resource-stream-{uuid.uuid4()}",
            "topic": "流式合同测试",
            "types": ["exercise"],
            "difficulty": "中级",
            "count": 1,
        },
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert events[0]["type"] == "start"
    data_event = next(event for event in events if event["type"] == "data")
    assert data_event["data"]["total"] == 1
    assert data_event["data"]["items"][0]["type"] == "exercise"
    assert events[-1]["type"] == "done"
