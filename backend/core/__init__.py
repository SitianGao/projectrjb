"""
core —— 多智能体系统公共基础设施。

提供:
- AgentContext: 统一 Agent 输入上下文
- 统一错误类型
- KnowledgeService: 课程作用域知识库检索
"""

from .agent_context import AgentContext
from .errors import (
    AgentError,
    AgentOutputInvalid,
    CourseAccessDenied,
    CourseContextMissing,
    CourseKnowledgeBaseNotFound,
    CourseNotFound,
    CourseScopeMismatch,
    EvaluationDataInsufficient,
    LLMProviderError,
    LLMTimeout,
    PathAdjustmentFailed,
    PathGenerationFailed,
    ResourceSchemaInvalid,
)
from .knowledge_service import KnowledgeService, knowledge_service

__all__ = [
    "AgentContext",
    "AgentError",
    "AgentOutputInvalid",
    "CourseAccessDenied",
    "CourseContextMissing",
    "CourseKnowledgeBaseNotFound",
    "CourseNotFound",
    "CourseScopeMismatch",
    "EvaluationDataInsufficient",
    "KnowledgeService",
    "LLMProviderError",
    "LLMTimeout",
    "PathAdjustmentFailed",
    "PathGenerationFailed",
    "ResourceSchemaInvalid",
    "knowledge_service",
]
