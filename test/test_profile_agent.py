"""Unit tests for ProfileAgent v01 —— LLM-based profile builder.

覆盖测试项: TC-P01 ~ TC-P08（见 docs/test_plan.md §3.1）
"""
import json
import sys
import os
import pytest
import asyncio

# 确保 backend 在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from agents.profile_agent import ProfileAgent


# ============================================================
# Mock LLMClient —— 模拟 chat_stream 异步流式调用
# ============================================================

class MockLLMClient:
    """可配置的 Mock LLM 客户端"""

    def __init__(self, chunks=None, should_fail=False):
        self.chunks = chunks or []
        self.should_fail = should_fail
        self.calls = []  # 记录调用历史

    async def chat_stream(self, system, user, model=None):
        self.calls.append({"system": system, "user": user, "model": model})
        if self.should_fail:
            raise RuntimeError("Mock LLM failure")
        for chunk in self.chunks:
            yield chunk


def make_mock_llm(json_obj):
    """快捷方法：创建一个返回指定 JSON 的 Mock LLM"""
    raw = json.dumps(json_obj, ensure_ascii=False)
    # 模拟流式：分 3 个 chunk 返回
    chunk_size = max(1, len(raw) // 3)
    chunks = [raw[i:i + chunk_size] for i in range(0, len(raw), chunk_size)]
    return MockLLMClient(chunks=chunks)


# ============================================================
# 测试数据
# ============================================================

VALID_LLM_JSON = {
    "profile": {
        "knowledge_level": "大二，Python基础扎实，数学较弱",
        "learning_goal": "掌握机器学习基础算法，能完成Kaggle入门赛",
        "cognitive_style": "视觉型（偏好图解/视频）",
        "weakness": ["数学推导", "概率论"],
        "interest": ["计算机视觉", "NLP"],
        "pace_preference": "中速均衡型",
    },
    "completeness": 0.75,
    "confidence": 0.90,
    "sources": ["dialogue", "learning_history"],
    "next_questions": ["你每天能投入多少时间学习？"],
}

MINIMAL_LLM_JSON = {
    "profile": {
        "knowledge_level": "初级",
        "learning_goal": "了解AI基础概念",
        "cognitive_style": "未明确",
        "weakness": [],
        "interest": [],
        "pace_preference": "中速均衡型",
    },
    "completeness": 0.3,
    "confidence": 0.5,
    "sources": ["dialogue"],
    "next_questions": [
        "你之前学过哪些编程或数学课程？",
        "你更偏好看书、看视频还是动手做项目？",
    ],
}


# ============================================================
# 通用 fixture
# ============================================================

@pytest.fixture
def agent_llm():
    """带有效 LLM 响应的 ProfileAgent"""
    return ProfileAgent(make_mock_llm(VALID_LLM_JSON))


@pytest.fixture
def agent_fallback():
    """LLM 失败的 ProfileAgent（触发 keyword fallback）"""
    return ProfileAgent(MockLLMClient(should_fail=True))


@pytest.fixture
def agent_minimal():
    """返回最低画像的 ProfileAgent"""
    return ProfileAgent(make_mock_llm(MINIMAL_LLM_JSON))


# ============================================================
# TC-P07~P08: Agent 基础属性
# ============================================================

class TestAgentIdentity:
    """Agent 名称与 system prompt"""

    def test_agent_name(self, agent_llm):
        assert agent_llm.name == "ProfileAgent"

    def test_system_prompt_contains_dimensions(self, agent_llm):
        prompt = agent_llm.get_system_prompt()
        assert "knowledge_level" in prompt
        assert "learning_goal" in prompt
        assert "cognitive_style" in prompt
        assert "weakness" in prompt
        assert "interest" in prompt
        assert "pace_preference" in prompt

    def test_system_prompt_mentions_output_format(self, agent_llm):
        prompt = agent_llm.get_system_prompt()
        assert "JSON" in prompt
        assert "next_questions" in prompt
        assert "completeness" in prompt

    def test_system_prompt_mentions_incremental_update(self, agent_llm):
        prompt = agent_llm.get_system_prompt()
        assert "增量更新" in prompt or "已有画像" in prompt

    def test_system_prompt_mentions_confidence(self, agent_llm):
        prompt = agent_llm.get_system_prompt()
        assert "confidence" in prompt.lower()


# ============================================================
# TC-P01~P03: LLM 路径 —— 正常画像构建
# ============================================================

class TestBuildProfileLLM:
    """LLM 正常返回时的画像构建"""

    def test_returns_valid_dict(self, agent_llm):
        result = asyncio.run(
            agent_llm.build_profile("s001", "我是大二学生，在学机器学习")
        )
        assert isinstance(result, dict)
        assert result["student_id"] == "s001"

    def test_profile_has_six_dimensions(self, agent_llm):
        result = asyncio.run(
            agent_llm.build_profile("s001", "我喜欢动手做项目，数学一般")
        )
        p = result["profile"]
        assert "knowledge_level" in p
        assert "learning_goal" in p
        assert "learning_history" in p
        assert "cognitive_style" in p
        assert "weakness" in p
        assert "interest" in p
        assert "pace_preference" in p

    def test_llm_result_preserved(self, agent_llm):
        """LLM 返回的值应原样传递"""
        result = asyncio.run(
            agent_llm.build_profile("s001", "随便说点什么")
        )
        assert result["profile"]["knowledge_level"] == VALID_LLM_JSON["profile"]["knowledge_level"]
        assert result["completeness"] == 0.75
        assert result["confidence"] == 0.90

    def test_history_passed_to_llm(self, agent_llm):
        history = ["学过Python基础", "完成线性代数练习"]
        asyncio.run(
            agent_llm.build_profile("s001", "继续学AI", history=history)
        )
        # 验证 user prompt 中包含历史记录
        user_prompt = agent_llm.llm_client.calls[-1]["user"]
        assert "学过Python基础" in user_prompt
        assert "线性代数" in user_prompt

    def test_current_profile_passed_to_llm(self, agent_llm):
        existing = {"profile": {"knowledge_level": "初级"}}
        asyncio.run(
            agent_llm.build_profile("s001", "我进步了", current_profile=existing)
        )
        user_prompt = agent_llm.llm_client.calls[-1]["user"]
        assert "已有画像" in user_prompt
        assert "初级" in user_prompt

    def test_next_questions_returned(self, agent_llm):
        result = asyncio.run(
            agent_llm.build_profile("s001", "test")
        )
        assert len(result["next_questions"]) == 1
        assert "时间" in result["next_questions"][0]


# ============================================================
# TC-P05: 增量更新
# ============================================================

class TestIncrementalUpdate:
    """画像增量更新"""

    def test_history_merged_into_profile(self, agent_llm):
        history = ["第1课", "第2课"]
        result = asyncio.run(
            agent_llm.build_profile("s001", "test", history=history)
        )
        # LLM JSON 不包含 learning_history，应由 build_profile 补充
        assert result["profile"]["learning_history"] == history


# ============================================================
# 降级路径 —— keyword fallback
# ============================================================

class TestKeywordFallback:
    """LLM 不可用时的关键字规则降级"""

    def test_returns_dict_on_failure(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "测试")
        )
        assert isinstance(result, dict)
        assert result["student_id"] == "s001"
        assert result["confidence"] == 0.4
        assert result["sources"] == ["keyword_fallback"]

    def test_beginner_detected(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "我是零基础入门学习者")
        )
        assert result["profile"]["knowledge_level"] == "初级"

    def test_advanced_detected(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "想学进阶内容，深入理解原理")
        )
        assert result["profile"]["knowledge_level"] == "中高级"

    def test_project_practice_style(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "我想做项目实践，多动手")
        )
        assert "实践项目" in result["profile"]["learning_goal"]
        assert "动手" in result["profile"]["cognitive_style"]

    def test_math_weakness(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "我对数学推导和公式不太懂")
        )
        assert "数学推导" in result["profile"]["weakness"]

    def test_probability_weakness(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "概率统计很难")
        )
        assert any("概率" in w for w in result["profile"]["weakness"])

    def test_code_interest(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "我喜欢编程和写代码")
        )
        assert "代码案例" in result["profile"]["interest"]

    def test_video_visual_style(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "我喜欢看视频学习")
        )
        assert "视觉" in result["profile"]["cognitive_style"]

    def test_fast_pace(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "我想速成，快一点学完")
        )
        assert result["profile"]["pace_preference"] == "快速概览型"

    def test_slow_pace(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "我想慢慢学，仔细理解每个概念")
        )
        assert result["profile"]["pace_preference"] == "慢速深入型"

    def test_case_insensitive(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "入门")
        )
        assert result["profile"]["knowledge_level"] == "初级"

    def test_next_questions_present(self, agent_fallback):
        result = asyncio.run(
            agent_fallback.build_profile("s001", "测试")
        )
        assert len(result["next_questions"]) >= 2


