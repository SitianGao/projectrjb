"""课程画像初始化与增量更新 API。"""

from __future__ import annotations

import json
import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth_api import require_user
from api.response import ApiError, ok
from database import get_db
from deps import profile_service
from models.auth import Course


router = APIRouter()

DIMENSIONS = [
    ("learning_goal", "学习目标"),
    ("knowledge_level", "基础水平"),
    ("learning_history", "学习经历"),
    ("weakness", "薄弱点"),
    ("interest", "兴趣方向"),
    ("cognitive_style", "理解偏好"),
    ("pace_preference", "学习节奏"),
    ("available_time", "可投入时间"),
    ("assessment_preference", "测评偏好"),
    ("resource_preference", "资源偏好"),
]


class CourseProfileMessageRequest(BaseModel):
    message: str
    client_message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    history: Optional[list] = None
    current_profile: Optional[dict] = None


class CourseProfileUpdateRequest(BaseModel):
    profile_patch: dict


def _course_for_user(db: Session, user, course_id: str) -> Course:
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
    if not course:
        raise ApiError("COURSE_NOT_FOUND", "课程不存在或不属于当前用户", status_code=404)
    return course


def _safe_list(value):
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in re.split(r"[、,，;；\n]", value) if part.strip()]
    return []


def _as_text(value):
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def _infer_patch(message: str, course: Course, current: dict | None) -> dict:
    text = message.strip()
    patch: dict = {}
    lowered = text.lower()

    if text:
        patch["learning_goal"] = current.get("learning_goal") if current else ""
        if not patch["learning_goal"] or any(key in text for key in ("想学", "目标", "掌握", "希望", "准备", "人工智能", "机器学习")):
            patch["learning_goal"] = text[:180]

    if any(key in lowered for key in ("零基础", "没学过", "不会", "入门")):
        patch["knowledge_level"] = "零基础或入门水平"
    elif any(key in lowered for key in ("基础", "学过", "了解", "会一点")):
        patch["knowledge_level"] = "有基础，需要系统梳理"
    elif any(key in lowered for key in ("提高", "进阶", "项目", "竞赛")):
        patch["knowledge_level"] = "有一定基础，适合进阶实践"

    weaknesses = []
    for label in ("数学", "编程", "算法", "英语", "概率", "线性代数", "Python"):
        if label.lower() in lowered or label in text:
            if any(key in text for key in ("薄弱", "不会", "困难", "差", "弱")):
                weaknesses.append(label)
    if weaknesses:
        patch["weakness"] = weaknesses

    interests = []
    for label in ("人工智能", "机器学习", "深度学习", "数据结构", "算法", "蓝桥杯", "项目实践", "PPT"):
        if label.lower() in lowered or label in text:
            interests.append(label)
    if interests:
        patch["interest"] = interests

    if any(key in text for key in ("图", "图解", "可视化", "例子", "案例")):
        patch["cognitive_style"] = "图解 + 案例驱动"
    elif any(key in text for key in ("公式", "推导", "严谨")):
        patch["cognitive_style"] = "公式推导型"
    elif any(key in text for key in ("做题", "练习", "刷题")):
        patch["cognitive_style"] = "练习反馈型"

    time_match = re.search(r"(\d+)\s*(小时|分钟|h|min|天|周)", text, re.I)
    if time_match:
        patch["pace_preference"] = f"每次约 {time_match.group(1)}{time_match.group(2)}"
    elif any(key in text for key in ("每天", "一周", "周末", "晚上")):
        patch["pace_preference"] = text[:120]

    learning_history = _safe_list(current.get("learning_history") if current else [])
    if any(key in text for key in ("学过", "做过", "看过", "课程", "项目", "比赛")):
        learning_history.append(text[:120])
        patch["learning_history"] = learning_history[-5:]

    if "做题" in text or "测试" in text or "测评" in text:
        patch["assessment_preference"] = "通过阶段测评和练习题验证掌握程度"
    if "视频" in text or "讲义" in text or "ppt" in lowered or "PPT" in text:
        patch["resource_preference"] = text[:120]

    if course.goal and not patch.get("learning_goal"):
        patch["learning_goal"] = course.goal
    return {key: value for key, value in patch.items() if value not in ("", [], None)}


def _dimension_values(profile: dict | None):
    profile = profile or {}
    memory = profile.get("memory_strength") if isinstance(profile.get("memory_strength"), dict) else {}
    return {
        "learning_goal": _as_text(profile.get("learning_goal")),
        "knowledge_level": _as_text(profile.get("knowledge_level")),
        "learning_history": _safe_list(profile.get("learning_history")),
        "weakness": _safe_list(profile.get("weakness")),
        "interest": _safe_list(profile.get("interest")),
        "cognitive_style": _as_text(profile.get("cognitive_style")),
        "pace_preference": _as_text(profile.get("pace_preference")),
        "available_time": _as_text(profile.get("available_time") or memory.get("available_time") or profile.get("pace_preference")),
        "assessment_preference": _as_text(profile.get("assessment_preference") or memory.get("assessment_preference")),
        "resource_preference": _as_text(profile.get("resource_preference") or memory.get("resource_preference")),
    }


def _completion(profile: dict | None):
    values = _dimension_values(profile)
    filled = []
    missing = []
    for key, label in DIMENSIONS:
        value = values.get(key)
        has_value = bool(value) if not isinstance(value, list) else len(value) > 0
        (filled if has_value else missing).append({"key": key, "label": label, "value": value})
    rate = max(float(profile.get("completeness") or 0) if profile else 0, len(filled) / len(DIMENSIONS))
    return min(1.0, rate), missing, filled


