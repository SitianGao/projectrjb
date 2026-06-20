"""
TutorAgent + RAG 集成测试 — TC-R01 ~ TC-R08（Day 8 新增）

验证:
- tutor_with_rag() 返回 §10.4.3 四字段结构
- RAG references 格式: {title, source, content, similarity}
- 四种解释风格 + auto 模式
- 空问题 / 非学术问题处理
- _build_rag_context / _format_references 格式化
- 无 LLM 时的规则化兜底
"""
import json
import pytest

from backend.agents.tutor_agent import TutorAgent


@pytest.fixture
def agent():
    """无 LLM 的 TutorAgent（规则化兜底路径）"""
    return TutorAgent()


@pytest.fixture
def mock_retriever():
    """构造一个轻量级 mock retriever，返回固定 RAG 结果"""

    class MockRetriever:
        def retrieve(self, query, top_k=3, min_similarity=0.0):
            return [
                {
                    "id": "chunk_001",
                    "content": "梯度下降是一种迭代优化算法，通过计算损失函数关于参数的梯度，沿负梯度方向更新参数以最小化损失。学习率控制每一步的步长。",
                    "source": "优化算法.md",
                    "title": "梯度下降法原理",
                    "similarity": 0.87,
                },
                {
                    "id": "chunk_002",
                    "content": "随机梯度下降 (SGD) 每次只使用一个样本计算梯度，更新更快但带有噪声。小批量梯度下降则是折中方案。",
                    "source": "优化算法.md",
                    "title": "SGD 与批量梯度下降",
                    "similarity": 0.72,
                },
                {
                    "id": "chunk_003",
                    "content": "学习率衰减策略包括：阶梯衰减、指数衰减、余弦退火等。适当的学习率调度有助于模型收敛到更好的最优点。",
                    "source": "训练技巧.md",
                    "title": "学习率调度策略",
                    "similarity": 0.58,
                },
            ]

    return MockRetriever()


# ── TC-R01: tutor_with_rag 返回完整四字段结构 ─────────────────────────
@pytest.mark.asyncio
async def test_rag_returns_structured_output(agent, mock_retriever):
    """TC-R01: tutor_with_rag() 返回 dict 含 answer/explanation_style/references/diagrams"""
    result = await agent.tutor_with_rag(
        question="梯度下降是什么？",
        retriever=mock_retriever,
        explanation_style="auto",
    )

    assert isinstance(result, dict)
    assert "answer" in result
    assert "explanation_style" in result
    assert "references" in result
    assert "diagrams" in result

    assert isinstance(result["answer"], str) and len(result["answer"]) > 0
    assert result["explanation_style"] in ("analogy", "formula", "visual", "story", "auto")
    assert isinstance(result["references"], list)
    assert isinstance(result["diagrams"], list)


# ── TC-R02: references 元素包含 title/source/content/similarity ─────────
@pytest.mark.asyncio
async def test_rag_references_format(agent, mock_retriever):
    """TC-R02: 每条 reference 包含 title, source, content, similarity"""
    result = await agent.tutor_with_rag(
        question="梯度下降和SGD有什么区别？",
        retriever=mock_retriever,
        explanation_style="analogy",
    )

    refs = result["references"]
    assert len(refs) >= 1, "RAG references 不应为空"

    for ref in refs:
        assert "title" in ref, f"缺少 title: {ref}"
        assert "source" in ref, f"缺少 source: {ref}"
        assert "content" in ref, f"缺少 content: {ref}"
        assert "similarity" in ref, f"缺少 similarity: {ref}"
        # 类型校验
        assert isinstance(ref["title"], str)
        assert isinstance(ref["source"], str)
        assert isinstance(ref["content"], str)
        assert isinstance(ref["similarity"], (int, float))
        assert 0.0 <= ref["similarity"] <= 1.0


# ── TC-R03: 四种解释风格均返回有效 JSON ─────────────────────────────────
@pytest.mark.asyncio
async def test_all_four_styles_with_rag(agent, mock_retriever):
    """TC-R03: analogy / formula / visual / story 四种风格均可正常输出"""
    question = "神经网络如何训练？"

    for style in ("analogy", "formula", "visual", "story"):
        result = await agent.tutor_with_rag(
            question=question,
            retriever=mock_retriever,
            explanation_style=style,
        )
        assert result["explanation_style"] == style, f"风格不匹配: 期望 {style}, 实际 {result['explanation_style']}"
        assert len(result["answer"]) > 0, f"{style} 风格答案为空"

        # visual 风格应有 diagrams
        if style == "visual":
            assert len(result["diagrams"]) >= 1, f"{style} 风格应有图表"


