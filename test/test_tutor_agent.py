"""
TutorAgent 单元测试 — TC-T01 ~ TC-T07（对齐 docs/test_plan.md §3.4）
"""
import json
import pytest

from backend.agents.tutor_agent import TutorAgent


@pytest.fixture
def agent():
    return TutorAgent()


# ── TC-T01: 基础问答 ──────────────────────────────────────
@pytest.mark.asyncio
async def test_basic_question(agent):
    """TC-T01: 提问返回结构化回答"""
    raw = await agent.tutor(question="梯度下降是什么？")
    data = json.loads(raw)

    assert "answer" in data
    assert "explanation_style" in data
    assert "references" in data
    assert "diagrams" in data
    assert isinstance(data["diagrams"], list)
    assert len(data["answer"]) > 0


# ── TC-T02: 类比法解释 ────────────────────────────────────
@pytest.mark.asyncio
async def test_analogy_style(agent):
    """TC-T02: analogy 风格输出日常生活类比"""
    raw = await agent.tutor(
        question="监督学习和无监督学习有什么区别？",
        explanation_style="analogy",
    )
    data = json.loads(raw)
    assert data["explanation_style"] == "analogy"
    assert any(kw in data["answer"] for kw in ["就像", "类比", "想象", "日常"])


# ── TC-T03: 图示法含 Mermaid ──────────────────────────────
@pytest.mark.asyncio
async def test_visual_style_with_mermaid(agent):
    """TC-T03: visual 风格回答含 Mermaid 图表"""
    raw = await agent.tutor(
        question="神经网络的训练流程是怎样的？",
        explanation_style="visual",
    )
    data = json.loads(raw)
    assert data["explanation_style"] == "visual"
    assert len(data["diagrams"]) >= 1
    assert "graph " in data["diagrams"][0].lower() or "TD" in data["diagrams"][0]


# ── TC-T04: 公式推导法 ───────────────────────────────────
@pytest.mark.asyncio
async def test_formula_style(agent):
    """TC-T04: formula 风格含推导步骤"""
    raw = await agent.tutor(
        question="如何推导梯度下降的更新公式？",
        explanation_style="formula",
    )
    data = json.loads(raw)
    assert data["explanation_style"] == "formula"
    assert "推导" in data["answer"] or "公式" in data["answer"] or "定义" in data["answer"]


# ── TC-T05: 非学术问题引导 ────────────────────────────────
@pytest.mark.asyncio
async def test_non_academic_redirect(agent):
    """TC-T05: 超出范围的问题礼貌引导回学习主题"""
    raw = await agent.tutor(question="今天天气怎么样？适合出去玩吗？")
    data = json.loads(raw)
    assert "学习" in data["answer"] or "课程" in data["answer"]
    assert data["diagrams"] == []


# ── TC-T06: answer/explanation_style/references/diagrams 完整性 ──
@pytest.mark.asyncio
async def test_output_fields_complete(agent):
    """验证输出 4 字段始终存在"""
    for q in ["什么是SVM？", "为什么需要激活函数？"]:
        raw = await agent.tutor(question=q)
        data = json.loads(raw)
        required = {"answer", "explanation_style", "references", "diagrams"}
        assert required.issubset(set(data.keys())), f"缺少字段: {required - set(data.keys())}"


# ── TC-T07: 自动风格选择 ──────────────────────────────────
@pytest.mark.asyncio
async def test_auto_style_selection(agent):
    """auto 模式根据问题类型自动选择风格"""
    # 含"区别" → analogy
    raw = await agent.tutor(question="CNN和RNN有什么区别？", explanation_style="auto")
    data = json.loads(raw)
    assert data["explanation_style"] in ("analogy", "formula", "visual", "story")

    # 含"推导" → formula
    raw = await agent.tutor(question="帮我推导一下反向传播公式", explanation_style="auto")
    data = json.loads(raw)
    assert data["explanation_style"] in ("analogy", "formula", "visual", "story")
