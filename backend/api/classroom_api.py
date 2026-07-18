"""互动课堂 API。"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth_api import require_user
from api.response import ApiError, ok
from database import SessionLocal, get_db
from deps import classroom_service, task_service

router = APIRouter()


class GenerateClassroomRequest(BaseModel):
    course_id: str
    stage_id: str = "stage_gradient_descent"
    task_id: str = "task_gradient_classroom"
    topic: str = "梯度下降与学习率"


class SceneProgressRequest(BaseModel):
    status: str = "completed"
    progress: float = 1.0
    interactions: list = []


class TutorChatRequest(BaseModel):
    scene_id: str
    question: str
    selected_text: str | None = None
    user_actions: list = []


class InterventionCheckRequest(BaseModel):
    scene_id: str
    user_actions: list = []


class QuizSubmitRequest(BaseModel):
    answers: dict


@router.post("/generate")
async def generate_classroom(request: GenerateClassroomRequest, background_tasks: BackgroundTasks, user=Depends(require_user)):
    task = task_service.create("互动课堂生成任务已创建")

    async def run_task():
        db = SessionLocal()
        try:
            def update(progress: int, phase: str, message: str):
                task_service.update(task["task_id"], status="running", progress=progress, phase=phase, message=message)

            update(8, "analyzing_goals", "读取阶段学习目标")
            update(24, "retrieving_knowledge", "检索当前课程知识库")
            update(42, "planning_scenes", "规划课堂场景")
            update(62, "generating_simulation", "生成交互模拟与课堂测验")
            result = await classroom_service.generate_for_stage(
                db,
                user=user,
                course_id=request.course_id,
                stage_id=request.stage_id,
                task_id=request.task_id,
                topic=request.topic,
            )
            update(88, "validating", "完成课堂内容校验")
            task_service.update(task["task_id"], status="done", progress=100, phase="completed", message="互动课堂生成完成", result=result)
        except Exception as exc:
            task_service.update(
                task["task_id"],
                status="failed",
                progress=100,
                phase="failed",
                message="互动课堂生成失败",
                error={"code": "CLASSROOM_GENERATION_FAILED", "message": str(exc)},
            )
        finally:
            db.close()

    background_tasks.add_task(run_task)
    return ok(task, "互动课堂生成任务已创建")


@router.get("/demo")
async def get_demo_classroom(course_id: str, user=Depends(require_user), db: Session = Depends(get_db)):
    return ok(classroom_service.get_or_create_demo_classroom(db, user, course_id))


@router.get("/{classroom_id}")
async def get_classroom(classroom_id: str, user=Depends(require_user), db: Session = Depends(get_db)):
    return ok(classroom_service.get_classroom(db, user, classroom_id))


@router.post("/{classroom_id}/sessions")
async def create_session(classroom_id: str, user=Depends(require_user), db: Session = Depends(get_db)):
    return ok(classroom_service.create_session(db, user, classroom_id), "课堂会话已创建")


@router.patch("/{classroom_id}/sessions/{session_id}/scenes/{scene_id}")
async def update_scene(classroom_id: str, session_id: str, scene_id: str, request: SceneProgressRequest, user=Depends(require_user), db: Session = Depends(get_db)):
    return ok(classroom_service.update_scene(db, user, classroom_id, session_id, scene_id, request.model_dump()))


@router.post("/{classroom_id}/sessions/{session_id}/tutor/chat")
async def tutor_chat(classroom_id: str, session_id: str, request: TutorChatRequest, user=Depends(require_user), db: Session = Depends(get_db)):
    try:
        return ok(classroom_service.tutor_reply(db, user, classroom_id, session_id, request.model_dump()))
    except ApiError:
        raise
    except Exception as exc:
        raise ApiError("TUTOR_SERVICE_UNAVAILABLE", "AI 导师暂时不可用，你仍可继续完成当前课堂", status_code=503) from exc


@router.post("/{classroom_id}/sessions/{session_id}/tutor/interventions/check")
async def check_intervention(classroom_id: str, session_id: str, request: InterventionCheckRequest, user=Depends(require_user), db: Session = Depends(get_db)):
    return ok(classroom_service.check_intervention(db, user, classroom_id, session_id, request.model_dump()))


@router.post("/{classroom_id}/sessions/{session_id}/quiz/submit")
async def submit_quiz(classroom_id: str, session_id: str, request: QuizSubmitRequest, user=Depends(require_user), db: Session = Depends(get_db)):
    return ok(classroom_service.submit_quiz(db, user, classroom_id, session_id, request.model_dump()))


@router.post("/{classroom_id}/sessions/{session_id}/complete")
async def complete_classroom(classroom_id: str, session_id: str, user=Depends(require_user), db: Session = Depends(get_db)):
    return ok(classroom_service.complete(db, user, classroom_id, session_id), "课堂已完成")


@router.post("/{classroom_id}/sessions/{session_id}/evaluate")
async def evaluate_classroom(classroom_id: str, session_id: str, user=Depends(require_user), db: Session = Depends(get_db)):
    return ok(classroom_service.evaluate(db, user, classroom_id, session_id))
