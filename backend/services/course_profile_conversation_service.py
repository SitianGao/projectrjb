"""
课程画像对话服务 —— 统一 ProfileAgent + LLM 的画像构建入口。

职责：
1. 加载 / 创建会话
2. 加载课程画像草稿
3. 调用 ProfileAgent.build_profile_v2()
4. 保存画像 + 对话
5. 返回结构化结果（含 agent_run 元数据）
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.agent_context import AgentContext
from agents.schemas import ProfileOutput, CourseProfile
from models.auth import Course
from models.student import CourseProfileConversationMessage

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 响应模型
# ═══════════════════════════════════════════════════════════════

class AgentRunMeta(BaseModel):
    run_id: str = ""
    agent_name: str = "ProfileAgent"
    provider: str = ""
    model: str = ""
    status: str = "completed"  # completed | failed | fallback
    fallback_used: bool = False
    fallback_type: Optional[str] = None
    fallback_reason: Optional[str] = None
    duration_ms: int = 0


class ConversationMessageResult(BaseModel):
    message_id: str = ""
    client_message_id: str = ""
    conversation_id: str = ""
    assistant_message: dict | None = None
    profile: dict | None = None
    profile_patch: dict | None = None
    profile_completion_rate: float = 0.0
    required_dimensions_complete: bool = False
    missing_required_dimensions: list[dict] = []
    missing_optional_dimensions: list[dict] = []
    missing_dimensions: list[dict] = []
    dimensions: list[dict] = []
    next_questions: list[str] = []
    can_confirm: bool = False
    ready_for_confirmation: bool = False
    sources: list[str] = []
    agent_run: AgentRunMeta | None = None


# ═══════════════════════════════════════════════════════════════
# 服务
# ═══════════════════════════════════════════════════════════════

DIMENSIONS = [
    ("learning_goal", "学习目标", True, "AI 将继续了解你希望最终完成什么"),
    ("knowledge_foundation", "知识基础", True, "AI 将继续判断你的编程、数学或课程基础"),
    ("learning_history", "学习经历", False, "AI 将继续提炼你的学习或项目经历"),
    ("weak_points", "薄弱知识点", True, "AI 将继续确认你最容易卡住的知识点"),
    ("interest_directions", "兴趣方向", False, "AI 将继续了解你感兴趣的应用方向"),
    ("cognitive_style", "认知或理解偏好", True, "AI 将继续了解你更偏好图示、案例、推导还是实践"),
    ("preferred_resources", "资源偏好", True, "AI 将继续询问你更喜欢图文、代码、视频还是互动实验"),
    ("assessment_preference", "测评偏好", False, "AI 将继续了解你更喜欢小测、项目还是阶段测评"),
    ("session_duration_minutes", "单次学习时长", False, "AI 将继续确认你每次适合学习多久"),
    ("sessions_per_week", "每周学习频率", False, "AI 将继续确认你每周大约学习几次"),
    ("weekly_available_hours", "每周可投入时间", False, "AI 将继续确认你每周能投入多少小时"),
    ("target_duration_weeks", "目标学习周期", True, "AI 将继续确认你希望几周内完成目标"),
    ("preferred_study_time", "偏好学习时间", False, "AI 将继续确认你通常适合什么时候学习"),
]

# 核心必填维度 key，用于确定性计算完成度
REQUIRED_DIMENSION_KEYS = [key for key, _label, required, _hint in DIMENSIONS if required]


def _generate_followup_question(profile: dict, first_missing: dict, model_questions: list[str]) -> str:
    """根据第一个缺失维度生成自然追问，优先使用模型提供的合理问题。"""
    if model_questions:
        return model_questions[0]
    hint = first_missing.get("hint", "")
    label = first_missing.get("label", "")
    if hint:
        return hint
    return f"我还想了解更多关于你的{label}，可以介绍一下吗？"


class CourseProfileConversationService:
    """课程画像对话服务 —— 唯一画像入口。

    所有课程级画像对话（包括 /api/courses/{id}/profile/conversations/...）
    和旧接口 /api/profile/chat 都应委托给本服务。
    """

    def __init__(self, profile_agent, profile_service):
        self.agent = profile_agent
        self.profile_service = profile_service

    async def process_message(
        self,
        db: Session,
        *,
        user,
        course_id: str,
        conversation_id: str,
        message: str,
        client_message_id: str | None = None,
        history: list[dict] | None = None,
        current_profile: dict | None = None,
    ) -> ConversationMessageResult:
        """处理用户画像对话消息 —— 主流程。"""
        started_at = time.monotonic()
        client_message_id = client_message_id or str(uuid.uuid4())

        existing = (
            db.query(CourseProfileConversationMessage)
            .filter_by(
                conversation_id=conversation_id,
                client_message_id=client_message_id,
                user_id=str(user.id),
                course_id=course_id,
            )
            .first()
        )
        if existing and existing.response_json:
            return ConversationMessageResult.model_validate(json.loads(existing.response_json))

        run_meta = AgentRunMeta(
            run_id=str(uuid.uuid4())[:8],
            agent_name="ProfileAgent",
            status="completed",
        )

        # 1. 解析 provider 信息
        llm = getattr(self.agent, "llm", None)
        primary = getattr(llm, "primary", "") or __import__("os").getenv("LLM_PRIMARY", "deepseek")
        run_meta.provider = primary
        run_meta.model = (
            __import__("os").getenv("DEEPSEEK_MODEL", "deepseek-chat")
            if primary == "deepseek"
            else __import__("os").getenv("SPARK_MODEL", "4.0Ultra")
        )

        # 2. 构建 AgentContext
        context = AgentContext(
            user_id=str(user.id),
            course_id=course_id,
            session_id=conversation_id,
        )

        # 3. 加载当前画像
        if current_profile is None:
            course = db.query(Course).filter_by(id=course_id, user_id=str(user.id)).first()
            if course:
                current_profile = self.profile_service.get_profile(db, course.student_id)
        else:
            course = db.query(Course).filter_by(id=course_id, user_id=str(user.id)).first()
        if not course:
            raise ValueError("课程不存在或不属于当前用户")

        # 4. 准备历史
        stored_history = self.get_messages(db, user=user, course_id=course_id, conversation_id=conversation_id)
        source_history = stored_history or history or []
        history_list = [
            f"{'user' if h.get('role') == 'user' else 'assistant'}: {h.get('content', '')}"
            for h in source_history[-20:]
            if h.get("content")
        ]

        # 5. 调用 ProfileAgent
        try:
            result: ProfileOutput = await self.agent.build_profile_v2(
                context=context,
                message=message,
                history=history_list,
                current_profile=current_profile,
            )
            normalizer = getattr(self.agent, "_normalize_profile_output", None)
            if callable(normalizer):
                result = normalizer(context, result, current_profile)
            usage = getattr(getattr(self.agent, "llm", None), "last_usage", None)
            if usage:
                run_meta.provider = usage.provider or run_meta.provider
                run_meta.model = usage.model or run_meta.model
            run_meta.status = "completed"
            run_meta.fallback_used = False
            run_meta.duration_ms = int((time.monotonic() - started_at) * 1000)

        except Exception as e:
            logger.exception("ProfileAgent LLM 调用失败: %s", e)
            # 降级：关键字规则
            try:
                from config import LLM_STRICT_MODE
            except ModuleNotFoundError:
                LLM_STRICT_MODE = False

            if LLM_STRICT_MODE:
                raise

            logger.warning("ProfileAgent LLM 失败，使用关键字降级")
            fallback_data = self.agent._keyword_fallback(
                str(user.id), message, history_list or [], current_profile,
            )
            result = self.agent._legacy_dict_to_profile_output(context, fallback_data)
            result.sources = ["keyword_fallback"]
            run_meta.status = "fallback"
            run_meta.fallback_used = True
            run_meta.fallback_type = "keyword"
            run_meta.fallback_reason = str(e)[:200]
            run_meta.duration_ms = int((time.monotonic() - started_at) * 1000)

        # 6. 确定性计算完整度（不信任 LLM 返回的 completeness）
        profile_dict = result.profile.model_dump() if hasattr(result.profile, "model_dump") else result.profile
        dimension_state = build_dimension_state(profile_dict)
        missing_required = [item for item in dimension_state if item["required"] and not item["filled"]]
        missing_optional = [item for item in dimension_state if not item["required"] and not item["filled"]]
        completed_required = len(REQUIRED_DIMENSION_KEYS) - len(missing_required)
        completion_rate = round(completed_required / len(REQUIRED_DIMENSION_KEYS), 2) if REQUIRED_DIMENSION_KEYS else 0.0
        can_confirm = completion_rate >= 0.75 and len(missing_required) <= 1

        # 7. 覆盖 LLM 的 assistant_reply（如果模型说"画像完整"但后端判断不完整）
        reply = result.assistant_reply or ""
        if not can_confirm and any(kw in reply for kw in ("足够", "可以生成", "画像完整", "已经足够", "已足够", "确认画像", "可以开始")):
            first_missing = missing_required[0] if missing_required else None
            if first_missing:
                reply = _generate_followup_question(profile_dict, first_missing, list(result.next_questions))
            else:
                reply = "我已经记录了这些信息。还需要补充一些关键信息才能为你生成学习路径。"
            logger.info("Overrode LLM reply: model claimed ready but can_confirm=False")

        # 8. 生成 patch（与旧画像对比）
        old_profile = current_profile or {}
        profile_patch = result.profile_patch or _compute_patch(old_profile, profile_dict)
        if "completeness" in profile_patch:
            profile_patch["completeness"] = completion_rate

        # 8. 保存画像
        try:
            if course:
                self.profile_service.save_profile(
                    db,
                    course.student_id,
                    {
                        **profile_dict,
                        "completeness": completion_rate,
                        "confidence": result.confidence,
                        "missing_dimensions": [item["label"] for item in missing_required + missing_optional],
                        "next_questions": list(result.next_questions),
                        "can_start_journey": can_confirm,
                    },
                    increment_version=True,
                )
        except Exception as e:
            logger.exception("保存课程画像失败: %s", e)

        # 9. 构建回复（优先使用覆盖后的 reply）
        assistant_content = reply or _build_reply(profile_dict, [item["label"] for item in missing_required], can_confirm)
        assistant_message = {
            "role": "assistant",
            "content": assistant_content,
            "agent_run": run_meta.model_dump(),
        }

        record = CourseProfileConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id or str(uuid.uuid4()),
            client_message_id=client_message_id,
            user_id=str(user.id),
            course_id=course_id,
            role="user",
            content=message,
            assistant_content=assistant_message["content"],
            agent_run_json=json.dumps(run_meta.model_dump(), ensure_ascii=False),
        )
        response = ConversationMessageResult(
            message_id=record.id,
            client_message_id=client_message_id,
            conversation_id=conversation_id or str(uuid.uuid4()),
            assistant_message=assistant_message,
            profile=profile_dict,
            profile_patch=profile_patch,
            profile_completion_rate=completion_rate,
            required_dimensions_complete=not missing_required,
            missing_required_dimensions=missing_required,
            missing_optional_dimensions=missing_optional,
            missing_dimensions=missing_required + missing_optional,
            dimensions=dimension_state,
            next_questions=list(result.next_questions),
            can_confirm=can_confirm,
            ready_for_confirmation=can_confirm,
            sources=list(result.sources),
            agent_run=run_meta,
        )
        record.response_json = response.model_dump_json()
        db.add(record)
        db.commit()
        return response

    def get_messages(self, db: Session, *, user, course_id: str, conversation_id: str) -> list[dict]:
        rows = (
            db.query(CourseProfileConversationMessage)
            .filter_by(user_id=str(user.id), course_id=course_id, conversation_id=conversation_id)
            .order_by(CourseProfileConversationMessage.created_at.asc())
            .all()
        )
        messages: list[dict] = []
        for row in rows:
            messages.append({
                "id": row.id,
                "client_message_id": row.client_message_id,
                "role": "user",
                "content": row.content,
            })
            if row.assistant_content:
                agent_run = _safe_json_loads(row.agent_run_json, None)
                messages.append({
                    "id": f"{row.id}:assistant",
                    "client_message_id": row.client_message_id,
                    "role": "assistant",
                    "content": row.assistant_content,
                    "agent_run": agent_run,
                })
        return messages


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def build_dimension_state(profile: dict | None) -> list[dict]:
    """Return one canonical dimension view for API and frontend."""
    profile = profile or {}
    dimensions = []
    for key, label, required, hint in DIMENSIONS:
        value = _dimension_value(profile, key)
        filled = _has_dimension_value(key, value)
        dimensions.append({
            "key": key,
            "label": label,
            "value": value if filled else "",
            "filled": filled,
            "required": required,
            "hint": hint,
        })
    return dimensions


def _compute_patch(old: dict, new: dict) -> dict:
    """计算增量 patch —— 只返回变化的部分。"""
    patch = {}
    for key, label, _required, _hint in DIMENSIONS:
        old_val = old.get(key) if isinstance(old, dict) else None
        if old_val is None and key in {"preferred_resources", "assessment_preference", "session_duration_minutes", "sessions_per_week", "weekly_available_hours", "target_duration_weeks", "preferred_study_time"}:
            memory = old.get("memory_strength") if isinstance(old, dict) and isinstance(old.get("memory_strength"), dict) else {}
            old_val = memory.get(key)
        new_val = new.get(key) if isinstance(new, dict) else None
        if new_val and new_val != old_val:
            patch[key] = new_val
    # Always include completeness
    patch["completeness"] = new.get("completeness", 0.0) if isinstance(new, dict) else 0.0
    return patch


def _build_reply(profile: dict, missing: list[str], ready: bool) -> str:
    """生成 AI 回复（非 LLM 降级时使用模板）。"""
    goal = profile.get("learning_goal", "这门课") if isinstance(profile, dict) else "这门课"
    if ready:
        return f"画像信息已经足够，我可以基于「{goal}」为你生成学习路径。请先检查右侧画像摘要，确认后再开始。"
    if missing:
        labels = "、".join(missing[:3])
        return f"我已经更新了你的课程画像。为了让路径更贴合你，还想补充了解：{labels}。"
    return "我已经记录了这些信息，可以继续补充你的目标、基础和偏好。"


def _dimension_value(profile: dict, key: str):
    memory = profile.get("memory_strength") if isinstance(profile.get("memory_strength"), dict) else {}
    value = profile.get(key)
    if value in (None, "", [], {}):
        value = memory.get(key)
    if key == "knowledge_foundation" and not value:
        value = profile.get("knowledge_level")
    if key == "weak_points" and not value:
        value = profile.get("weakness")
    if key == "interest_directions" and not value:
        value = profile.get("interest")
    return _format_dimension_value(key, value)


def _format_dimension_value(key: str, value):
    if value is None:
        return ""
    if key == "knowledge_foundation" and isinstance(value, dict):
        labels = {
            "python": "Python",
            "linear_algebra": "线性代数",
            "calculus": "微积分",
            "machine_learning": "机器学习",
            "deep_learning": "深度学习",
        }
        return "、".join(
            f"{labels.get(k, k)} {v}/100"
            for k, v in value.items()
            if v not in (None, "")
        )
    if key == "weak_points" and isinstance(value, list):
        names = []
        for item in value:
            if isinstance(item, dict):
                names.append(item.get("name") or item.get("knowledge_point_id"))
            else:
                names.append(str(item))
        return [name for name in names if name]
    if key == "session_duration_minutes" and value:
        return f"约 {value} 分钟"
    if key == "sessions_per_week" and value:
        return f"每周 {value} 次"
    if key == "weekly_available_hours" and value:
        return f"约 {value} 小时"
    if key == "target_duration_weeks" and value:
        return f"{value} 周"
    return value


def _has_dimension_value(key: str, value) -> bool:
    if value in (None, "", [], {}):
        return False
    if key == "knowledge_foundation":
        if isinstance(value, dict):
            # All-default values (50) mean the LLM didn't actually extract knowledge
            if all(v == 50 for v in value.values()):
                return False
            # Any non-default value counts
            return any(v != 50 for v in value.values())
        if isinstance(value, str):
            if not value.strip():
                return False
            if all(token in value for token in ["Python 50/100", "线性代数 50/100", "微积分 50/100"]):
                return False
        return bool(value)
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, list) and len(value) == 0:
        return False
    if isinstance(value, dict) and len(value) == 0:
        return False
    return True


def build_profile_state(course: Course, profile: dict | None, messages: list[dict] | None = None, agent_run: dict | None = None) -> dict:
    dimensions = build_dimension_state(profile)
    missing_required = [item for item in dimensions if item["required"] and not item["filled"]]
    missing_optional = [item for item in dimensions if not item["required"] and not item["filled"]]
    completed_required = len([item for item in dimensions if item["required"] and item["filled"]])
    completeness = round(completed_required / len(REQUIRED_DIMENSION_KEYS), 2) if REQUIRED_DIMENSION_KEYS else 0.0
    can_confirm = completeness >= 0.75 and len(missing_required) <= 1
    restored_messages = messages or []
    if not restored_messages:
        restored_messages = [{
            "id": "profile-opening",
            "role": "assistant",
            "content": "你好，我会通过几轮简单对话了解你的课程基础、学习目标和偏好。你可以先介绍一下为什么想学习这门课程，以及希望最终完成什么。",
        }]
    return {
        "course": {"id": course.id, "title": course.title, "goal": course.goal or "", "student_id": course.student_id},
        "profile": profile,
        "completion_rate": completeness,
        "profile_completion_rate": completeness,
        "dimensions": dimensions,
        "filled_dimensions": [item for item in dimensions if item["filled"]],
        "missing_dimensions": missing_required + missing_optional,
        "missing_required_dimensions": missing_required,
        "missing_optional_dimensions": missing_optional,
        "required_dimensions_complete": not missing_required,
        "can_confirm": can_confirm,
        "ready_for_confirmation": can_confirm,
        "ready_for_path_generation": can_confirm,
        "next_questions": (profile or {}).get("next_questions") or [],
        "messages": restored_messages,
        "agent_run": agent_run,
    }


def _safe_json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default
