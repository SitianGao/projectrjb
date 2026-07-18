"""RAG startup bootstrap and health reporting."""

from __future__ import annotations

import logging
from typing import Callable, Dict, Optional

try:
    from config import RAG_AUTO_INIT, RAG_STRICT_MODE
except ModuleNotFoundError:
    from backend.config import RAG_AUTO_INIT, RAG_STRICT_MODE

from .knowledge_loader import quick_load
from .lexical_retriever import default_lexical_retriever
from .vector_store import default_store

logger = logging.getLogger(__name__)


def initialize_rag(
    auto_init: bool = RAG_AUTO_INIT,
    store=None,
    loader: Optional[Callable[..., Dict]] = None,
) -> Dict:
    """Create/load the vector collection and import the knowledge base when empty."""
    store = store or default_store
    loader = loader or quick_load
    try:
        count = store.count()
        if count == 0 and auto_init:
            logger.info("RAG 向量库为空，开始自动导入 data/knowledge")
            stats = loader(clear=False)
            count = store.count()
            if stats.get("errors"):
                logger.warning("RAG 自动导入完成但存在错误: %s", stats["errors"][:3])
        status = "ready" if count > 0 else "empty"
        return {
            "status": status,
            "mode": "vector",
            "strict": bool(RAG_STRICT_MODE),
            "documents": count,
            "collection": getattr(store, "collection_name", "edu_knowledge"),
            "auto_init": bool(auto_init),
        }
    except Exception as exc:
        if RAG_STRICT_MODE:
            logger.error("RAG 严格模式初始化失败，禁止关键词降级: %s", exc)
            return {
                "status": "unavailable",
                "mode": "none",
                "strict": True,
                "documents": 0,
                "collection": getattr(store, "collection_name", "edu_knowledge"),
                "auto_init": bool(auto_init),
                "vector_error": str(exc),
            }
        logger.warning("RAG 初始化失败，辅导功能将使用可解释降级: %s", exc)
        lexical_count = default_lexical_retriever.count()
        return {
            "status": "degraded" if lexical_count > 0 else "unavailable",
            "mode": "lexical" if lexical_count > 0 else "none",
            "strict": False,
            "documents": lexical_count,
            "collection": getattr(store, "collection_name", "edu_knowledge"),
            "auto_init": bool(auto_init),
            "vector_error": str(exc),
        }


def get_rag_status(store=None) -> Dict:
    """Read current RAG status without importing or rebuilding knowledge data."""
    store = store or default_store
    try:
        count = store.count()
        return {
            "status": "ready" if count > 0 else "empty",
            "mode": "vector",
            "strict": bool(RAG_STRICT_MODE),
            "documents": count,
            "collection": getattr(store, "collection_name", "edu_knowledge"),
        }
    except Exception as exc:
        if RAG_STRICT_MODE:
            return {
                "status": "unavailable",
                "mode": "none",
                "strict": True,
                "documents": 0,
                "collection": getattr(store, "collection_name", "edu_knowledge"),
                "vector_error": str(exc),
            }
        lexical_count = default_lexical_retriever.count()
        return {
            "status": "degraded" if lexical_count > 0 else "unavailable",
            "mode": "lexical" if lexical_count > 0 else "none",
            "strict": False,
            "documents": lexical_count,
            "collection": getattr(store, "collection_name", "edu_knowledge"),
            "vector_error": str(exc),
        }
