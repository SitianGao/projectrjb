"""In-memory task status registry for local development and demos."""

from __future__ import annotations

import datetime
import threading
import uuid
from typing import Any, Dict, Optional


class TaskService:
    """Small task registry used by async API endpoints."""

    def __init__(self):
        self._tasks: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def create(
        self,
        message: str = "任务已创建",
        owner_user_id: Optional[str] = None,
    ) -> Dict:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = _now_iso()
        task = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "message": message,
            "phase": "queued",
            "result": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "finished_at": None,
            "duration_ms": None,
            "owner_user_id": owner_user_id,
            "progress_history": [
                {"progress": 0, "message": message, "phase": "queued", "at": now}
            ],
        }
        with self._lock:
            self._tasks[task_id] = task
            return dict(task)

    def update(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        phase: Optional[str] = None,
        result=None,
        error: Any = None,
    ) -> Dict:
        with self._lock:
            task = self._tasks[task_id]
            now = _now_iso()
            if status is not None:
                task["status"] = status
                if status == "running" and not task["started_at"]:
                    task["started_at"] = now
                if status in {"done", "failed"}:
                    task["finished_at"] = now
                    task["duration_ms"] = _duration_ms(task["started_at"] or task["created_at"], now)
            if progress is not None:
                task["progress"] = max(0, min(100, int(progress)))
            if message is not None:
                task["message"] = message
            if phase is not None:
                task["phase"] = phase
            if result is not None:
                task["result"] = result
            if error is not None:
                task["error"] = error
            task["updated_at"] = now
            task.setdefault("progress_history", []).append({
                "progress": task["progress"],
                "message": task["message"],
                "phase": task.get("phase"),
                "at": now,
            })
            return dict(task)

    def get(
        self,
        task_id: str,
        owner_user_id: Optional[str] = None,
    ) -> Optional[Dict]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task and owner_user_id and task.get("owner_user_id") != owner_user_id:
                return None
            return dict(task) if task else None


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _duration_ms(start_iso: str, end_iso: str) -> int:
    start = datetime.datetime.strptime(start_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    end = datetime.datetime.strptime(end_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    return max(0, round((end - start).total_seconds() * 1000))