# ============================================================
# JSON 解析器
# ============================================================

class TestParseLLMJson:
    """_parse_llm_json 各种输入格式的健壮性"""

    def test_pure_json(self, agent_llm):
        result = agent_llm._parse_llm_json('{"a": 1}')
        assert result == {"a": 1}

    def test_json_in_markdown_code_block(self, agent_llm):
        result = agent_llm._parse_llm_json('```json\n{"a": 1}\n```')
        assert result == {"a": 1}

    def test_json_in_code_block_no_lang(self, agent_llm):
        result = agent_llm._parse_llm_json('```\n{"a": 1}\n```')
        assert result == {"a": 1}

    def test_json_with_surrounding_text(self, agent_llm):
        result = agent_llm._parse_llm_json(
            '好的，这是学生画像：\n{"profile": {"knowledge_level": "初级"}}\n希望对你有所帮助。'
        )
        assert result["profile"]["knowledge_level"] == "初级"

    def test_trailing_comma_recovery(self, agent_llm):
        """尾部逗号应被清理后解析"""
        result = agent_llm._parse_llm_json('{"a": 1,}')
        assert result == {"a": 1}

    def test_trailing_comma_in_array(self, agent_llm):
        result = agent_llm._parse_llm_json('{"a": [1, 2,]}')
        assert result == {"a": [1, 2]}

    def test_empty_string_returns_none(self, agent_llm):
        assert agent_llm._parse_llm_json("") is None

    def test_whitespace_only_returns_none(self, agent_llm):
        assert agent_llm._parse_llm_json("   \n  ") is None

    def test_no_braces_returns_none(self, agent_llm):
        assert agent_llm._parse_llm_json("这里没有JSON对象") is None


