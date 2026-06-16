"""
ProfileAgent 单元测试 — TC-P01 ~ TC-P08（对齐 docs/test_plan.md §3.1）
"""
import json
import pytest
import asyncio

from backend.agents.profile_agent import ProfileAgent


class MockLLMClient:
    """简单的 Mock LLM，返回预置的 profile JSON"""
    def __init__(self, profile_data=None):
        self.profile_data = profile_data or {
            "profile": {
                "knowledge_level": "大二，Python基础扎实，数学较弱",
                "learning_goal": "掌握机器学习基础算法",
                "cognitive_style": "视觉型（偏好图解/视频）",
                "weakness": ["数学推导", "概率论"],
                "interest": ["计算机视觉", "NLP"],
            },
            "completeness": 0.75,
            "confidence": 0.90,
            "sources": ["dialogue"],
            "next_questions": ["你每天能投入多少时间学习？"],
        }
        self.calls = []

    async def chat_stream(self, system, user, model=None):
        self.calls.append({"system": system, "user": user})
        raw = json.dumps(self.profile_data, ensure_ascii=False)
        chunk_size = max(1, len(raw) // 3)
        for i in range(0, len(raw), chunk_size):
            yield raw[i:i + chunk_size]


@pytest.fixture
def agent():
    return ProfileAgent(MockLLMClient())


def run_async(coro):
    return asyncio.run(coro)


# ── TC-P01: 首次对话构建画像 ──────────────────────────────
def test_first_chat_builds_profile(agent):
    """输入学习描述，返回完整 6 维 dict"""
    data = run_async(agent.build_profile(
        student_id="stu_001",
        message="我是大二学生，在学机器学习，数学基础不太好",
    ))

    assert data["student_id"] == "stu_001"
    assert "profile" in data
    assert data["completeness"] > 0
    assert isinstance(data["next_questions"], list)

    p = data["profile"]
    assert "knowledge_level" in p
    assert "learning_goal" in p
    assert "cognitive_style" in p
    assert "weakness" in p
    assert "interest" in p


# ── TC-P02: 多轮对话补充信息 ──────────────────────────────
def test_multi_turn_updates_completeness(agent):
    """多轮对话后 completeness 提升"""
    data1 = run_async(agent.build_profile("stu_001", "我想学AI"))

    data2 = run_async(agent.build_profile(
        "stu_001",
        "我更喜欢代码实践和项目驱动学习",
        history=["我想学AI"],
        current_profile=data1["profile"],
    ))

    assert data2["completeness"] >= data1["completeness"]


# ── TC-P03: 6 维度完整性 ──────────────────────────────────
def test_profile_six_dimensions_present(agent):
    """TC-P03: 画像始终包含 6 个维度字段"""
    data = run_async(agent.build_profile("stu_test", "入门机器学习"))
    p = data["profile"]

    for field in ["knowledge_level", "learning_goal", "cognitive_style", "weakness", "interest"]:
        assert field in p, f"缺少字段: {field}"


# ── TC-P04: 画像字段类型正确 ──────────────────────────────
def test_profile_json_serializable(agent):
    """TC-P04: Agent 返回 dict，字段类型正确"""
    data = run_async(agent.build_profile("stu_001", "test message"))

    assert isinstance(data["student_id"], str)
    assert isinstance(data["profile"], dict)
    assert isinstance(data["completeness"], (int, float))
    assert isinstance(data["next_questions"], list)


# ── TC-P06: 输出格式稳定性 ────────────────────────────────
def test_profile_output_format_stable(agent):
    """多次调用保持相同字段结构"""
    expected_keys = {"student_id", "profile", "completeness", "confidence", "sources", "next_questions"}
    for msg in ["学习机器学习", "我有编程基础", "我想学深度学习"]:
        data = run_async(agent.build_profile("stu_001", msg))
        assert expected_keys.issubset(set(data.keys()))


# ── TC-P07: 空输入处理 ────────────────────────────────────
def test_empty_message_handling(agent):
    """空消息不应抛出异常，返回基础画像"""
    data = run_async(agent.build_profile("stu_001", ""))
    assert data["student_id"] == "stu_001"
    assert data["completeness"] > 0


# ── TC-P08: 超长输入 ──────────────────────────────────────
def test_long_message_handling(agent):
    """超长消息正常处理"""
    long_msg = "我对机器学习很感兴趣，" * 50
    data = run_async(agent.build_profile("stu_001", long_msg))
    assert "error" not in data
