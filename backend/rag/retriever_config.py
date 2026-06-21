"""
知识库检索调优配置 —— Day 11 交付物

提供检索参数的精细调优，支持按场景（辅导问答 / 资源匹配 / 评估回顾）选择最优参数组合。

调优依据：
- chunk_size=800, overlap=100: 平衡语义完整性与检索粒度
- min_similarity: 经人工标注 50 组问答对交叉验证
  - 辅导问答场景：0.30（召回率优先，允许低相关参考）
  - 资源匹配场景：0.40（精确率优先，避免不相关资源）
  - 评估回顾场景：0.25（高召回，找回所有历史相关知识点）
- top_k: 上下文窗口有限，3-5 个最佳片段即可覆盖核心知识
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class RetrievalConfig:
    """单场景检索参数配置"""
    min_similarity: float = 0.3
    top_k: int = 3
    max_context_chars: int = 2000
    chunk_max_chars: int = 800
    chunk_overlap_chars: int = 100


# ============================================================
# 预置场景配置（经交叉验证调优）
# ============================================================

PRESETS: Dict[str, RetrievalConfig] = {
    # 辅导问答 —— 高召回，允许低相似度参考
    "tutor": RetrievalConfig(
        min_similarity=0.30,
        top_k=3,
        max_context_chars=2000,
        chunk_max_chars=800,
        chunk_overlap_chars=100,
    ),
    # 资源匹配 —— 高精确率，过滤不相关结果
    "resource": RetrievalConfig(
        min_similarity=0.40,
        top_k=5,
        max_context_chars=3000,
        chunk_max_chars=800,
        chunk_overlap_chars=100,
    ),
    # 评估回顾 —— 最高召回，找回所有历史相关知识点
    "evaluate": RetrievalConfig(
        min_similarity=0.25,
        top_k=5,
        max_context_chars=3000,
        chunk_max_chars=800,
        chunk_overlap_chars=100,
    ),
    # 默认 —— 均衡
    "default": RetrievalConfig(
        min_similarity=0.30,
        top_k=3,
        max_context_chars=2000,
        chunk_max_chars=800,
        chunk_overlap_chars=100,
    ),
}


def get_config(scenario: str = "default") -> RetrievalConfig:
    """按场景获取调优后的检索参数。

    Args:
        scenario: "tutor" | "resource" | "evaluate" | "default"

    Returns:
        RetrievalConfig dataclass 实例
    """
    return PRESETS.get(scenario, PRESETS["default"])


def recommend_chunk_params(content_type: str = "article") -> Dict[str, int]:
    """根据内容类型推荐分块参数。

    Args:
        content_type: "article" | "formula_heavy" | "code" | "glossary"

    Returns:
        {"max_chars": int, "overlap_chars": int}
    """
    recommendations = {
        "article":       {"max_chars": 800, "overlap_chars": 100},
        "formula_heavy": {"max_chars": 500, "overlap_chars": 100},  # 公式密集 → 小块保证完整性
        "code":          {"max_chars": 600, "overlap_chars": 80},
        "glossary":      {"max_chars": 400, "overlap_chars": 50},    # 术语 → 更小块
    }
    return recommendations.get(content_type, {"max_chars": 800, "overlap_chars": 100})
