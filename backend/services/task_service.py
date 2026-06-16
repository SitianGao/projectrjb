"""In-memory task status registry for local development and demos."""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict, Optional


class TaskService:
    """Small task registry used by async API endpoints."""

    def __init__(self):
        self._tasks: Dict[str, Dict] = {}

    def create(self, message: str = "任务已创建") -> Dict:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "message": message,
            "result": None,
            "error": None,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        self._tasks[task_id] = task
        return task

    def update(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        result=None,
        error: Any = None,
    ) -> Dict:
        task = self._tasks[task_id]
        if status is not None:
            task["status"] = status
        if progress is not None:
            task["progress"] = progress
        if message is not None:
            task["message"] = message
        if result is not None:
            task["result"] = result
        if error is not None:
            task["error"] = error
        task["updated_at"] = _now_iso()
        return task

    def get(self, task_id: str) -> Optional[Dict]:
        return self._tasks.get(task_id)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