# ============================================================
# 流式 chat() 方法
# ============================================================

class TestChatStreaming:
    """SSE 流式对话"""

    def test_yields_chat_events(self, agent_llm):
        async def collect():
            events = []
            async for evt in agent_llm.chat("s001", "hello"):
                events.append(evt)
            return events

        events = asyncio.run(collect())
        assert len(events) >= 3  # 至少 3 个 chunk + profile_update + done

    def test_chat_contains_profile_update(self, agent_llm):
        async def collect():
            events = []
            async for evt in agent_llm.chat("s001", "hello"):
                events.append(evt)
            return events

        events = asyncio.run(collect())
        profile_updates = [e for e in events if "profile_update" in e]
        assert len(profile_updates) == 1

    def test_chat_contains_done(self, agent_llm):
        async def collect():
            events = []
            async for evt in agent_llm.chat("s001", "hello"):
                events.append(evt)
            return events

        events = asyncio.run(collect())
        assert any("done" in e for e in events)

    def test_chat_fallback_on_llm_failure(self, agent_fallback):
        async def collect():
            events = []
            async for evt in agent_fallback.chat("s001", "hello"):
                events.append(evt)
            return events

        events = asyncio.run(collect())
        assert any("profile_update" in e for e in events)
        assert any("done" in e for e in events)


# ============================================================
# 低完整性画像的追问
# ============================================================

class TestLowCompleteness:
    """低完整性画像自带追问"""

    def test_minimal_profile_has_questions(self, agent_minimal):
        result = asyncio.run(
            agent_minimal.build_profile("s001", "我想学AI")
        )
        assert result["completeness"] == 0.3
        assert len(result["next_questions"]) >= 2
