"""
PlannerAgent 单元测试 — TC-L01 ~ TC-L06（对齐 docs/test_plan.md §3.2）
"""
import json
import pytest
import asyncio

from backend.agents.planner_agent import PlannerAgent


@pytest.fixture
def agent():
    return PlannerAgent()  # 无 LLM，走规则化兜底


@pytest.fixture
def sample_profile():
    return {
        "knowledge_level": "初级",
        "learning_goal": "掌握机器学习基础",
        "learning_history": ["Python 基础", "线性代数入门"],
        "cognitive_style": "偏好图解和案例",
        "weakness": ["数学推导"],
        "interest": ["代码案例", "计算机视觉"],
    }


# ── TC-L01: 生成分阶段学习路径 ────────────────────────────
@pytest.mark.asyncio
async def test_generate_learning_path(agent, sample_profile):
    """TC-L01: 基于画像生成分阶段路径"""
    raw = await agent.generate_plan(profile=sample_profile)
    data = json.loads(raw)

    assert "goal" in data
    assert "stages" in data
    assert "current_stage" in data
    assert "estimated_days" in data
    assert len(data["stages"]) >= 1


# ── TC-L02: 阶段目标明确 ──────────────────────────────────
@pytest.mark.asyncio
async def test_stages_have_objectives(agent, sample_profile):
    """TC-L02: 每个阶段含 title / objectives / topics / tasks"""
    raw = await agent.generate_plan(profile=sample_profile)
    data = json.loads(raw)

    for stage in data["stages"]:
        assert "title" in stage
        assert "objectives" in stage
        assert "topics" in stage
        assert "tasks" in stage
        assert isinstance(stage["tasks"], list)
        for task in stage["tasks"]:
            assert "task" in task
            assert "resource_type" in task
            assert "estimated_hours" in task


# ── TC-L03: 难度适配 ──────────────────────────────────────
@pytest.mark.asyncio
async def test_difficulty_adaptation(agent):
    """TC-L03: 初级画像生成更多阶段"""
    profile_easy = {
        "knowledge_level": "初级",
        "learning_goal": "入门机器学习",
        "learning_history": [],
        "cognitive_style": "视觉型",
        "weakness": [],
        "interest": [],
    }
    profile_advanced = {
        "knowledge_level": "高级",
        "learning_goal": "深入强化学习",
        "learning_history": ["机器学习基础", "深度学习"],
        "cognitive_style": "公式推导",
        "weakness": [],
        "interest": [],
    }

    easy_raw = await agent.generate_plan(profile=profile_easy)
    adv_raw = await agent.generate_plan(profile=profile_advanced)
    easy = json.loads(easy_raw)
    adv = json.loads(adv_raw)

    # 初级应有更长预估天数
    assert easy["estimated_days"] >= adv["estimated_days"]


# ── TC-L04: 路径数据持久化格式 ────────────────────────────
@pytest.mark.asyncio
async def test_plan_json_serializable(agent, sample_profile):
    """TC-L04: Agent 输出是合法 JSON，字段类型正确"""
    raw = await agent.generate_plan(profile=sample_profile)
    data = json.loads(raw)

    assert isinstance(data["goal"], str)
    assert isinstance(data["stages"], list)
    assert isinstance(data["current_stage"], int)
    assert isinstance(data["estimated_days"], int)


# ── TC-L05: 目标覆盖 ──────────────────────────────────────
@pytest.mark.asyncio
async def test_goal_override(agent, sample_profile):
    """goal_override 应替换 learning_goal"""
    raw = await agent.generate_plan(
        profile=sample_profile,
        goal_override="完成深度学习实战项目",
    )
    data = json.loads(raw)
    assert data["goal"] == "完成深度学习实战项目"


# ── TC-L06: 空画像也能生成（不抛异常） ────────────────────
@pytest.mark.asyncio
async def test_empty_profile_no_crash(agent):
    """无画像时 Agent 不崩溃，返回基本路径"""
    raw = await agent.generate_plan(profile={})
    data = json.loads(raw)
    assert "stages" in data
    assert len(data["stages"]) >= 1


# ── 额外: tasks[] 字段稳定 ────────────────────────────────
@pytest.mark.asyncio
async def test_tasks_fields_stable(agent, sample_profile):
    """验证 stages[].tasks[] 字段命名稳定（对齐 §10.4.3）"""
    raw = await agent.generate_plan(profile=sample_profile)
    data = json.loads(raw)

    for stage in data["stages"]:
        for task in stage.get("tasks", []):
            required_keys = {"task", "resource_type", "estimated_hours"}
            assert required_keys.issubset(set(task.keys())), f"task 缺少字段: {required_keys - set(task.keys())}"
