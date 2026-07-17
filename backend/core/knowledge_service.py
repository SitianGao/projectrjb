"""
KnowledgeService —— 课程作用域知识库检索服务。

根据 course_id 获取正确的 knowledge_base_id 和 vector_collection，
确保检索操作只返回当前课程的知识库内容。

所有 Agent 必须通过此服务进行知识检索，不允许直接使用全局默认集合。
"""

from __future__ import annotations

import logging
from typing import Optional

from .errors import CourseKnowledgeBaseNotFound

logger = logging.getLogger(__name__)

# 课程 → 知识库配置映射表
# 每门课程绑定独立的 knowledge_base_id 和 vector_collection
COURSE_KNOWLEDGE_MAP: dict[str, dict] = {
    "ai_deep_learning_demo": {
        "knowledge_base_id": "kb_ai_deep_learning",
        "vector_collection": "ai_deep_learning_documents",
        "course_name": "人工智能与深度学习",
    },
}


class KnowledgeService:
    """课程作用域知识库检索服务。

    职责：
    1. 根据 course_id 解析 knowledge_base_id 和 vector_collection
    2. 使用正确的 collection 进行 RAG 检索
    3. 确保跨课程数据隔离
    """

    def __init__(self, retriever=None, vector_store_factory=None):
        """
        Args:
            retriever: RAG 检索器实例（默认使用模块级单例）
            vector_store_factory: VectorStore 工厂函数（用于创建课程专用 collection）
        """
        self._retriever = retriever
        self._vector_store_factory = vector_store_factory

    # ── 知识库配置解析 ──

    def resolve_knowledge_base(self, course_id: str) -> dict:
        """根据 course_id 获取知识库配置。

        Returns:
            {"knowledge_base_id": str, "vector_collection": str, "course_name": str}

        Raises:
            CourseKnowledgeBaseNotFound: 课程未在知识库映射表中配置
        """
        config = COURSE_KNOWLEDGE_MAP.get(course_id)
        if not config:
            raise CourseKnowledgeBaseNotFound(course_id)
        return config

    def get_vector_collection(self, course_id: str) -> str:
        """获取课程对应的向量集合名称。"""
        return self.resolve_knowledge_base(course_id)["vector_collection"]

    def get_knowledge_base_id(self, course_id: str) -> str:
        """获取课程对应的知识库 ID。"""
        return self.resolve_knowledge_base(course_id)["knowledge_base_id"]

    # ── 检索 ──

    def retrieve(
        self,
        course_id: str,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.3,
    ) -> list[dict]:
        """课程作用域语义检索。

        只检索当前课程绑定的向量集合，确保跨课程数据隔离。

        Args:
            course_id: 课程 ID
            query: 检索查询文本
            top_k: 返回结果数
            min_similarity: 最低相似度阈值

        Returns:
            [{"id", "content", "source", "title", "similarity"}, ...]

        Raises:
            CourseKnowledgeBaseNotFound: 课程未绑定知识库
        """
        from rag.retriever import default_retriever
        from rag.vector_store import VectorStore

        config = self.resolve_knowledge_base(course_id)
        collection_name = config["vector_collection"]

        retriever = self._retriever or default_retriever

        # 如果课程使用特定的 collection（非默认），创建专用 VectorStore
        if collection_name != retriever.vector_store.collection_name:
            persist_dir = retriever.vector_store.persist_dir
            course_store = VectorStore(
                collection_name=collection_name,
                persist_dir=persist_dir,
            )
            # 创建专用检索器
            from rag.retriever import Retriever
            course_retriever = Retriever(
                embedding=retriever.embedding,
                vector_store=course_store,
                lexical_retriever=retriever.lexical_retriever,
                strict=retriever.strict,
            )
            results = course_retriever.retrieve(
                query=query,
                top_k=top_k,
                min_similarity=min_similarity,
            )
        else:
            results = retriever.retrieve(
                query=query,
                top_k=top_k,
                min_similarity=min_similarity,
            )

        logger.info(
            "KnowledgeService 检索: course=%s collection=%s query='%s' → %d results",
            course_id, collection_name, query[:60], len(results),
        )
        return results

    def search_context(
        self,
        course_id: str,
        query: str,
        top_k: int = 3,
    ) -> str:
        """检索并格式化为 LLM 可用的上下文文本。

        Args:
            course_id: 课程 ID
            query: 检索查询
            top_k: 引用数量

        Returns:
            格式化的 Markdown 参考文本，可直接拼入 LLM prompt
        """
        results = self.retrieve(course_id, query, top_k=top_k)

        if not results:
            return "（资料库中未找到可靠依据）"

        lines = ["## 参考知识点（来自课程知识库）\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"### 参考 {i}：{r['title']}")
            lines.append(f"- **来源**：{r['source']}")
            lines.append(f"- **相似度**：{r['similarity']:.2%}")
            lines.append(f"- **内容**：{r['content'][:500]}")
            lines.append("")

        return "\n".join(lines)

    # ── 课程注册 ──

    @classmethod
    def register_course(
        cls,
        course_id: str,
        knowledge_base_id: str,
        vector_collection: str,
        course_name: str = "",
    ) -> None:
        """注册新课程的知识库映射。

        用于演示课程初始化时动态注册。
        幂等——重复注册同一 course_id 会更新配置。
        """
        COURSE_KNOWLEDGE_MAP[course_id] = {
            "knowledge_base_id": knowledge_base_id,
            "vector_collection": vector_collection,
            "course_name": course_name,
        }
        logger.info(
            "注册课程知识库: %s → collection=%s kb=%s",
            course_id, vector_collection, knowledge_base_id,
        )


# 模块级单例
knowledge_service = KnowledgeService()
