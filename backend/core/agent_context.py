"""
统一 AgentContext —— 所有业务 Agent 的标准化输入上下文。

所有 Agent 的公开方法必须以 AgentContext 作为第一个参数。
内部统一使用 snake_case；API 层负责 camelCase 转换。

设计依据：赛题要求多智能体协作，上下文必须包含完整的课程和知识点信息。
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AgentContext(BaseModel):
    """多 Agent 协同的统一上下文。

    每个 Agent 调用时都必须提供完整的上下文信息。
    不允许部分 Agent 使用 user_id、部分使用 courseId 等不一致字段。
    """

    # ── 核心标识 ──
    user_id: str = Field(..., description="用户唯一标识")
    course_id: str = Field(..., description="课程唯一标识")

    # ── 学习位置 ──
    stage_id: Optional[str] = Field(default=None, description="当前学习阶段 ID")
    task_id: Optional[str] = Field(default=None, description="当前学习任务 ID")

    # ── 知识点 ──
    knowledge_point_ids: list[str] = Field(
        default_factory=list,
        description="关联知识点 ID 列表",
    )

    # ── 会话 ──
    session_id: Optional[str] = Field(default=None, description="会话唯一标识（用于追踪多轮对话）")

    # ── 知识库绑定 ──
    knowledge_base_id: Optional[str] = Field(
        default=None,
        description="课程绑定的知识库 ID；由 KnowledgeService 根据 course_id 解析",
    )
    vector_collection: Optional[str] = Field(
        default=None,
        description="课程绑定的向量集合名称；由 KnowledgeService 根据 course_id 解析",
    )

    # ── 本地化 ──
    locale: str = Field(default="zh-CN", description="语言/地区（默认简体中文）")

    class Config:
        frozen = False  # 允许 Agent 在执行过程中补充字段
        extra = "forbid"  # 禁止未声明的字段，强制统一合同
