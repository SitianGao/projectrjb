"""
ProfileService —— 学生画像业务逻辑层

职责：
- 管理 ProfileAgent 生命周期
- 构建/更新学生画像（同步 LLM + 持久化）
- 数据库读写（StudentProfile 表）
- 多轮对话上下文管理

API 层 → Service 层 → Agent 层 → LLM 客户端
"""

import json
import logging
import uuid
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

from sqlalchemy.orm import Session

from agents.profile_agent import ProfileAgent
from models.student import Student, StudentProfile

logger = logging.getLogger(__name__)


class ProfileService:
    """
    学生画像服务 —— API 和 Agent 之间的桥梁。

    用法：
        from agents.llm_client import create_llm_client
        llm = create_llm_client()
        service = ProfileService(llm)

        # 构建画像
        result = await service.build_or_update_profile(
            db, student_id="stu_001", message="你好，我是...",
        )
    """

    # 多轮对话上下文：student_id -> [message, ...]
    # 生产环境可替换为 Redis
    _chat_histories: Dict[str, List[str]] = {}

    def __init__(self, llm_client):
        """
        Args:
            llm_client: LLM 客户端实例（实现 chat_stream 协议）
        """
        self.agent = ProfileAgent(llm_client)
        self.llm_client = llm_client

    # ---- 画像构建 ----

    async def build_or_update_profile(
        self,
        db: Session,
        student_id: str,
        message: str,
        current_profile: Optional[Dict] = None,
    ) -> Dict:
        """
        单轮画像构建/更新（非流式）。

        流程：
        1. 获取聊天历史
        2. 若无 current_profile，尝试从 DB 加载已有画像
        3. 调用 ProfileAgent.build_profile()
        4. 追加消息到历史
        5. 持久化画像到 DB

        Args:
            db: 数据库会话
            student_id: 学生唯一标识
            message: 当前用户消息
            current_profile: 已有画像（优先使用，否则从 DB 加载）

        Returns:
            dict: 完整画像结果 {student_id, profile, completeness, confidence, ...}
        """
        history = self._get_history(student_id)

        # 如果没有明确传入 current_profile，从 DB 加载最新画像
        if current_profile is None:
            current_profile = self._load_latest_profile(db, student_id)

        logger.info(
            "ProfileService: 开始构建画像 student=%s, history_len=%s, has_prior=%s",
            student_id, len(history), current_profile is not None,
        )

        result = await self.agent.build_profile(
            student_id=student_id,
            message=message,
            history=history,
            current_profile=current_profile,
        )

        # 保存消息到历史
        self._append_to_history(student_id, message)

        # 持久化到数据库
        self._save_profile(db, result)

        logger.info(
            "ProfileService: 画像构建完成 student=%s, completeness=%.2f, confidence=%.2f",
            student_id, result.get("completeness", 0), result.get("confidence", 0),
        )

        return result

    # ---- 流式对话 ----

    async def chat_stream(
        self,
        db: Session,
        student_id: str,
        message: str,
        current_profile: Optional[Dict] = None,
    ) -> AsyncIterator[str]:
        """
        流式对话画像构建 —— 供 SSE 端点使用。

        产出 SSE 事件行：
        - data: {"type":"chat","content":"..."}
        - data: {"type":"profile_update","profile":{...}}
        - data: {"type":"done"}

        Args:
            db: 数据库会话
            student_id: 学生标识
            message: 当前用户消息
            current_profile: 已有画像

        Yields:
            str: SSE 格式的事件行
        """
        history = self._get_history(student_id)

        if current_profile is None:
            current_profile = self._load_latest_profile(db, student_id)

        logger.info(
            "ProfileService: 开始流式对话 student=%s, message_len=%s",
            student_id, len(message),
        )

        # 收集完整响应用于持久化
        full_chat_text = []
        profile_result = None

        async for sse_line in self.agent.chat(
            student_id=student_id,
            message=message,
            history=history,
            current_profile=current_profile,
        ):
            yield sse_line

            # 解析 SSE 行，收集数据（格式: "data: {...json...}\n\n"）
            if sse_line.startswith("data: "):
                try:
                    data = json.loads(sse_line[len("data: "):].strip())
                    if data.get("type") == "chat":
                        full_chat_text.append(data.get("content", ""))
                    elif data.get("type") == "profile_update":
                        profile_result = data.get("profile")
                except json.JSONDecodeError:
                    pass

        # 持久化
        self._append_to_history(student_id, message)
        if profile_result:
            self._save_profile(db, profile_result)
            logger.info(
                "ProfileService: 流式对话完成，画像已持久化 student=%s", student_id,
            )

    # ---- 画像查询 ----

    def get_profile(self, db: Session, student_id: str) -> Optional[Dict]:
        """
        获取学生最新画像。

        Args:
            db: 数据库会话
            student_id: 学生标识

        Returns:
            dict 或 None（学生不存在时）
        """
        stored = self._load_latest_profile(db, student_id)
        if stored is None:
            return None

        # _load_latest_profile 返回 {student_id, profile: {6维度}, completeness, ...}
        inner = stored.get("profile", stored)

        return {
            "student_id": student_id,
            "profile": {
                "knowledge_level": inner.get("knowledge_level", ""),
                "learning_goal": inner.get("learning_goal", ""),
                "cognitive_style": inner.get("cognitive_style", ""),
                "weakness": inner.get("weakness", []),
                "interest": inner.get("interest", []),
                "pace_preference": inner.get("pace_preference", "中速均衡型"),
                "learning_history": inner.get("learning_history", []),
            },
            "completeness": stored.get("completeness", 0.0),
            "confidence": stored.get("confidence", 0.0),
            "sources": stored.get("sources", []),
            "next_questions": stored.get("next_questions", []),
        }

    def update_profile(
        self,
        db: Session,
        student_id: str,
        profile_data: Dict,
    ) -> Dict:
        """
        手动更新画像（API PUT 端点使用）。

        Args:
            db: 数据库会话
            student_id: 学生标识
            profile_data: 画像数据

        Returns:
            dict: 更新后的完整画像
        """
        # 合并已有画像
        existing = self._load_latest_profile(db, student_id) or {}
        existing.update(profile_data)
        existing["student_id"] = student_id

        self._save_profile(db, existing)

        logger.info("ProfileService: 手动更新画像 student=%s", student_id)
        return self.get_profile(db, student_id)

    # ---- 历史管理 ----

    def clear_history(self, student_id: str) -> None:
        """清空学生的对话历史"""
        self._chat_histories.pop(student_id, None)
        logger.info("ProfileService: 清空对话历史 student=%s", student_id)

    def get_history(self, student_id: str) -> List[str]:
        """获取学生对话历史"""
        return list(self._get_history(student_id))

    # ---- 私有方法 ----

    def _get_history(self, student_id: str) -> List[str]:
        """获取对话历史（线程安全副本）"""
        return list(self._chat_histories.get(student_id, []))

    def _append_to_history(self, student_id: str, message: str) -> None:
        """追加消息到对话历史"""
        if student_id not in self._chat_histories:
            self._chat_histories[student_id] = []
        self._chat_histories[student_id].append(message)

    def _load_latest_profile(self, db: Session, student_id: str) -> Optional[Dict]:
        """
        从数据库加载最新版本的画像。

        Returns:
            dict 或 None（无已存储画像）
        """
        try:
            row = (
                db.query(StudentProfile)
                .filter(StudentProfile.student_id == student_id)
                .order_by(StudentProfile.version.desc())
                .first()
            )
            if row is None:
                return None

            # 将 ORM 对象转为 dict（与 ProfileAgent 输出格式对齐）
            return {
                "student_id": row.student_id,
                "profile": {
                    "knowledge_level": row.knowledge_level or "",
                    "learning_goal": row.learning_goal or "",
                    "cognitive_style": row.cognitive_style or "",
                    "weakness": self._safe_json_loads(row.weakness, []),
                    "interest": self._safe_json_loads(row.interest, []),
                    "pace_preference": self._get_pace_from_db(row),
                    "learning_history": self._safe_json_loads(row.learning_history, []),
                    "chat_history": self._safe_json_loads(row.chat_history, []),
                    "memory_strength": self._safe_json_loads(row.memory_strength, {}),
                },
                "completeness": row.completeness or 0.0,
                "confidence": 0.5,  # 从 DB 恢复时默认置信度
                "sources": [],
                "next_questions": [],
            }
        except Exception as e:
            logger.error("加载画像失败 student=%s: %s", student_id, e)
            return None

    def _save_profile(self, db: Session, result: Dict) -> None:
        """
        持久化画像到数据库。

        策略：
        - 确保 Student 记录存在
        - 每次保存创建新版本（StudentProfile version++）
        """
        try:
            student_id = result.get("student_id", "")
            if not student_id:
                logger.warning("保存画像失败: 缺少 student_id")
                return

            profile = result.get("profile", {})

            # 确保 Student 存在
            student = db.query(Student).filter(Student.id == student_id).first()
            if student is None:
                student = Student(id=student_id, nickname=student_id[:8])
                db.add(student)
                db.flush()

            # 计算新版本号
            latest_version = (
                db.query(StudentProfile)
                .filter(StudentProfile.student_id == student_id)
                .order_by(StudentProfile.version.desc())
                .first()
            )
            new_version = (latest_version.version + 1) if latest_version else 1

            # 创建新版本的画像记录
            record = StudentProfile(
                id=str(uuid.uuid4()),
                student_id=student_id,
                version=new_version,
                knowledge_level=profile.get("knowledge_level", ""),
                learning_goal=profile.get("learning_goal", ""),
                learning_history=json.dumps(
                    profile.get("learning_history", []), ensure_ascii=False
                ),
                cognitive_style=profile.get("cognitive_style", ""),
                weakness=json.dumps(
                    profile.get("weakness", []), ensure_ascii=False
                ),
                interest=json.dumps(
                    profile.get("interest", []), ensure_ascii=False
                ),
                chat_history=json.dumps(
                    # 保存最近 50 条对话历史
                    self._get_history(student_id)[-50:],
                    ensure_ascii=False,
                ),
                memory_strength=json.dumps(
                    profile.get("memory_strength", {}), ensure_ascii=False
                ),
                completeness=result.get("completeness", 0.0),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(record)
            db.commit()

            logger.debug(
                "画像已保存 student=%s version=%s completeness=%.2f",
                student_id, new_version, result.get("completeness", 0),
            )
        except Exception as e:
            db.rollback()
            logger.error("保存画像失败 student=%s: %s", student_id, e)
            raise

    @staticmethod
    def _safe_json_loads(value, default):
        """安全解析 JSON 字段（数据库 TEXT 字段存储）"""
        if value is None:
            return default
        if isinstance(value, (list, dict)):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default

    @staticmethod
    def _get_pace_from_db(row: StudentProfile) -> str:
        """
        从 DB 记录中推断 pace_preference。
        pace_preference 存储在 cognitive_style 字段的备注中，
        或通过 weakness 字段中的关键词间接推断。
        默认返回 "中速均衡型"。
        """
        # 由于 schema 中没有单独的 pace_preference 列，
        # 从 memory_strength 字段中尝试提取
        try:
            ms = json.loads(row.memory_strength) if row.memory_strength else {}
            return ms.get("pace_preference", "中速均衡型")
        except (json.JSONDecodeError, TypeError):
            return "中速均衡型"
