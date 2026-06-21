"""
ResourceAgent 单元测试 — TC-R01 ~ TC-R09（对齐 docs/test_plan.md §3.3）
"""
import json
import pytest

from backend.agents.resource_agent import ResourceAgent


@pytest.fixture
def agent():
    return ResourceAgent()


@pytest.fixture
def sample_profile():
    return {
        "profile": {
            "knowledge_level": "初级",
            "learning_goal": "掌握机器学习",
            "cognitive_style": "偏好图解和案例",
            "weakness": ["数学推导"],
            "interest": ["计算机视觉"],
        }
    }


# ── TC-R01: 生成 document ─────────────────────────────────
@pytest.mark.asyncio
async def test_generate_document(agent, sample_profile):
    """TC-R01: 生成 Markdown 讲解文档"""
    data = await agent.generate_resources(
        topic="线性回归",
        resource_types=["document"],
        difficulty="初级",
        profile=sample_profile,
    )
    resources = data["resources"]
    assert len(resources) == 1
    r = resources[0]
    assert r["type"] == "document"
    assert "线性回归" in r["title"]
    assert r["difficulty"] == "初级"
    assert "#" in r["content"]  # Markdown 标题


# ── TC-R02: 生成 mindmap ──────────────────────────────────
@pytest.mark.asyncio
async def test_generate_mindmap(agent, sample_profile):
    """TC-R02: 生成嵌套 Markdown 列表（供 markmap 渲染）"""
    data = await agent.generate_resources(
        topic="神经网络",
        resource_types=["mindmap"],
        difficulty="中级",
    )
    r = data["resources"][0]
    assert r["type"] == "mindmap"
    # mindmap 内容应为缩进 Markdown 列表
    assert "- " in r["content"]
    assert "  - " in r["content"]


# ── TC-R03: 生成 exercise ─────────────────────────────────
@pytest.mark.asyncio
async def test_generate_exercise(agent, sample_profile):
    """TC-R03: 生成练习题，含 question / options / answer / explanation"""
    data = await agent.generate_resources(
        topic="梯度下降",
        resource_types=["exercise"],
        difficulty="初级",
    )
    r = data["resources"][0]
    assert r["type"] == "exercise"
    # exercise 的 content 是 JSON 字符串，包含题目列表
    questions = json.loads(r["content"])
    assert isinstance(questions, list)
    assert len(questions) >= 1
    q = questions[0]
    assert "question" in q
    assert "answer" in q
    assert "explanation" in q


# ── TC-R04: 生成 code ─────────────────────────────────────
@pytest.mark.asyncio
async def test_generate_code(agent, sample_profile):
    """TC-R04: 生成含注释的 Python 代码"""
    data = await agent.generate_resources(
        topic="KNN 分类",
        resource_types=["code"],
        difficulty="中级",
    )
    r = data["resources"][0]
    assert r["type"] == "code"
    assert "import" in r["content"] or "def " in r["content"] or "print" in r["content"]


# ── TC-R05: 生成 reading ──────────────────────────────────
@pytest.mark.asyncio
async def test_generate_reading(agent, sample_profile):
    """TC-R05: 生成拓展阅读材料"""
    data = await agent.generate_resources(
        topic="CNN 架构",
        resource_types=["reading"],
        difficulty="高级",
    )
    r = data["resources"][0]
    assert r["type"] == "reading"
    assert "推荐" in r["content"] or "参考" in r["content"] or "阅读" in r["content"]


# ── TC-R06: 批量生成多种类型 ──────────────────────────────
@pytest.mark.asyncio
async def test_generate_multiple_types(agent, sample_profile):
    """一次性生成多种资源类型"""
    data = await agent.generate_resources(
        topic="SVM",
        resource_types=["document", "mindmap", "exercise"],
        difficulty="中级",
    )
    assert len(data["resources"]) == 3
    types = {r["type"] for r in data["resources"]}
    assert types == {"document", "mindmap", "exercise"}


# ── TC-R07: 内容难度匹配 ─────────────────────────────────
@pytest.mark.asyncio
async def test_difficulty_reflected_in_content(agent):
    """初级和高级的内容应不同"""
    data_easy = await agent.generate_resources(
        topic="线性回归",
        resource_types=["document"],
        difficulty="初级",
    )
    data_hard = await agent.generate_resources(
        topic="线性回归",
        resource_types=["document"],
        difficulty="高级",
    )
    easy_content = data_easy["resources"][0]["content"]
    hard_content = data_hard["resources"][0]["content"]

    # 初级标注"入门"，高级标注"深入"
    assert "入门" in easy_content
    assert "深入" in hard_content


# ── 所有资源字段完整性 ────────────────────────────────────
@pytest.mark.asyncio
async def test_resource_fields_complete(agent, sample_profile):
    """TC-R08: 每个资源必须包含 type/title/topic/difficulty/content"""
    data = await agent.generate_resources(
        topic="决策树",
        resource_types=["document", "mindmap", "exercise", "code", "reading", "ppt"],
        difficulty="中级",
        profile=sample_profile,
    )
    for r in data["resources"]:
        required = {"type", "title", "topic", "difficulty", "content"}
        assert required.issubset(set(r.keys())), f"缺少字段: {required - set(r.keys())}"
        assert r["topic"] == "决策树"
        assert r["difficulty"] == "中级"


# ── TC-R09: 无 LLM 时 Agent 不崩溃 ────────────────────────
@pytest.mark.asyncio
async def test_no_llm_fallback(agent):
    """无 LLM 时规则化兜底正常工作"""
    data = await agent.generate_resources(topic="测试", resource_types=["document"])
    assert len(data["resources"]) >= 1
    assert data["resources"][0]["type"] == "document"
