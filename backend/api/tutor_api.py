"""
智能辅导 API
- POST /api/tutor/chat        智能辅导问答（SSE）
- POST /api/tutor/ask/stream  流式辅导对话（前端兼容）
- GET  /api/tutor/sessions    获取会话列表
- POST /api/tutor/sessions    创建会话
"""
from typing import List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.openapi_examples import json_responses, sse_responses
from api.auth_api import require_user
from api.contextual_resource_jobs import queue_contextual_resource
from api.response import ApiError, ok
from database import SessionLocal, get_db
from deps import planner_service, resource_service, task_service, tutor_service
from models.auth import Course
from sqlalchemy.orm import Session

router = APIRouter()

TUTOR_SSE_RESPONSES = sse_responses("TUTOR_CHAT_FAILED")


class TutorChatRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])
    message: str = Field(..., examples=["请解释一下二次函数的顶点式"])
    session_id: Optional[str] = None
    course_id: Optional[str] = None
    stage_id: Optional[str] = None
    task_id: Optional[str] = None
    learning_goal: Optional[str] = None
    action: str = Field(default="ask", examples=["ask"])
    selected_text: Optional[str] = None
    conversation_id: Optional[str] = None
    history: Optional[List[str]] = None
    explanation_style: Literal["auto", "analogy", "formula", "visual", "story"] = Field(
        default="auto",
        examples=["auto"],
    )
    top_k: int = Field(default=3, ge=1, le=8, examples=[3])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "student_id": "demo-student-01",
                    "message": "请用类比法解释一下二次函数顶点式",
                    "course_id": "ai_deep_learning_demo",
                    "stage_id": "stage_ai_basics",
                    "task_id": "task_ai_basics_document",
                    "action": "ask",
                    "session_id": None,
                    "history": [],
                    "explanation_style": "analogy",
                    "top_k": 3,
                }
            ]
        }
    }


class TutorSessionRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])
    title: Optional[str] = None


class TutorResourceRequest(BaseModel):
    course_id: str
    message: str
    session_id: Optional[str] = None
    topic: Optional[str] = None
    action: str = "document"
    resource_type: Optional[str] = None
    difficulty: str = "初级"
    force_regenerate: bool = False
    variant_type: Optional[str] = None


def _resolve_owned_course(db: Session, user, course_id: Optional[str], student_id: Optional[str]) -> Course:
    query = db.query(Course).filter(Course.user_id == user.id)
    if course_id:
        query = query.filter(Course.id == course_id)
    elif student_id:
        query = query.filter(Course.student_id == student_id)
    elif user.active_course_id:
        query = query.filter(Course.id == user.active_course_id)
    course = query.first()
    if not course:
        raise ApiError("COURSE_NOT_FOUND", "课程不存在或不属于当前登录用户", status_code=404)
    return course


async def _stream_tutor_response(request: TutorChatRequest, *, student_id: str, course_id: str):
    from core.sse import StreamingSseResponse

    async def event_generator():
        db = SessionLocal()
        try:
            async for event in tutor_service.chat_stream(
                db=db,
                student_id=student_id,
                message=request.message,
                session_id=request.session_id,
                course_id=course_id,
                stage_id=request.stage_id,
                task_id=request.task_id,
                learning_goal=request.learning_goal,
                action=request.action or "ask",
                selected_text=request.selected_text,
                conversation_id=request.conversation_id,
                history=request.history,
                explanation_style=request.explanation_style,
                top_k=request.top_k,
            ):
                yield event
        except Exception as e:
            import traceback
            traceback.print_exc()
            from core.sse import sse_error, sse_done
            yield sse_error("TUTOR_CHAT_FAILED", str(e) or "智能辅导失败，请稍后重试")
            yield sse_done()
        finally:
            db.close()

    return StreamingSseResponse(event_generator())


@router.post("/chat", responses=TUTOR_SSE_RESPONSES)
async def tutor_chat(
    request: TutorChatRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """智能辅导对话，SSE 流式返回"""
    course = _resolve_owned_course(db, user, request.course_id, request.student_id)
    return await _stream_tutor_response(request, student_id=course.student_id, course_id=course.id)


@router.post("/ask", responses=TUTOR_SSE_RESPONSES)
async def tutor_ask(
    request: TutorChatRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """智能辅导问答（前端兼容，非流式入口返回 SSE）"""
    course = _resolve_owned_course(db, user, request.course_id, request.student_id)
    return await _stream_tutor_response(request, student_id=course.student_id, course_id=course.id)


@router.post("/ask/stream", responses=TUTOR_SSE_RESPONSES)
async def tutor_ask_stream(
    request: TutorChatRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """流式辅导对话 (SSE, 前端兼容)"""
    course = _resolve_owned_course(db, user, request.course_id, request.student_id)
    return await _stream_tutor_response(request, student_id=course.student_id, course_id=course.id)


@router.post("/resources", responses=json_responses("RESOURCE_NOT_FOUND"))
async def create_tutor_resource(
    request: TutorResourceRequest,
    background_tasks: BackgroundTasks,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    course = _resolve_owned_course(db, user, request.course_id, None)
    intent = await tutor_service.extract_resource_intent(
        student_id=course.student_id,
        message=request.message,
        action=request.action,
        session_id=request.session_id,
        topic=request.topic,
        resource_type=request.resource_type,
    )
    session_key = request.session_id or "no-session"
    source_key = f"tutor:{session_key}:{intent['topic']}:{intent['resource_type']}"
    learning_task = planner_service.create_contextual_task(
        db,
        user_id=user.id,
        course_id=course.id,
        source_key=source_key,
        topic=intent["topic"],
        resource_type=intent["resource_type"],
        reason="由 AI 导师对话转化为可继续学习的资源",
        difficulty=request.difficulty,
        trigger_source="tutor",
    )
    job = queue_contextual_resource(
        background_tasks=background_tasks,
        task_service=task_service,
        resource_service=resource_service,
        owner_user_id=user.id,
        course_id=course.id,
        learning_task=learning_task,
        topic=intent["topic"],
        resource_type=intent["resource_type"],
        trigger_source="tutor",
        trigger_context={
            "tutor_session_id": request.session_id,
            "conversation_summary": intent["conversation_summary"],
            "intent_action": request.action,
        },
        difficulty=request.difficulty,
        force_regenerate=request.force_regenerate,
        variant_type=request.variant_type,
    )
    return ok(job, "已将对话转为学习资源")


@router.get("/history/{session_id}", responses=json_responses())
async def get_tutor_history(session_id: str):
    """获取对话历史"""
    return ok({"session_id": session_id, "messages": []})


@router.get("/sessions", responses=json_responses())
async def list_tutor_sessions(
    student_id: Optional[str] = None,
    course_id: Optional[str] = None,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """获取辅导会话列表。"""
    course = _resolve_owned_course(db, user, course_id, student_id)
    return ok(tutor_service.list_sessions(course.student_id))


@router.post("/sessions", responses=json_responses())
async def create_tutor_session(
    request: TutorSessionRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """创建辅导会话。"""
    course = _resolve_owned_course(db, user, None, request.student_id)
    return ok(tutor_service.create_session(course.student_id, request.title), "会话已创建")


@router.post("/check", responses=json_responses())
async def submit_answer():
    """提交答案供检查（前端兼容）"""
    return ok({"status": "ok", "correct": None, "feedback": "答案检查功能待 EvaluateAgent 接入。"})
