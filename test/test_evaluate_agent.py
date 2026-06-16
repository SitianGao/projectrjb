"""
EvaluateAgent 单元测试 — TC-E01 ~ TC-E06（对齐 docs/test_plan.md §3.5）
"""
import json
from datetime import datetime, timezone
import pytest

from backend.agents.evaluate_agent import EvaluateAgent


@pytest.fixture
def agent():
    return EvaluateAgent()


@pytest.fixture
def sample_profile():
    return {
        "knowledge_level": "初级",
        "learning_goal": "掌握深度学习基础",
        "learning_history": [],
        "cognitive_style": "视觉型",
        "weakness": ["数学推导"],
        "interest": ["计算机视觉"],
        "memory_strength": "{}",
    }


@pytest.fixture
def sample_records():
    now = datetime.now(timezone.utc)
    return [
        {"action": "view", "topic": "线性回归", "score": None, "time_spent": 1800,
         "created_at": now.isoformat()},
        {"action": "complete", "topic": "线性回归", "score": 0.85, "time_spent": 3600,
         "created_at": now.isoformat()},
        {"action": "answer", "topic": "梯度下降", "score": 0.60, "time_spent": 2400,
         "created_at": now.isoformat()},
        {"action": "answer", "topic": "梯度下降", "score": 0.45, "time_spent": 1200,
         "created_at": now.isoformat()},
        {"action": "view", "topic": "神经网络基础", "score": None, "time_spent": 900,
         "created_at": now.isoformat()},
    ]


@pytest.fixture
def sample_path():
    return {
        "goal": "掌握机器学习基础",
        "stages": [
            {"title": "阶段1: 数学基础", "objectives": "...", "topics": ["线性代数"], "tasks": []},
            {"title": "阶段2: 监督学习", "objectives": "...", "topics": ["线性回归", "逻辑回归"], "tasks": []},
            {"title": "阶段3: 深度学习", "objectives": "...", "topics": ["神经网络"], "tasks": []},
        ],
        "current_stage": 2,
    }


# ── TC-E01: 学习进度统计 ──────────────────────────────────
@pytest.mark.asyncio
async def test_progress_statistics(agent, sample_profile, sample_records, sample_path):
    """TC-E01: 评估返回 overall_score 和 dimensions"""
    raw = await agent.evaluate(
        student_id="stu_001",
        profile=sample_profile,
        records=sample_records,
        path=sample_path,
    )
    data = json.loads(raw)

    assert "overall_score" in data
    assert 0 <= data["overall_score"] <= 100
    assert "dimensions" in data
    assert isinstance(data["dimensions"], list)


# ── TC-E02: 知识掌握分析 — dimensions 含 4 维度 ───────────
@pytest.mark.asyncio
async def test_dimensions_complete(agent, sample_profile, sample_records, sample_path):
    """TC-E02: dimensions 含 knowledge_mastery / progress / efficiency / weakness_analysis"""
    raw = await agent.evaluate(
        student_id="stu_001",
        profile=sample_profile,
        records=sample_records,
        path=sample_path,
    )
    data = json.loads(raw)

    dim_names = {d["name"] for d in data["dimensions"]}
    expected = {"knowledge_mastery", "progress", "efficiency", "weakness_analysis"}
    assert dim_names == expected, f"维度名称不匹配: {dim_names}"

    for d in data["dimensions"]:
        assert "name" in d
        assert "score" in d
        assert "comment" in d
        assert 0 <= d["score"] <= 100


# ── TC-E03: 薄弱点识别 ────────────────────────────────────
@pytest.mark.asyncio
async def test_weak_topics_identified(agent, sample_profile, sample_records, sample_path):
    """TC-E03: 低分 topic 应出现在 weak_topics 中"""
    raw = await agent.evaluate(
        student_id="stu_001",
        profile=sample_profile,
        records=sample_records,
        path=sample_path,
    )
    data = json.loads(raw)

    assert "weak_topics" in data
    assert isinstance(data["weak_topics"], list)
    # 梯度下降有低分记录 (0.45, 0.60)，应被标记
    has_gradient = any("梯度下降" in w for w in data["weak_topics"])
    assert has_gradient, f"薄弱点中未检测到梯度下降: {data['weak_topics']}"


# ── TC-E04: 改进建议 ──────────────────────────────────────
@pytest.mark.asyncio
async def test_suggestions_generated(agent, sample_profile, sample_records, sample_path):
    """TC-E04: 返回具体改进建议"""
    raw = await agent.evaluate(
        student_id="stu_001",
        profile=sample_profile,
        records=sample_records,
        path=sample_path,
    )
    data = json.loads(raw)

    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) >= 1
    assert all(isinstance(s, str) for s in data["suggestions"])


# ── TC-E05: review_plan 遗忘曲线复习 ─────────────────────
@pytest.mark.asyncio
async def test_review_plan_generated(agent, sample_profile, sample_records, sample_path):
    """TC-E05: review_plan 含 topic / urgency / reason / recommended_resources"""
    raw = await agent.evaluate(
        student_id="stu_001",
        profile=sample_profile,
        records=sample_records,
        path=sample_path,
    )
    data = json.loads(raw)

    assert "review_plan" in data
    assert isinstance(data["review_plan"], list)
    for item in data["review_plan"]:
        assert "topic" in item
        assert "urgency" in item
        assert item["urgency"] in ("high", "medium", "low")
        assert "reason" in item
        assert "recommended_resources" in item


# ── TC-E06: 空记录不崩溃 ──────────────────────────────────
@pytest.mark.asyncio
async def test_empty_records_no_crash(agent, sample_profile):
    """无学习记录时 Agent 不抛出异常"""
    raw = await agent.evaluate(
        student_id="stu_001",
        profile=sample_profile,
        records=[],
        path=None,
    )
    data = json.loads(raw)
    assert "overall_score" in data
    assert data["overall_score"] > 0


# ── 遗忘曲线计算 ──────────────────────────────────────────
def test_compute_memory_strength():
    """静态方法 compute_memory_strength 返回 topic→strength 映射"""
    records = [
        {"topic": "线性回归", "score": 0.9, "created_at": datetime.now(timezone.utc).isoformat()},
        {"topic": "线性回归", "score": 0.7, "created_at": datetime.now(timezone.utc).isoformat()},
        {"topic": "梯度下降", "score": 0.4, "created_at": datetime.now(timezone.utc).isoformat()},
    ]
    strength = EvaluateAgent.compute_memory_strength(records)
    assert "线性回归" in strength
    assert "梯度下降" in strength
    # 得分低 → 记忆强度低
    assert strength["梯度下降"] < strength["线性回归"]


# ── 输出字段完整性 ────────────────────────────────────────
@pytest.mark.asyncio
async def test_output_fields_complete(agent, sample_profile, sample_records, sample_path):
    """验证 5 字段: overall_score / dimensions / weak_topics / suggestions / review_plan"""
    raw = await agent.evaluate(
        student_id="stu_001",
        profile=sample_profile,
        records=sample_records,
        path=sample_path,
    )
    data = json.loads(raw)
    required = {"overall_score", "dimensions", "weak_topics", "suggestions", "review_plan"}
    assert required.issubset(set(data.keys())), f"缺少字段: {required - set(data.keys())}"
