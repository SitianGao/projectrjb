"""
语义检索器 —— 组合 embedding + vector_store，提供高层检索接口

设计依据：docs/design.md §4.3 + §7.3
"""
import logging
from typing import List, Dict

from .embedding import default_embedding
from .vector_store import default_store

logger = logging.getLogger(__name__)


class Retriever:
    """RAG 检索器：查询文本 → 嵌入 → ChromaDB 检索 → 格式化结果"""

    def __init__(self, embedding=None, vector_store=None):
        """
        Args:
            embedding: 嵌入模型（默认使用模块级单例）
            vector_store: 向量存储（默认使用模块级单例）
        """
        self.embedding = embedding or default_embedding
        self.vector_store = vector_store or default_store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> List[Dict]:
        """语义检索

        Args:
            query: 用户查询文本
            top_k: 返回结果数
            min_similarity: 最低相似度阈值（0~1），低于此值的结果被过滤。
                           余弦距离 < 0.5 ≈ 余弦相似度 > 0.5

        Returns:
            list of dict: [
                {
                    "id": str,
                    "content": str,       # 匹配的文本片段
                    "source": str,        # 来源文件名
                    "title": str,         # 文档标题
                    "similarity": float,  # 余弦相似度 (0~1)
                },
                ...
            ]
        """
        if self.vector_store.count() == 0:
            logger.warning("知识库为空，检索返回空结果")
            return []

        # 查询向量化
        query_embedding = self.embedding.embed(query)

        # ChromaDB 检索
        results = self.vector_store.query(query_embedding, n_results=top_k)

        # 格式化 + 过滤
        formatted = []
        for r in results:
            # ChromaDB 使用余弦距离，转换为余弦相似度: similarity = 1 - distance
            distance = r.get("distance", 1.0)
            similarity = 1.0 - distance

            if similarity < min_similarity:
                continue

            metadata = r.get("metadata", {})
            formatted.append({
                "id": r["id"],
                "content": r["document"],
                "source": metadata.get("source", "unknown"),
                "title": metadata.get("title", ""),
                "similarity": round(similarity, 4),
            })

        logger.info(
            f"检索完成: query='{query[:50]}...' -> {len(formatted)}/{len(results)} 条结果 (top_k={top_k})"
        )
        return formatted

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> str:
        """检索并格式化为 LLM 可用的上下文文本

        用于 TutorAgent 拼接 RAG 上下文。

        Args:
            query: 用户查询
            top_k: 引用数量

        Returns:
            str: 格式化的参考知识文本，可直接拼入 LLM prompt
        """
        results = self.retrieve(query, top_k=top_k, min_similarity=0.3)

        if not results:
            return "（资料库中未找到可靠依据）"

        lines = ["## 参考知识点（来自知识库）\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"### 参考 {i}：{r['title']}")
            lines.append(f"- **来源**：{r['source']}")
            lines.append(f"- **相似度**：{r['similarity']:.2%}")
            lines.append(f"- **内容**：{r['content'][:500]}")
            lines.append("")

        return "\n".join(lines)


# 模块级单例
default_retriever = Retriever()
