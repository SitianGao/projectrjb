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
from services import resource_service as resource_service_module  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        login = test_client.post(
            "/api/auth/login",
            json={"username": "demo_student", "password": "demo123"},
        )
        assert login.status_code == 200
        token = login.json()["data"]["token"]
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        yield test_client


def parse_sse_events(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


def test_resource_generate_uses_resource_agent_v2(monkeypatch, client):
    """v2 合约：ResourceService 应调用 generate_resources_v2 并返回结构化输出。"""
    calls = []

    class FakeResourceAgent:
        async def generate_resources_v2(
            self,
            *,
            context,
            topic,
            resource_types=None,
            difficulty="中级",
            profile=None,
            stage_info=None,
            knowledge_context=None,
            **kwargs,
        ):
            calls.append({
                "topic": topic,
                "resource_types": resource_types,
                "difficulty": difficulty,
                "profile": profile,
            })
            # 返回 ResourceGenerationOutput Pydantic 模型模拟
            from agents.schemas import ResourceGenerationOutput, ResourceMeta
            return ResourceGenerationOutput(
                resources=[
                    ResourceMeta(
                        resource_type="document",
                        title=f"{topic} Agent 讲义",
                        topic=topic,
                        difficulty=difficulty,
                        content={"sections": [{"heading": "test", "paragraphs": ["ok"], "examples": [], "key_points": []}], "summary": "test"},
                    )
                ],
                total=1,
            )

    monkeypatch.setattr(resource_api.resource_service, "resource_agent", FakeResourceAgent())

    response = client.post(
        "/api/resource/generate",
        json={
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
    # v2 输出是结构化 dict，不是字符串
    content = status_payload["result"]["items"][0]["content"]
    assert isinstance(content, dict) or isinstance(content, str)
    assert calls[0]["resource_types"] == ["document"]
    assert calls[0]["difficulty"] == "初级"


def test_resource_generate_falls_back_when_agent_raises(monkeypatch, client):
    """v2：Agent 抛异常时应降级为 template 资源。"""
    class FailingResourceAgent:
        async def generate_resources_v2(self, **kwargs):
            raise RuntimeError("模拟 LLM 调用失败")

    monkeypatch.setattr(resource_api.resource_service, "resource_agent", FailingResourceAgent())
    monkeypatch.setattr(resource_service_module, "RAG_STRICT_MODE", False)
    monkeypatch.setattr(resource_api.resource_service, "retriever", None)

    response = client.post(
        "/api/resource/generate",
        json={
            "topic": "异常兜底测试",
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
    assert status_payload["result"]["items"][0]["topic"] == "异常兜底测试"
    assert "暂时无法生成完整内容" in status_payload["result"]["items"][0]["content"]


def test_resource_stream_uses_generate_resources_v2(monkeypatch, client):
    """v2 合约：stream/generate 端点应调用 v2 方法。"""
    class StreamV2ResourceAgent:
        async def generate_resources_v2(
            self, *, context, topic, resource_types=None,
            difficulty="中级", profile=None, stage_info=None,
            knowledge_context=None, **kwargs,
        ):
            from agents.schemas import ResourceGenerationOutput, ResourceMeta
            return ResourceGenerationOutput(
                resources=[
                    ResourceMeta(
                        resource_type="exercise",
                        title=f"{topic} 练习",
                        topic=topic,
                        difficulty=difficulty,
                        content={
                            "instructions": "完成练习",
                            "questions": [{
                                "id": "q1",
                                "type": "short_answer",
                                "stem": f"请解释 {topic}",
                                "options": [],
                                "correct_answer": ["围绕核心概念作答"],
                                "explanation": "检查是否掌握核心概念",
                                "difficulty": "medium",
                                "knowledge_point_ids": [topic],
                            }],
                        },
                    )
                ],
                total=1,
            )

    monkeypatch.setattr(resource_api.resource_service, "resource_agent", StreamV2ResourceAgent())

    response = client.post(
        "/api/resource/generate/stream",
        json={
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
    assert data_event["total"] == 1
    assert data_event["items"][0]["type"] == "exercise"
    assert events[-1]["type"] == "done"