# ── TC-R04: auto 模式自动选择有效风格 ────────────────────────────────────
@pytest.mark.asyncio
async def test_auto_style_with_rag(agent, mock_retriever):
    """TC-R04: auto 模式根据问题类型自动选风格，结果仍含 RAG references"""
    test_cases = [
        ("CNN 和 RNN 有什么区别？", ["analogy", "formula", "visual", "story"]),
        ("推导一下反向传播公式", ["analogy", "formula", "visual", "story"]),
        ("描述神经网络的训练流程", ["analogy", "formula", "visual", "story"]),
    ]

    for q, valid_styles in test_cases:
        result = await agent.tutor_with_rag(
            question=q,
            retriever=mock_retriever,
            explanation_style="auto",
        )
        assert result["explanation_style"] in valid_styles
        assert len(result["references"]) >= 1
        assert len(result["answer"]) > 0


# ── TC-R05: 空问题处理 ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_empty_question_with_rag(agent, mock_retriever):
    """TC-R05: 空问题不抛异常，返回合理回答"""
    result = await agent.tutor_with_rag(
        question="",
        retriever=mock_retriever,
    )
    assert isinstance(result, dict)
    assert "answer" in result
    assert isinstance(result["answer"], str)


# ── TC-R06: 无 LLM 规则化兜底仍注入 references ──────────────────────────
@pytest.mark.asyncio
async def test_rule_based_fallback_with_references(agent, mock_retriever):
    """TC-R06: 无 LLM 时规则化回答也包含 RAG references"""
    result = await agent.tutor_with_rag(
        question="什么是激活函数？",
        retriever=mock_retriever,
        explanation_style="formula",
    )

    assert len(result["references"]) >= 1
    assert result["explanation_style"] == "formula"
    assert result["references"][0]["title"] == "梯度下降法原理"  # mock 的第一条


# ── TC-R07: _build_rag_context 格式化验证 ────────────────────────────────
def test_build_rag_context_format():
    """TC-R07: _build_rag_context 输出含标题、来源、相似度"""
    mock_results = [
        {
            "title": "测试知识点",
            "source": "test.md",
            "content": "这是测试内容。",
            "similarity": 0.95,
        },
    ]
    context = TutorAgent._build_rag_context(mock_results)
    assert "测试知识点" in context
    assert "test.md" in context
    assert "95%" in context
    assert "这是测试内容" in context


# ── TC-R08: _format_references 输出列表包含 content ──────────────────────
def test_format_references_content():
    """TC-R08: _format_references 将 RAG 结果转为 {title, source, content, similarity}"""
    mock_results = [
        {
            "title": "Ref A",
            "source": "source_a.md",
            "content": "内容A" * 100,  # 足够长以验证截断
            "similarity": 0.88,
        },
    ]
    refs = TutorAgent._format_references(mock_results)
    assert isinstance(refs, list)
    assert len(refs) == 1
    assert refs[0]["title"] == "Ref A"
    assert refs[0]["source"] == "source_a.md"
    assert len(refs[0]["content"]) <= 200  # content 截断在 200 字符
    assert refs[0]["similarity"] == 0.88


# ==========================================================================
# Day 12 扩展测试: TC-R09 ~ TC-R15
# ==========================================================================

# ── TC-R09: RetrieverConfig 预置场景加载正确 ──────────────────────
def test_retriever_config_presets():
    """TC-R09: 四种场景预设配置加载正确"""
    from backend.rag.retriever_config import get_config, PRESETS

    assert "tutor" in PRESETS
    assert "resource" in PRESETS
    assert "evaluate" in PRESETS
    assert "default" in PRESETS

    # 辅导场景：高召回
    tutor_cfg = get_config("tutor")
    assert tutor_cfg.min_similarity == 0.30
    assert tutor_cfg.top_k == 3

    # 资源匹配：高精确率
    resource_cfg = get_config("resource")
    assert resource_cfg.min_similarity == 0.40
    assert resource_cfg.top_k == 5

    # 评估回顾：最高召回
    evaluate_cfg = get_config("evaluate")
    assert evaluate_cfg.min_similarity == 0.25

    # 未知场景退回 default
    unknown_cfg = get_config("nonexistent")
    assert unknown_cfg.min_similarity == PRESETS["default"].min_similarity


# ── TC-R10: 推荐分块参数按内容类型返回 ──────────────────────────
def test_recommend_chunk_params():
    """TC-R10: 不同内容类型返回合理的分块参数"""
    from backend.rag.retriever_config import recommend_chunk_params

    # article 类型
    article = recommend_chunk_params("article")
    assert article["max_chars"] == 800
    assert article["overlap_chars"] == 100

    # 公式密集
    formula = recommend_chunk_params("formula_heavy")
    assert formula["max_chars"] <= article["max_chars"], "公式密集应更小块"

    # 术语表
    glossary = recommend_chunk_params("glossary")
    assert glossary["max_chars"] <= formula["max_chars"], "术语表应最小块"

    # 未知类型返回默认
    unknown = recommend_chunk_params("unknown_type")
    assert unknown["max_chars"] == 800


