"""
Contextual Resource Job Queue
Background job scheduling for contextual resource generation
triggered by tutor, evaluation, wrong-book, etc.
"""

from __future__ import annotations

from typing import Dict, Optional

from database import SessionLocal
from models.auth import User


def queue_contextual_resource(
    *,
    background_tasks,
    task_service,
    resource_service,
    owner_user_id: str,
    course_id: str,
    learning_task: Dict,
    topic: str,
    resource_type: str,
    trigger_source: str,
    trigger_context: Optional[Dict] = None,
    difficulty: str = "初级",
    force_regenerate: bool = False,
    variant_type: Optional[str] = None,
) -> Dict:
    """Queue a background task to generate a contextual learning resource.

    Returns a task-status dict that callers can return directly to the client.
    """
    task_id = learning_task.get("task_id", "")
    stage_id = learning_task.get("stage_id")

    task = task_service.create("正在准备学习资源…", owner_user_id=owner_user_id)
    tracking_id = task["task_id"]

    async def _run():
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == owner_user_id).first()
            if not user:
                task_service.update(
                    tracking_id,
                    status="failed",
                    progress=100,
                    phase="failed",
                    message="用户不存在",
                    error={"code": "USER_NOT_FOUND", "message": "用户不存在"},
                )
                return

            def _on_progress(progress: int, phase: str, message: str):
                task_service.update(
                    tracking_id,
                    status="running",
                    progress=progress,
                    phase=phase,
                    message=message,
                )

            generation_options = {
                "difficulty": difficulty,
                "force_regenerate": force_regenerate,
                "variant_type": variant_type,
            }

            result = await resource_service.generate_contextual_resource(
                db=db,
                user=user,
                course_id=course_id,
                task_id=task_id,
                stage_id=stage_id,
                resource_type=resource_type,
                topic=topic,
                trigger_source=trigger_source,
                trigger_context=trigger_context,
                generation_options=generation_options,
                on_progress=_on_progress,
            )

            task_service.update(
                tracking_id,
                status="done",
                progress=100,
                phase="completed",
                message="学习资源已就绪",
                result=result,
            )
        except Exception as exc:
            task_service.update(
                tracking_id,
                status="failed",
                progress=100,
                phase="failed",
                message="资源生成失败",
                error={"code": "CONTEXTUAL_RESOURCE_FAILED", "message": str(exc)},
            )
        finally:
            db.close()

    background_tasks.add_task(_run)

    return {
        "task_id": task_id,
        "tracking_id": tracking_id,
        "status": "generating",
        "topic": topic,
        "resource_type": resource_type,
        "trigger_source": trigger_source,
    }
