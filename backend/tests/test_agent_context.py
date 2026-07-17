"""AgentContext 校验测试。"""
import pytest
from pydantic import ValidationError

# 将 backend 加入 path
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_context import AgentContext


class TestAgentContext:
    """测试 AgentContext 的字段校验。"""

    def test_minimal_valid(self):
        """最小有效字段：user_id + course_id。"""
        ctx = AgentContext(user_id="u1", course_id="c1")
        assert ctx.user_id == "u1"
        assert ctx.course_id == "c1"
        assert ctx.stage_id is None
        assert ctx.task_id is None
        assert ctx.knowledge_point_ids == []
        assert ctx.locale == "zh-CN"

    def test_full_fields(self):
        """所有字段都可设置。"""
        ctx = AgentContext(
            user_id="u1",
            course_id="ai_deep_learning_demo",
            stage_id="stage_gd",
            task_id="task_gd_document",
            knowledge_point_ids=["kp_learning_rate"],
            session_id="sess_001",
            knowledge_base_id="kb_ai",
            vector_collection="ai_docs",
            locale="zh-CN",
        )
        assert ctx.stage_id == "stage_gd"
        assert ctx.task_id == "task_gd_document"
        assert len(ctx.knowledge_point_ids) == 1
        assert ctx.knowledge_base_id == "kb_ai"

    def test_missing_course_id_fails(self):
        """缺少 course_id 应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            AgentContext(user_id="u1")

    def test_missing_user_id_fails(self):
        """缺少 user_id 应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            AgentContext(course_id="c1")

    def test_extra_fields_forbidden(self):
        """禁止未声明的额外字段。"""
        with pytest.raises(ValidationError):
            AgentContext(user_id="u1", course_id="c1", random_field="should_fail")

    def test_defaults(self):
        """测试默认值。"""
        ctx = AgentContext(user_id="u1", course_id="c1")
        assert ctx.knowledge_point_ids == []
        assert ctx.session_id is None
        assert ctx.knowledge_base_id is None
        assert ctx.vector_collection is None
        assert ctx.locale == "zh-CN"
