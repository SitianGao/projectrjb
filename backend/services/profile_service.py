"""
画像业务逻辑层 —— API 与 Agent / DB 的桥梁。

职责：
- 管理 Student + StudentProfile 的 CRUD
- 调度 ProfileAgent 进行流式/非流式画像构建
- 将 Agent 输出持久化到数据库
"""
import json
import logging
import uuid
from typing import AsyncIterator, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.student import Student, StudentProfile

logger = logging.getLogger(__name__)


class ProfileService:
    """画像业务服务"""

    def __init__(self, profile_agent, db_session_factory):
        """
        Args:
            profile_agent: ProfileAgent 实例
            db_session_factory: get_db 生成器工厂（用于 FastAPI Depends）
        """
        self.agent = profile_agent
        self.db_session_factory = db_session_factory

    # ── Student 基础操作 ──────────────────────────────────────

    def get_or_create_student(self, db: Session, student_id: str, nickname: str = "") -> Student:
        """获取已有学生，不存在则创建。"""
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            student = Student(
                id=student_id,
                nickname=nickname or f"学生_{student_id[:8]}",
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            logger.info(f"创建新学生: {student_id}")
        return student

    # ── 画像 CRUD ────────────────────────────────────────────

    def get_profile(self, db: Session, student_id: str) -> Optional[Dict]:
        """获取学生最新画像（返回 dict 供前端展示）。"""
        profile = (
            db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .order_by(StudentProfile.version.desc())
            .first()
        )
        if not profile:
            return None
        result = self._profile_to_dict(profile)
        # 旧数据中可能已经出现“新版本完整度低于历史版本”的情况。
        # 读取时也以历史最高值为准，使现有脏数据无需等待下一次对话即可恢复。
        result["completeness"] = max(
            _as_completeness(result.get("completeness")),
            self._get_highest_completeness(db, student_id),
        )
        return result

    def get_profile_history(self, db: Session, student_id: str) -> list:
        """获取学生画像历史版本列表。"""
        profiles = (
            db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .order_by(StudentProfile.version.asc())
            .all()
        )
        return [self._profile_to_dict(p) for p in profiles]

    def get_chat_history(self, db: Session, student_id: str) -> list:
        """Return the latest successful profile-chat messages."""
        latest = self._get_latest_profile_record(db, student_id)
        if not latest:
            return []
        return _safe_json_loads(latest.chat_history, [])

    def save_profile(
        self,
        db: Session,
        student_id: str,
        profile_data: Dict,
        increment_version: bool = True,
    ) -> StudentProfile:
        """保存或更新学生画像。"""
        historical_completeness = self._get_highest_completeness(db, student_id)
        latest = (
            db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .order_by(StudentProfile.version.desc())
            .first()
        )

        p = profile_data.get("profile", profile_data)

        if latest and not increment_version:
            # 原地更新
            latest.completeness = max(
                _as_completeness(latest.completeness),
                historical_completeness,
            )
            self._apply_profile_fields(latest, p, profile_data)
            db.commit()
            db.refresh(latest)
            return latest

        # 新版本：从旧版本复制已有字段，再用新数据覆盖
        new_version = (latest.version + 1) if latest else 1
        record = StudentProfile(
            id=str(uuid.uuid4()),
            student_id=student_id,
            version=new_version,
            completeness=historical_completeness,
        )
        # 先复制旧版本的所有字段（如果有）
        if latest:
            record.knowledge_level = latest.knowledge_level
            record.learning_goal = latest.learning_goal
            record.learning_history = latest.learning_history
            record.cognitive_style = latest.cognitive_style
            record.pace_preference = latest.pace_preference
            record.weakness = latest.weakness
            record.interest = latest.interest
            record.chat_history = latest.chat_history
            record.memory_strength = latest.memory_strength
            record.completeness = max(
                _as_completeness(latest.completeness),
                historical_completeness,
            )
        # 再应用新数据（部分更新：只覆盖传入的字段）
        self._apply_profile_fields(record, p, profile_data)
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(f"画像已保存: student={student_id} v{new_version}")
        return record

    # ── 对话式画像构建（SSE 流式） ───────────────────────────

    async def chat_stream(
        self,
        db: Session,
        student_id: str,
        message: str,
        history: Optional[list] = None,
        current_profile: Optional[Dict] = None,
    ) -> AsyncIterator[str]:
        """
        流式画像对话 —— 直接透传 ProfileAgent.chat() 的 SSE 事件。

        产出 SSE 事件流：
            data: {"type":"chat","content":"..."}
            data: {"type":"profile_update","profile":{...}}
            data: {"type":"done"}

        在收到 profile_update 后自动持久化到数据库。
        """
        yield f'data: {{"type":"start","message":"开始分析学习画像"}}\n\n'
        self.get_or_create_student(db, student_id)

        latest_before_chat = self._get_latest_profile_record(db, student_id)
        old_completeness = max(
            _as_completeness(
                latest_before_chat.completeness if latest_before_chat else 0.0
            ),
            self._get_highest_completeness(db, student_id),
        )

        # The model is stateless. When the client omits context, restore it from
        # the latest persisted profile so a browser refresh does not restart the
        # interview from the first question.
        effective_history = (
            _normalize_chat_history(history)
            if history is not None
            else _history_for_agent(latest_before_chat)
        )
        effective_profile = current_profile
        if effective_profile is None and latest_before_chat:
            effective_profile = self._profile_to_dict(latest_before_chat)

        full_chat = []
        profile_saved = False
        error_occurred = False

        async for event in self.agent.chat(
            student_id=student_id,
            message=message,
            history=effective_history,
            current_profile=effective_profile,
        ):
            payload = _parse_sse_payload(event)

            # 检测 profile_update 事件以便持久化
            if payload and payload.get("type") == "profile_update" and not profile_saved:
                try:
                    profile_data = payload.get("profile", {})
                    if profile_data:
                        # Completeness is accumulated knowledge and must never
                        # regress because of one unstable LLM response.
                        profile_data["completeness"] = max(
                            old_completeness,
                            _as_completeness(profile_data.get("completeness", 0.0)),
                        )
                        self.save_profile(
                            db,
                            student_id,
                            profile_data,
                            increment_version=True,
                        )
                        profile_saved = True
                        event = _format_sse_payload(payload)
                        logger.info(f"画像已自动持久化: student={student_id}")
                except (TypeError, ValueError, KeyError) as e:
                    db.rollback()
                    logger.warning(f"解析 profile_update 事件失败: {e}")

            # 收集 chat 内容用于记录
            if payload and payload.get("type") == "chat":
                content = payload.get("content", "")
                if content:
                    full_chat.append(str(content))

            if payload and payload.get("type") == "error":
                error_occurred = True

            # 透传 Agent 事件；profile_update 会携带修正后的完整度。
            yield event

        # 更新聊天历史到画像
        if profile_saved and full_chat and not error_occurred:
            try:
                latest = self._get_latest_profile_record(db, student_id)
                if latest:
                    chat_list = _safe_json_loads(latest.chat_history, [])
                    if not isinstance(chat_list, list):
                        chat_list = []
                    chat_list.append({
                        "role": "user",
                        "content": message,
                    })
                    chat_list.append({
                        "role": "assistant",
                        "content": "".join(full_chat),
                    })
                    latest.chat_history = json.dumps(chat_list, ensure_ascii=False)
                    db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"更新聊天历史失败: {e}")

    # ── 非流式画像构建（供编排器使用） ───────────────────────

    async def build_profile(
        self,
        db: Session,
        student_id: str,
        message: str,
        history: Optional[list] = None,
        current_profile: Optional[Dict] = None,
    ) -> Dict:
        """非流式画像构建，返回完整 dict 并持久化。"""
        result = await self.agent.build_profile(
            student_id=student_id,
            message=message,
            history=history,
            current_profile=current_profile,
        )
        if result and result.get("profile"):
            self.save_profile(db, student_id, result, increment_version=True)
        return result

    # ── 工具方法 ─────────────────────────────────────────────

    @staticmethod
    def _get_latest_profile_record(
        db: Session,
        student_id: str,
    ) -> Optional[StudentProfile]:
        return (
            db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .order_by(StudentProfile.version.desc())
            .first()
        )

    @staticmethod
    def _get_highest_completeness(db: Session, student_id: str) -> float:
        """返回学生全部画像版本中的最高完整度。"""
        value = (
            db.query(func.max(StudentProfile.completeness))
            .filter(StudentProfile.student_id == student_id)
            .scalar()
        )
        return _as_completeness(value)

    def _apply_profile_fields(self, record: StudentProfile, p: Dict, meta: Dict):
        """将 dict 字段写入 ORM 对象（仅更新显式传入的字段，支持部分更新）。"""
        if "knowledge_level" in p:
            record.knowledge_level = p["knowledge_level"]
        if "learning_goal" in p:
            record.learning_goal = p["learning_goal"]
        if "cognitive_style" in p:
            record.cognitive_style = p["cognitive_style"]
        if "weakness" in p:
            record.weakness = json.dumps(p["weakness"], ensure_ascii=False)
        if "interest" in p:
            record.interest = json.dumps(p["interest"], ensure_ascii=False)
        if "pace_preference" in p:
            record.pace_preference = p["pace_preference"]
        if "memory_strength" in p:
            record.memory_strength = json.dumps(p["memory_strength"], ensure_ascii=False)

        # learning_history 可能在 profile 内或 meta 中
        if "learning_history" in p or "learning_history" in meta:
            lh = p.get("learning_history") or meta.get("learning_history", [])
            if isinstance(lh, list):
                record.learning_history = json.dumps(lh, ensure_ascii=False)
            elif isinstance(lh, str):
                record.learning_history = lh
            else:
                record.learning_history = "[]"

        if "completeness" in meta or "completeness" in p:
            previous = _as_completeness(record.completeness)
            incoming = _as_completeness(
                meta.get("completeness", p.get("completeness", 0.0))
            )
            record.completeness = max(previous, incoming)

    @staticmethod
    def _profile_to_dict(profile: StudentProfile) -> Dict:
        """将 ORM 对象转为前端友好的 dict。"""
        return {
            "id": profile.id,
            "student_id": profile.student_id,
            "version": profile.version,
            "knowledge_level": profile.knowledge_level,
            "learning_goal": profile.learning_goal,
            "learning_history": _safe_json_loads(profile.learning_history, []),
            "cognitive_style": profile.cognitive_style,
            "pace_preference": profile.pace_preference or "",
            "weakness": _safe_json_loads(profile.weakness, []),
            "interest": _safe_json_loads(profile.interest, []),
            "memory_strength": _safe_json_loads(profile.memory_strength, {}),
            "completeness": profile.completeness,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        }


def _safe_json_loads(value, default):
    """安全解析 JSON 字段，失败返回默认值。"""
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def _as_completeness(value) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def _normalize_chat_history(history) -> list:
    if not isinstance(history, list):
        return []
    normalized = []
    for item in history[-20:]:
        if isinstance(item, dict):
            role = item.get("role") or "message"
            content = item.get("content")
            if content:
                normalized.append(f"{role}: {content}")
        elif item is not None:
            normalized.append(str(item))
    return normalized


def _history_for_agent(profile: Optional[StudentProfile]) -> list:
    if not profile:
        return []
    return _normalize_chat_history(_safe_json_loads(profile.chat_history, []))


def _parse_sse_payload(event: str) -> Optional[Dict]:
    if not isinstance(event, str):
        return None
    raw = event.strip()
    if raw.startswith("data:"):
        raw = raw[5:].strip()
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def _format_sse_payload(payload: Dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
