"""课程知识库隔离测试。"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.knowledge_service import KnowledgeService, COURSE_KNOWLEDGE_MAP
from core.errors import CourseKnowledgeBaseNotFound


class TestKnowledgeService:
    """测试 KnowledgeService 的课程隔离。"""

    def setup_method(self):
        self.service = KnowledgeService()

    def test_resolve_known_course(self):
        """已注册课程应返回正确配置。"""
        config = self.service.resolve_knowledge_base("ai_deep_learning_demo")
        assert config["knowledge_base_id"] == "kb_ai_deep_learning"
        assert config["vector_collection"] == "ai_deep_learning_documents"
        assert config["course_name"] == "人工智能与深度学习"

    def test_unknown_course_raises(self):
        """未注册课程应抛出 CourseKnowledgeBaseNotFound。"""
        with pytest.raises(CourseKnowledgeBaseNotFound) as exc:
            self.service.resolve_knowledge_base("nonexistent_course")
        assert "nonexistent_course" in str(exc.value)
        assert exc.value.code == "COURSE_KNOWLEDGE_BASE_NOT_FOUND"

    def test_unknown_course_not_fallback(self):
        """未注册课程不应自动兜底到其他课程。"""
        with pytest.raises(CourseKnowledgeBaseNotFound):
            self.service.get_vector_collection("discrete_math")

    def test_get_vector_collection(self):
        """get_vector_collection 返回正确的集合名。"""
        col = self.service.get_vector_collection("ai_deep_learning_demo")
        assert col == "ai_deep_learning_documents"

    def test_get_knowledge_base_id(self):
        """get_knowledge_base_id 返回正确的知识库 ID。"""
        kb_id = self.service.get_knowledge_base_id("ai_deep_learning_demo")
        assert kb_id == "kb_ai_deep_learning"

    def test_register_course_idempotent(self):
        """重复注册同一课程应幂等更新。"""
        KnowledgeService.register_course(
            course_id="test_course",
            knowledge_base_id="kb_test",
            vector_collection="test_collection",
            course_name="测试课程",
        )
        config = self.service.resolve_knowledge_base("test_course")
        assert config["knowledge_base_id"] == "kb_test"

        # 重复注册
        KnowledgeService.register_course(
            course_id="test_course",
            knowledge_base_id="kb_test_v2",
            vector_collection="test_collection_v2",
        )
        config2 = self.service.resolve_knowledge_base("test_course")
        assert config2["knowledge_base_id"] == "kb_test_v2"

    def test_cross_course_isolation(self):
        """人工智能课程不应返回离散数学知识库。"""
        ai_config = self.service.resolve_knowledge_base("ai_deep_learning_demo")
        # 离散数学未注册
        with pytest.raises(CourseKnowledgeBaseNotFound):
            self.service.resolve_knowledge_base("discrete_math")
        # AI 课程配置不应被影响
        assert ai_config["knowledge_base_id"] == "kb_ai_deep_learning"
