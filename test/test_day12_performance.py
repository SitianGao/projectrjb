"""Day 12 performance and stability tests."""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.llm_client import LLMClient  # noqa: E402
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


def test_planner_sse_emits_start_before_profile_lookup(client):
    response = client.post(
        "/api/planner/generate",
        json={"student_id": "__day12_missing_profile__", "goal": "性能测试"},
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert events[0]["type"] == "start"
    assert events[1]["type"] == "error"
    assert events[1]["code"] == "PROFILE_NOT_FOUND"
    assert events[-1]["type"] == "done"


def test_resource_task_reports_stage_progress(monkeypatch, client):
    monkeypatch.setattr(resource_api.resource_service, "resource_agent", None)

    response = client.post(
        "/api/resource/generate",
        json={
            "student_id": "day12-progress-student",
            "topic": "异步进度测试",
            "types": ["document"],
            "difficulty": "初级",
            "count": 1,
        },
    )

    assert response.status_code == 200
    task_id = response.json()["data"]["task_id"]
    status_response = client.get(f"/api/task/{task_id}/status")
    payload = status_response.json()["data"]
    assert payload["status"] == "done"
    assert payload["progress"] == 100
    assert payload["phase"] == "completed"
    assert payload["duration_ms"] is not None
    phases = [item["phase"] for item in payload["progress_history"]]
    assert {"queued", "started", "preparing", "generating", "persisting", "formatting", "completed"} <= set(phases)


def test_concurrent_resource_generation_tasks_do_not_interfere(monkeypatch):
    async def fake_generate_resources(
        db,
        student_id,
        topic,
        types=None,
        difficulty="中级",
        count=1,
        path_id=None,
        on_progress=None,
    ):
        if on_progress:
            on_progress(30, "generating", f"正在生成 {topic}")
            on_progress(80, "persisting", f"正在保存 {topic}")
        return {
            "student_id": student_id,
            "topic": topic,
            "difficulty": difficulty,
            "items": [
                {
                    "id": f"fake-{student_id}",
                    "student_id": student_id,
                    "type": "document",
                    "title": f"{topic} 并发测试资源",
                    "topic": topic,
                    "difficulty": difficulty,
                }
            ],
            "resources": [],
            "total": 1,
            "generated_at": "2026-06-19T10:00:00Z",
        }

    monkeypatch.setattr(resource_api.resource_service, "generate_resources", fake_generate_resources)

    def create_and_read(index: int) -> dict:
        with TestClient(app) as local_client:
            response = local_client.post(
                "/api/resource/generate",
                json={
                    "student_id": f"day12-concurrent-{index}",
                    "topic": f"并发资源 {index}",
                    "types": ["document"],
                    "difficulty": "初级",
                    "count": 1,
                },
            )
            task_id = response.json()["data"]["task_id"]
            status_response = local_client.get(f"/api/task/{task_id}/status")
            return status_response.json()["data"]

    with ThreadPoolExecutor(max_workers=5) as pool:
        tasks = list(pool.map(create_and_read, range(5)))

    task_ids = {task["task_id"] for task in tasks}
    topics = {task["result"]["topic"] for task in tasks}
    assert len(task_ids) == 5
    assert topics == {f"并发资源 {index}" for index in range(5)}
    assert all(task["status"] == "done" for task in tasks)
    assert all(task["duration_ms"] is not None for task in tasks)


async def test_llm_client_retries_spark_and_falls_back_to_deepseek(monkeypatch):
    attempts = []

    async def failing_spark(system, user, model=None):
        attempts.append("spark")
        raise httpx.ReadTimeout("spark timeout")
        yield ""

    async def fallback_deepseek(system, user):
        yield "备用模型回答"

    monkeypatch.setenv("LLM_PRIMARY", "spark")
    client = LLMClient()
    client.max_retries = 2
    client.retry_base_delay = 0
    monkeypatch.setattr(client, "_call_spark", failing_spark)
    monkeypatch.setattr(client, "_call_deepseek", fallback_deepseek)

    chunks = [chunk async for chunk in client.chat_stream("system", "user")]

    assert attempts == ["spark", "spark"]
    assert any("正在重试" in chunk for chunk in chunks)
    assert any("切换至备用模型" in chunk for chunk in chunks)
    assert chunks[-1] == "备用模型回答"