# ── TC-R11: Retriever.search() 返回格式化上下文 ──────────────────
def test_retriever_search_returns_formatted_context():
    """TC-R11: search() 返回含标题/来源/相似度的 LLM 上下文"""
    from backend.rag.retriever import Retriever

    class FakeEmbedding:
        def embed(self, text):
            return [0.1] * 384

    class FakeStore:
        def count(self):
            return 1

        def query(self, embedding, n_results=3):
            return [
                {
                    "id": "chunk_x",
                    "document": "训练集和测试集应保持相同的分布特征，否则模型评估结果不可靠。",
                    "distance": 0.15,
                    "metadata": {
                        "source": "ml_basics.md",
                        "title": "数据集划分原则",
                    },
                }
            ]

    retriever = Retriever(embedding=FakeEmbedding(), vector_store=FakeStore())
    context = retriever.search("训练集和测试集", top_k=1)
    assert "数据集划分原则" in context
    assert "ml_basics.md" in context
    assert "85" in context  # similarity = 1 - 0.15 = 85%


# ── TC-R12: 空知识库返回友好降级文案 ───────────────────────────
def test_retriever_empty_store_graceful():
    """TC-R12: 知识库为空时 search() 返回「未找到可靠依据」"""
    from backend.rag.retriever import Retriever

    class EmptyStore:
        def count(self):
            return 0

    retriever = Retriever(embedding=None, vector_store=EmptyStore())
    context = retriever.search("机器学习", top_k=3)
    assert "未找到可靠依据" in context


# ── TC-R13: 低相似度结果被 min_similarity 过滤 ──────────────────
def test_retriever_low_similarity_filtered():
    """TC-R13: 低于阈值的检索结果被过滤"""
    from backend.rag.retriever import Retriever

    class FakeEmbedding:
        def embed(self, text):
            return [0.1] * 384

    class LowSimStore:
        def count(self):
            return 1

        def query(self, embedding, n_results=5):
            return [
                {"id": "c1", "document": "高相关", "distance": 0.2,
                 "metadata": {"source": "s1.md", "title": "T1"}},
                {"id": "c2", "document": "低相关", "distance": 0.8,
                 "metadata": {"source": "s2.md", "title": "T2"}},
            ]

    retriever = Retriever(embedding=FakeEmbedding(), vector_store=LowSimStore())
    results = retriever.retrieve("查询", top_k=5, min_similarity=0.5)
    # distance 0.8 = similarity 0.2 → 应被过滤
    # distance 0.2 = similarity 0.8 → 保留
    assert len(results) == 1, f"预期过滤低相似度，实际返回 {len(results)} 条"
    assert results[0]["title"] == "T1"


# ── TC-R14: 按 scenario 调整检索参数 ────────────────────────────
@pytest.mark.asyncio
async def test_rag_with_different_scenarios(agent, mock_retriever):
    """TC-R14: tutor/resource/evaluate 场景使用不同的相似度阈值"""
    from backend.rag.retriever_config import get_config

    # 辅导场景 top_k=3
    tutor_cfg = get_config("tutor")
    result_tutor = await agent.tutor_with_rag(
        question="梯度下降是什么？",
        retriever=mock_retriever,
        explanation_style="auto",
        top_k=tutor_cfg.top_k,
    )
    assert len(result_tutor["references"]) >= 1

    # 资源匹配场景应返回更多引用 (top_k=5)
    resource_cfg = get_config("resource")
    result_resource = await agent.tutor_with_rag(
        question="深度学习优化器的选择",
        retriever=mock_retriever,
        explanation_style="auto",
        top_k=resource_cfg.top_k,
    )
    # mock_retriever 固定返回 3 条，所以这里的 3 <= top_k=5
    assert len(result_resource["references"]) >= 1


# ── TC-R15: 相似度值在合法范围内 ────────────────────────────────
@pytest.mark.asyncio
async def test_rag_similarity_in_valid_range(agent, mock_retriever):
    """TC-R15: 所有 reference 的 similarity 值在 [0.0, 1.0] 范围内"""
    result = await agent.tutor_with_rag(
        question="神经网络如何训练？",
        retriever=mock_retriever,
        explanation_style="analogy",
    )

    for ref in result["references"]:
        sim = ref["similarity"]
        assert 0.0 <= sim <= 1.0, f"similarity={sim} 超出 [0, 1] 范围"
        # 应该是合理的数值（不是 NaN 或 Inf）
        assert isinstance(sim, (int, float))
