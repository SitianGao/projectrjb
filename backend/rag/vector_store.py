"""
ChromaDB 向量存储操作封装

设计依据：docs/design.md §3.1 + §4.3
"""
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# 默认持久化目录
DEFAULT_PERSIST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "chroma_db"
)


class VectorStore:
    """ChromaDB 向量存储封装，提供增删查操作"""

    def __init__(self, collection_name: str = "edu_knowledge", persist_dir: str = DEFAULT_PERSIST_DIR):
        """
        Args:
            collection_name: 集合名称
            persist_dir: 持久化目录（默认 data/chroma_db）
        """
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self._client = None
        self._collection = None

    def _ensure_collection(self):
        """延迟初始化 ChromaDB 客户端和集合"""
        if self._collection is not None:
            return

        try:
            import chromadb
        except ImportError:
            raise ImportError("chromadb 未安装。请执行: pip install chromadb")

        os.makedirs(self.persist_dir, exist_ok=True)

        self._client = chromadb.PersistentClient(path=self.persist_dir)

        # 获取或创建集合
        try:
            self._collection = self._client.get_collection(self.collection_name)
            logger.info(f"加载已有集合: {self.collection_name} (文档数: {self._collection.count()})")
        except Exception:
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # 余弦相似度
            )
            logger.info(f"创建新集合: {self.collection_name}")

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict],
    ) -> None:
        """批量添加文档向量

        Args:
            ids: 唯一标识列表（如 ["kb_001", "kb_002"]）
            embeddings: 向量列表
            documents: 原始文本列表
            metadatas: 元数据列表（如 {"source": "ml_basics.md", "title": "..."}）
        """
        self._ensure_collection()
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"添加 {len(ids)} 条文档到集合")

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
    ) -> List[Dict]:
        """语义检索

        Args:
            query_embedding: 查询向量
            n_results: 返回结果数

        Returns:
            list of dict: [
                {"id": str, "document": str, "metadata": dict, "distance": float},
                ...
            ]
        """
        self._ensure_collection()
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        formatted = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted.append({
                    "id": doc_id,
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                })

        return formatted

    def count(self) -> int:
        """返回集合中文档总数"""
        self._ensure_collection()
        return self._collection.count()

    def get_all(self) -> List[Dict]:
        """获取集合中全部文档（用于浏览/导出）"""
        self._ensure_collection()
        results = self._collection.get(
            include=["documents", "metadatas"],
        )

        formatted = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                formatted.append({
                    "id": doc_id,
                    "document": results["documents"][i] if results["documents"] else "",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })
        return formatted

    def delete_by_ids(self, ids: List[str]) -> None:
        """按 ID 删除文档"""
        self._ensure_collection()
        self._collection.delete(ids=ids)
        logger.info(f"删除 {len(ids)} 条文档")

    def delete_collection(self) -> None:
        """删除整个集合（慎用）"""
        self._ensure_collection()
        self._client.delete_collection(self.collection_name)
        self._collection = None
        logger.warning(f"集合 {self.collection_name} 已删除")


# 模块级单例
default_store = VectorStore()
