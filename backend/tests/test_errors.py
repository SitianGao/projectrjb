"""统一错误类型测试。"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.errors import (
    AgentError,
    AgentOutputInvalid,
    CourseContextMissing,
    CourseNotFound,
    CourseAccessDenied,
    CourseKnowledgeBaseNotFound,
    CourseScopeMismatch,
    ResourceSchemaInvalid,
    EvaluationDataInsufficient,
    PathGenerationFailed,
    PathAdjustmentFailed,
    LLMTimeout,
    LLMProviderError,
)


class TestAgentErrors:
    """测试所有统一错误类型。"""

    def test_agent_error_to_dict(self):
        err = AgentError("TEST_CODE", "测试错误", retryable=True, details={"key": "val"})
        d = err.to_dict()
        assert d["code"] == "TEST_CODE"
        assert d["message"] == "测试错误"
        assert d["retryable"] is True
        assert d["details"] == {"key": "val"}

    def test_agent_output_invalid(self):
        err = AgentOutputInvalid("PlannerAgent", "JSON 解析失败")
        d = err.to_dict()
        assert d["code"] == "AGENT_OUTPUT_INVALID"
        assert d["retryable"] is True

    def test_course_context_missing(self):
        err = CourseContextMissing("TutorAgent")
        assert err.code == "COURSE_CONTEXT_MISSING"
        assert not err.retryable

    def test_course_not_found(self):
        err = CourseNotFound("unknown_course")
        assert err.code == "COURSE_NOT_FOUND"

    def test_course_access_denied(self):
        err = CourseAccessDenied("user1", "course2")
        d = err.to_dict()
        assert d["details"]["user_id"] == "user1"
        assert d["details"]["course_id"] == "course2"

    def test_knowledge_base_not_found(self):
        err = CourseKnowledgeBaseNotFound("no_kb_course")
        assert err.code == "COURSE_KNOWLEDGE_BASE_NOT_FOUND"
        assert not err.retryable

    def test_scope_mismatch(self):
        err = CourseScopeMismatch(expected="ai_course", actual="math_course", resource="测试资源")
        assert err.code == "COURSE_SCOPE_MISMATCH"
        assert not err.retryable

    def test_resource_schema_invalid(self):
        err = ResourceSchemaInvalid("exercise", "content 不是合法 JSON")
        assert err.code == "RESOURCE_SCHEMA_INVALID"
        assert err.retryable

    def test_evaluation_data_insufficient(self):
        err = EvaluationDataInsufficient("只有 2 条记录")
        assert err.code == "EVALUATION_DATA_INSUFFICIENT"
        assert not err.retryable

    def test_path_generation_failed(self):
        err = PathGenerationFailed("LLM 超时")
        assert err.code == "PATH_GENERATION_FAILED"
        assert err.retryable

    def test_path_adjustment_failed(self):
        err = PathAdjustmentFailed("用户未确认")
        assert err.code == "PATH_ADJUSTMENT_FAILED"
        assert err.retryable

    def test_llm_timeout(self):
        err = LLMTimeout("spark", 120)
        d = err.to_dict()
        assert d["code"] == "LLM_TIMEOUT"
        assert d["retryable"] is True
        assert d["details"]["model"] == "spark"

    def test_llm_provider_error(self):
        err = LLMProviderError("deepseek", "503 Service Unavailable")
        assert err.code == "LLM_PROVIDER_ERROR"
        assert err.retryable

    def test_all_error_codes_unique(self):
        """所有错误码应唯一。"""
        codes = [
            AgentOutputInvalid("x", "x").code,
            CourseContextMissing("x").code,
            CourseNotFound("x").code,
            CourseAccessDenied("x", "x").code,
            CourseKnowledgeBaseNotFound("x").code,
            CourseScopeMismatch("x", "x").code,
            ResourceSchemaInvalid("x", "x").code,
            EvaluationDataInsufficient("x").code,
            PathGenerationFailed("x").code,
            PathAdjustmentFailed("x").code,
            LLMTimeout("x", 1).code,
            LLMProviderError("x", "x").code,
        ]
        assert len(codes) == len(set(codes))
