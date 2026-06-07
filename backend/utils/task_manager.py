"""
异步任务管理器 —— 管理资源生成等长耗时任务的进度追踪

用法（Day 6-7 实现）:
    from utils.task_manager import TaskStatus, TaskManager

    manager = TaskManager()
    task_id = manager.create_task()
    manager.update(task_id, status=TaskStatus.RUNNING, progress=0.5)
"""
import uuid
import time
from enum import Enum
from typing import Any, Optional


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class TaskManager:
    """异步任务进度管理器 —— 供 resource_api 和 task_api 使用"""

    def __init__(self):
        self._tasks: dict[str, dict[str, Any]] = {}

    def create_task(self) -> str:
        """创建新任务，返回 task_id"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        self._tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "progress": 0.0,
            "message": "任务已创建",
            "result": None,
            "created_at": time.time(),
        }
        return task_id

    def update(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        result: Optional[Any] = None,
    ) -> None:
        """更新任务进度"""
        if task_id not in self._tasks:
            raise KeyError(f"任务不存在: {task_id}")
        task = self._tasks[task_id]
        if status is not None:
            task["status"] = status
        if progress is not None:
            task["progress"] = progress
        if message is not None:
            task["message"] = message
        if result is not None:
            task["result"] = result

    def get(self, task_id: str) -> Optional[dict[str, Any]]:
        """获取任务状态"""
        return self._tasks.get(task_id)
