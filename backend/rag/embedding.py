"""
文本转向量 —— 基于 sentence-transformers 的嵌入模型封装

设计依据：docs/design.md §3.1
"""
from typing import List
import logging

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """文本嵌入模型封装，支持单条和批量文本转向量"""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Args:
            model_name: sentence-transformers 模型名。
                        默认 paraphrase-multilingual-MiniLM-L12-v2，
                        中英文双语支持，384 维向量，模型仅 ~120MB。
        """
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """延迟加载模型（首次使用时加载，节省启动时间）"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"加载嵌入模型: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"嵌入模型加载完成，向量维度: {self.dim}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers 未安装。请执行: pip install sentence-transformers"
                )
            except Exception as e:
                logger.error(f"加载嵌入模型失败: {e}")
                raise

    def embed(self, text: str) -> List[float]:
        """将单条文本转为向量

        Args:
            text: 输入文本

        Returns:
            list of float: 384 维向量
        """
        self._load_model()
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量文本转向量（比逐条调用快）

        Args:
            texts: 输入文本列表

        Returns:
            list of list of float
        """
        self._load_model()
        embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()

    @property
    def dim(self) -> int:
        """向量维度"""
        self._load_model()
        return self._model.get_sentence_embedding_dimension()


# 模块级单例
default_embedding = EmbeddingModel()
