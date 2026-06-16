"""
ProfileAgent 单元测试 — TC-P01 ~ TC-P08（对齐 docs/test_plan.md §3.1）
"""
import json
import pytest

from backend.agents.profile_agent import ProfileAgent


@pytest.fixture
def agent():
    return ProfileAgent()


# ── TC-P01: 首次对话构建画像 ──────────────────────────────
def test_first_chat_builds_profile(agent):
    """输入学习描述，返回完整 6 维 JSON"""
    raw = agent.build_profile(
        student_id="stu_001",
        message="我是大二学生，在学机器学习，数学基础不太好",
    )
    data = json.loads(raw)

    assert data["student_id"] == "stu_001"
    assert "profile" in data
    assert data["completeness"] > 0
    assert isinstance(data["next_questions"], list)
    assert len(data["next_questions"]) >= 1

    p = data["profile"]
    assert "knowledge_level" in p
    assert "learning_goal" in p
    assert "learning_history" in p
    assert "cognitive_style" in p
    assert "weakness" in p
    assert "interest" in p


# ── TC-P02: 多轮对话补充信息 ──────────────────────────────
def test_multi_turn_updates_completeness(agent):
    """多轮对话后 completeness 提升"""
    raw1 = agent.build_profile("stu_001", "我想学AI")
    data1 = json.loads(raw1)

    raw2 = agent.build_profile(
        "stu_001",
        "我更喜欢代码实践和项目驱动学习",
        history=["我想学AI"],
        current_profile=data1["profile"],
    )
    data2 = json.loads(raw2)

    assert data2["completeness"] >= data1["completeness"]


# ── TC-P03: 6 维度完整性 ──────────────────────────────────
def test_profile_six_dimensions_present(agent):
    """TC-P03: 画像始终包含 6 个维度字段"""
    raw = agent.build_profile("stu_test", "入门机器学习")
    data = json.loads(raw)
    p = data["profile"]

    required_fields = [
        "knowledge_level",
        "learning_goal",
        "learning_history",
        "cognitive_style",
        "weakness",
        "interest",
    ]
    for field in required_fields:
        assert field in p, f"缺少字段: {field}"


# ── TC-P04: 画像可持久化（JSON 可解析 + 字段类型正确） ────
def test_profile_json_serializable(agent):
    """TC-P04: Agent 输出必须是合法 JSON"""
    raw = agent.build_profile("stu_001", "测试输入")
    data = json.loads(raw)

    assert isinstance(data["student_id"], str)
    assert isinstance(data["profile"], dict)
    assert isinstance(data["completeness"], (int, float))
    assert isinstance(data["next_questions"], list)


# ── TC-P06: 输出格式稳定性 ────────────────────────────────
def test_profile_output_format_stable(agent):
    """多次调用保持相同字段结构"""
    for msg in ["学习机器学习", "我有编程基础", "我想学深度学习"]:
        raw = agent.build_profile("stu_001", msg)
        data = json.loads(raw)
        assert set(data.keys()) == {"student_id", "profile", "completeness", "next_questions"}


# ── TC-P07: 空输入处理 ────────────────────────────────────
def test_empty_message_handling(agent):
    """空消息不应抛出异常，返回基础画像"""
    raw = agent.build_profile("stu_001", "")
    data = json.loads(raw)
    assert data["student_id"] == "stu_001"
    assert data["completeness"] > 0


# ── TC-P08: 超长输入 ──────────────────────────────────────
def test_long_message_handling(agent):
    """超长消息正常处理"""
    long_msg = "我对机器学习很感兴趣，" * 50
    raw = agent.build_profile("stu_001", long_msg)
    data = json.loads(raw)
    assert "error" not in data
