"""
统一错误类型 —— 所有 Agent 和 API 层的标准错误格式。

前端需要收到统一的结构化错误:
    { "code": "ERROR_CODE", "message": "...", "retryable": true, "details": {} }

不要把 Python 异常堆栈直接返回给前端。
"""

from __future__ import annotations


class AgentError(Exception):
    """Agent 层统一异常基类。

    所有 Agent 抛出的异常都应使用此类型或其子类，
    确保前端能收到结构化的错误信息。
    """

    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "details": self.details,
        }


# ── Agent 输出错误 ──

class AgentOutputInvalid(AgentError):
    """Agent 输出的 JSON 无法解析或 Schema 校验失败。"""

    def __init__(self, agent_name: str, reason: str, raw_output: str = ""):
        super().__init__(
            code="AGENT_OUTPUT_INVALID",
            message=f"{agent_name} 输出格式无效: {reason}",
            retryable=True,
            details={"agent": agent_name, "reason": reason},
        )


# ── 课程上下文错误 ──

class CourseContextMissing(AgentError):
    """调用 Agent 时缺少 course_id。"""

    def __init__(self, agent_name: str):
        super().__init__(
            code="COURSE_CONTEXT_MISSING",
            message=f"调用 {agent_name} 时未提供 course_id，所有 Agent 必须绑定课程上下文",
            retryable=False,
            details={"agent": agent_name},
        )


class CourseNotFound(AgentError):
    """课程不存在。"""

    def __init__(self, course_id: str):
        super().__init__(
            code="COURSE_NOT_FOUND",
            message=f"课程 {course_id} 不存在",
            retryable=False,
            details={"course_id": course_id},
        )


class CourseAccessDenied(AgentError):
    """当前用户无权访问该课程。"""

    def __init__(self, user_id: str, course_id: str):
        super().__init__(
            code="COURSE_ACCESS_DENIED",
            message=f"用户 {user_id} 无权访问课程 {course_id}",
            retryable=False,
            details={"user_id": user_id, "course_id": course_id},
        )


class CourseKnowledgeBaseNotFound(AgentError):
    """课程未绑定知识库。"""

    def __init__(self, course_id: str):
        super().__init__(
            code="COURSE_KNOWLEDGE_BASE_NOT_FOUND",
            message=f"课程 {course_id} 未绑定知识库，无法检索相关知识",
            retryable=False,
            details={"course_id": course_id},
        )


class CourseScopeMismatch(AgentError):
    """数据 course_id 不匹配当前上下文。"""

    def __init__(self, expected: str, actual: str, resource: str = ""):
        super().__init__(
            code="COURSE_SCOPE_MISMATCH",
            message=f"数据范围不匹配：期望课程 {expected}，实际课程 {actual}（{resource}）",
            retryable=False,
            details={"expected_course_id": expected, "actual_course_id": actual, "resource": resource},
        )


# ── 资源错误 ──

class ResourceSchemaInvalid(AgentError):
    """资源 Schema 校验失败。"""

    def __init__(self, resource_type: str, reason: str):
        super().__init__(
            code="RESOURCE_SCHEMA_INVALID",
            message=f"类型「{resource_type}」的资源 Schema 校验失败: {reason}",
            retryable=True,
            details={"resource_type": resource_type, "reason": reason},
        )


# ── 评估错误 ──

class EvaluationDataInsufficient(AgentError):
    """评估数据不足。"""

    def __init__(self, reason: str = "学习记录不足，无法生成有效评估"):
        super().__init__(
            code="EVALUATION_DATA_INSUFFICIENT",
            message=reason,
            retryable=False,
            details={"reason": reason},
        )


# ── 路径错误 ──

class PathGenerationFailed(AgentError):
    """路径生成失败。"""

    def __init__(self, reason: str):
        super().__init__(
            code="PATH_GENERATION_FAILED",
            message=f"学习路径生成失败: {reason}",
            retryable=True,
            details={"reason": reason},
        )


class PathAdjustmentFailed(AgentError):
    """路径调整失败。"""

    def __init__(self, reason: str):
        super().__init__(
            code="PATH_ADJUSTMENT_FAILED",
            message=f"路径调整失败: {reason}",
            retryable=True,
            details={"reason": reason},
        )


# ── LLM 错误 ──

class LLMTimeout(AgentError):
    """LLM 调用超时。"""

    def __init__(self, model: str, timeout_s: int):
        super().__init__(
            code="LLM_TIMEOUT",
            message=f"模型 {model} 响应超时（{timeout_s}s）",
            retryable=True,
            details={"model": model, "timeout_s": timeout_s},
        )


class LLMProviderError(AgentError):
    """LLM 服务商错误。"""

    def __init__(self, provider: str, reason: str):
        super().__init__(
            code="LLM_PROVIDER_ERROR",
            message=f"{provider} 服务异常: {reason}",
            retryable=True,
            details={"provider": provider, "reason": reason},
        )
