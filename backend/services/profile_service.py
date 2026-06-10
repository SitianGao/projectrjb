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
        return self._profile_to_dict(profile)

    def get_profile_history(self, db: Session, student_id: str) -> list:
        """获取学生画像历史版本列表。"""
        profiles = (
            db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .order_by(StudentProfile.version.asc())
            .all()
        )
        return [self._profile_to_dict(p) for p in profiles]

    def save_profile(
        self,
        db: Session,
        student_id: str,
        profile_data: Dict,
        increment_version: bool = True,
    ) -> StudentProfile:
        """保存或更新学生画像。"""
        latest = (
            db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .order_by(StudentProfile.version.desc())
            .first()
        )

        p = profile_data.get("profile", profile_data)

        if latest and not increment_version:
            # 原地更新
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
            record.completeness = latest.completeness
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

        full_chat = []
        profile_received = None
        error_occurred = False

        async for event in self.agent.chat(
            student_id=student_id,
            message=message,
            history=history,
            current_profile=current_profile,
        ):
            # 透传 Agent 产出的 SSE 事件
            yield event

            # 检测 profile_update 事件以便持久化
            if '"type":"profile_update"' in event:
                try:
                    # 从 SSE 行中提取 JSON
                    prefix = "data: "
                    json_str = event.strip()
                    if json_str.startswith(prefix):
                        json_str = json_str[len(prefix):]
                    payload = json.loads(json_str)
                    profile_data = payload.get("profile", {})
                    if profile_data:
                        self.save_profile(
                            db,
                            student_id,
                            profile_data,
                            increment_version=True,
                        )
                        logger.info(f"画像已自动持久化: student={student_id}")
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"解析 profile_update 事件失败: {e}")

            # 收集 chat 内容用于记录
            if '"type":"chat"' in event:
                try:
                    prefix = "data: "
                    json_str = event.strip()
                    if json_str.startswith(prefix):
                        json_str = json_str[len(prefix):]
                    payload = json.loads(json_str)
                    content = payload.get("content", "")
                    if content:
                        full_chat.append(content)
                except json.JSONDecodeError:
                    pass

            if '"type":"error"' in event:
                error_occurred = True

        # 更新聊天历史到画像
        if full_chat and not error_occurred:
            try:
                latest = (
                    db.query(StudentProfile)
                    .filter(StudentProfile.student_id == student_id)
                    .order_by(StudentProfile.version.desc())
                    .first()
                )
                if latest:
                    chat_list = []
                    if latest.chat_history:
                        try:
                            chat_list = json.loads(latest.chat_history)
                        except json.JSONDecodeError:
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
            record.completeness = meta.get("completeness", p.get("completeness", 0.0))

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