def _assistant_reply(profile: dict, missing: list, ready: bool) -> str:
    goal = profile.get("learning_goal") or "这门课"
    if ready:
        return f"画像信息已经足够，我可以基于「{goal}」为你生成学习路径。请先检查右侧画像摘要，确认后再开始。"
    if missing:
        labels = "、".join(item["label"] for item in missing[:3])
        return f"我已经更新了你的课程画像。为了让路径更贴合你，还想补充了解：{labels}。"
    return "我已经记录了这些信息，可以继续补充你的目标、基础和偏好。"


def _merge_profile(current: dict | None, patch: dict, completion: float, history: list):
    current = current or {}
    merged = {**current}
    for key, value in patch.items():
        if key in {"weakness", "interest", "learning_history"}:
            existing = _safe_list(merged.get(key))
            incoming = _safe_list(value)
            merged[key] = list(dict.fromkeys([*existing, *incoming]))[-8:]
        elif key in {"available_time", "assessment_preference", "resource_preference"}:
            extras = merged.get("memory_strength") if isinstance(merged.get("memory_strength"), dict) else {}
            extras[key] = value
            merged["memory_strength"] = extras
        else:
            merged[key] = value
    merged["completeness"] = completion
    merged["chat_history"] = history
    return merged


@router.get("/courses/{course_id}/profile")
async def get_course_profile(course_id: str, user=Depends(require_user), db: Session = Depends(get_db)):
    course = _course_for_user(db, user, course_id)
    profile = profile_service.get_profile(db, course.student_id)
    from services.course_profile_conversation_service import build_profile_state
    return ok(build_profile_state(course, profile))


@router.get("/courses/{course_id}/profile/conversations/{conversation_id}/state")
async def get_course_profile_conversation_state(
    course_id: str,
    conversation_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    course = _course_for_user(db, user, course_id)
    from deps import profile_agent
    from services.course_profile_conversation_service import (
        CourseProfileConversationService,
        build_profile_state,
    )

    svc = CourseProfileConversationService(profile_agent, profile_service)
    messages = svc.get_messages(
        db,
        user=user,
        course_id=course_id,
        conversation_id=conversation_id,
    )
    latest_agent_run = None
    for message in reversed(messages):
        if message.get("role") == "assistant" and message.get("agent_run"):
            latest_agent_run = message.get("agent_run")
            break
    profile = profile_service.get_profile(db, course.student_id)
    state = build_profile_state(course, profile, messages=messages, agent_run=latest_agent_run)
    state["conversation"] = {"conversation_id": conversation_id}
    return ok(state)


@router.post("/courses/{course_id}/profile/conversations/{conversation_id}/messages")
async def send_course_profile_message(
    course_id: str,
    conversation_id: str,
    request: CourseProfileMessageRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """课程画像对话 —— 委托给 CourseProfileConversationService → ProfileAgent.build_profile_v2() → DeepSeek。

    旧关键字匹配 _infer_patch / _assistant_reply 已不再作为主流程，
    仅保留为 ProfileAgent 内部的 keyword_fallback 降级路径。
    """
    from services.course_profile_conversation_service import CourseProfileConversationService
    from deps import profile_agent

    svc = CourseProfileConversationService(profile_agent, profile_service)
    result = await svc.process_message(
        db=db,
        user=user,
        course_id=course_id,
        conversation_id=conversation_id or request.conversation_id or str(uuid.uuid4()),
        message=request.message,
        client_message_id=request.client_message_id,
        history=request.history,
        current_profile=request.current_profile,
    )

    return ok({
        "message_id": result.message_id,
        "client_message_id": result.client_message_id,
        "conversation_id": result.conversation_id,
        "assistant_message": result.assistant_message,
        "profile": result.profile,
        "profile_patch": result.profile_patch,
        "profile_completion_rate": result.profile_completion_rate,
        "completion_rate": result.profile_completion_rate,
        "dimensions": result.dimensions,
        "required_dimensions_complete": result.required_dimensions_complete,
        "missing_required_dimensions": result.missing_required_dimensions,
        "missing_optional_dimensions": result.missing_optional_dimensions,
        "missing_dimensions": result.missing_dimensions,
        "next_questions": result.next_questions,
        "can_confirm": result.can_confirm,
        "ready_for_confirmation": result.ready_for_confirmation,
        "ready_for_path_generation": result.ready_for_confirmation,
        "sources": result.sources,
        "agent_run": result.agent_run.model_dump() if result.agent_run else None,
    })


@router.put("/courses/{course_id}/profile")
async def update_course_profile(
    course_id: str,
    request: CourseProfileUpdateRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    course = _course_for_user(db, user, course_id)
    current = profile_service.get_profile(db, course.student_id) or {}
    provisional = _merge_profile(current, request.profile_patch, 0, [])
    completion, _, _ = _completion(provisional)
    profile = _merge_profile(current, request.profile_patch, completion, [])
    profile_service.save_profile(db, course.student_id, profile, increment_version=True)
    saved = profile_service.get_profile(db, course.student_id)
    from services.course_profile_conversation_service import build_profile_state
    state = build_profile_state(course, saved)
    state["profile_patch"] = request.profile_patch
    return ok(state)
