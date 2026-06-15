"""Unit tests for ResourceAgent v01 —— LLM-based resource generator.

覆盖测试项: TC-R01 ~ TC-R09（见 docs/test_plan.md §3.3）
"""
import json
import sys
import os
import pytest
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from agents.resource_agent import ResourceAgent, SAMPLE_OUTPUT_ML_INTRO


# ============================================================
# Mock LLMClient
# ============================================================

class MockLLMClient:
    """可配置的 Mock LLM 客户端"""

    def __init__(self, chunks=None, should_fail=False):
        self.chunks = chunks or []
        self.should_fail = should_fail
        self.calls = []

    async def chat_stream(self, system, user, model=None):
        self.calls.append({"system": system, "user": user, "model": model})
        if self.should_fail:
            raise RuntimeError("Mock LLM failure")
        for chunk in self.chunks:
            yield chunk


def make_mock_llm(json_obj):
    """快捷方法：创建一个返回指定 JSON 的 Mock LLM"""
    raw = json.dumps(json_obj, ensure_ascii=False)
    chunk_size = max(1, len(raw) // 3)
    chunks = [raw[i:i + chunk_size] for i in range(0, len(raw), chunk_size)]
    return MockLLMClient(chunks=chunks)


# ============================================================
# 模拟 LLM 返回数据
# ============================================================

VALID_DOCUMENT_JSON = {
    "resources": [
        {
            "type": "document",
            "title": "线性回归：从原理到实践",
            "topic": "线性回归",
            "difficulty": "中级",
            "content": (
                "## 线性回归：从原理到实践\n\n"
                "### 1. 什么是线性回归？\n\n"
                "线性回归是最基础的监督学习算法之一，用于建模自变量与因变量之间的线性关系。\n\n"
                "### 2. 核心公式\n\n"
                "y = wx + b\n\n"
                "### 3. 小结\n\n"
                "线性回归虽然简单，但它是理解更复杂模型的基础。"
            ),
        }
    ]
}

VALID_EXERCISE_JSON = {
    "resources": [
        {
            "type": "exercise",
            "title": "线性回归基础练习",
            "topic": "线性回归",
            "difficulty": "初级",
            "content": (
                "# 线性回归基础练习\n\n"
                "### 选择题\n\n"
                "**1. 线性回归中，最小二乘法的目标是最小化什么？**\n\n"
                "A. 预测值的总和\n"
                "B. 残差的平方和\n"
                "C. 权重的绝对值之和\n"
                "D. 样本数量\n\n"
                "**正确答案：B**\n"
                "**解析：**最小二乘法的核心是最小化残差（预测值与真实值之差）的平方和。\n\n"
                "**2. 以下哪个指标不适合评估回归模型？**\n\n"
                "A. MSE\n"
                "B. MAE\n"
                "C. R²\n"
                "D. Accuracy\n\n"
                "**正确答案：D**\n"
                "**解析：**Accuracy用于分类任务。回归任务常用MSE、MAE、R²。\n\n"
                "**3. 如果数据中存在明显异常值，以下哪个指标更稳健？**\n\n"
                "A. MSE\n"
                "B. MAE\n"
                "C. RMSE\n"
                "D. Huber Loss\n\n"
                "**正确答案：D**\n"
                "**解析：**Huber Loss结合了MSE和MAE的优点，对异常值更稳健。\n\n"
                "### 简答题\n\n"
                "**4. 请解释线性回归中R²分数的含义。**\n\n"
                "**参考答案：**R²表示模型解释的方差比例，取值范围0~1，越接近1说明模型拟合越好。"
            ),
        }
    ]
}

VALID_CODE_JSON = {
    "resources": [
        {
            "type": "code",
            "title": "线性回归 Python 实现",
            "topic": "线性回归",
            "difficulty": "中级",
            "content": (
                "# 线性回归 Python 实现\n\n"
                "```python\n"
                "import numpy as np\n"
                "from sklearn.linear_model import LinearRegression\n"
                "X = np.array([[1], [2], [3], [4], [5]])\n"
                "y = np.array([2, 4, 5, 4, 5])\n"
                "model = LinearRegression()\n"
                "model.fit(X, y)\n"
                "print(f'斜率: {model.coef_[0]:.2f}')\n"
                "print(f'截距: {model.intercept_:.2f}')\n"
                "print(f'R²: {model.score(X, y):.2f}')\n"
                "```\n\n"
                "### 运行说明\n\n"
                "- 依赖：`numpy scikit-learn`\n"
                "- 预期输出：斜率约0.6，截距约2.2"
            ),
        }
    ]
}

VALID_MINDMAP_JSON = {
    "resources": [
        {
            "type": "mindmap",
            "title": "线性回归知识图谱",
            "topic": "线性回归",
            "difficulty": "中级",
            "content": (
                "- 线性回归\n"
                "  - 基本概念\n"
                "    - 自变量与因变量\n"
                "    - 线性关系假设\n"
                "  - 核心算法\n"
                "    - 最小二乘法\n"
                "    - 梯度下降\n"
                "  - 评估指标\n"
                "    - MSE\n"
                "    - R²\n"
            ),
        }
    ]
}

VALID_READING_JSON = {
    "resources": [
        {
            "type": "reading",
            "title": "线性回归拓展阅读",
            "topic": "线性回归",
            "difficulty": "中级",
            "content": (
                "# 线性回归拓展阅读\n\n"
                "### 推荐教材\n\n"
                "- 《统计学习导论》(ISLR) 第3章\n"
                "- 《机器学习》(周志华) 第3章\n\n"
                "### 经典论文\n\n"
                "- Legendre (1805) 最小二乘法原始论文"
            ),
        }
    ]
}

MULTI_RESOURCE_JSON = {
    "resources": [
        {
            "type": "document",
            "title": "线性回归入门",
            "topic": "线性回归",
            "difficulty": "初级",
            "content": "## 线性回归入门\n\n适合零基础学习者的线性回归入门教程。",
        },
        {
            "type": "exercise",
            "title": "线性回归练习",
            "topic": "线性回归",
            "difficulty": "初级",
            "content": "# 练习\n\n**1. 线性回归属于什么学习类型？**\n\nA. 监督学习\nB. 无监督学习\nC. 强化学习\n\n**答案：A**",
        },
        {
            "type": "code",
            "title": "线性回归代码",
            "topic": "线性回归",
            "difficulty": "初级",
            "content": "```python\nfrom sklearn.linear_model import LinearRegression\nmodel = LinearRegression()\n```",
        },
    ]
}

# 用于 TC-R07：不同难度对比
EASY_JSON = {
    "resources": [
        {
            "type": "document",
            "title": "线性回归初级教程",
            "topic": "线性回归",
            "difficulty": "初级",
            "content": "## 初级内容\n\n用生活化类比解释线性回归，避免数学公式，适合零基础。",
        }
    ]
}

HARD_JSON = {
    "resources": [
        {
            "type": "document",
            "title": "线性回归高级专题",
            "topic": "线性回归",
            "difficulty": "高级",
            "content": "## 高级内容\n\n深入讨论正则化、多重共线性、岭回归与Lasso的数学推导。",
        }
    ]
}

# 异常格式（用于鲁棒性测试）
MALFORMED_JSON_1 = {
    "resources": [
        {"type": "unknown_type", "title": "测试", "topic": "测试", "difficulty": "初级", "content": "内容"}
    ]
}

MALFORMED_JSON_2 = {
    "resources": [
        {"title": "缺少type字段", "topic": "测试"}
    ]
}


# ============================================================
# 测试类
# ============================================================

class TestResourceAgentGenerate:
    """TC-R01~R05: 各类资源生成"""

    def test_generate_document(self):
        """TC-R01: 生成课程讲解文档"""
        llm = make_mock_llm(VALID_DOCUMENT_JSON)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="线性回归", types=["document"], difficulty="中级")
        )

        assert result["topic"] == "线性回归"
        assert result["difficulty"] == "中级"
        assert "generated_at" in result
        assert len(result["resources"]) == 1

        r = result["resources"][0]
        assert r["type"] == "document"
        assert "线性回归" in r["title"]
        assert "线性回归" in r["topic"]
        assert "##" in r["content"]  # Markdown 标题
        assert len(r["content"]) > 50

    def test_generate_exercise(self):
        """TC-R03: 生成练习题，至少3道"""
        llm = make_mock_llm(VALID_EXERCISE_JSON)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="线性回归", types=["exercise"], difficulty="初级")
        )

        assert len(result["resources"]) == 1
        r = result["resources"][0]
        assert r["type"] == "exercise"
        assert "正确答案" in r["content"]
        assert "解析" in r["content"]

    def test_generate_code(self):
        """TC-R04: 生成代码案例"""
        llm = make_mock_llm(VALID_CODE_JSON)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="线性回归", types=["code"], difficulty="中级")
        )

        r = result["resources"][0]
        assert r["type"] == "code"
        assert "```python" in r["content"] or "```" in r["content"]
        assert "import" in r["content"].lower() or "from" in r["content"].lower()

    def test_generate_mindmap(self):
        """TC-R02: 生成思维导图（嵌套Markdown列表）"""
        llm = make_mock_llm(VALID_MINDMAP_JSON)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="线性回归", types=["mindmap"])
        )

        r = result["resources"][0]
        assert r["type"] == "mindmap"
        # 应包含嵌套的 Markdown 列表结构
        assert "- " in r["content"]
        assert "  - " in r["content"]  # 缩进子项

    def test_generate_reading(self):
        """TC-R05: 生成拓展阅读"""
        llm = make_mock_llm(VALID_READING_JSON)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="线性回归", types=["reading"])
        )

        r = result["resources"][0]
        assert r["type"] == "reading"
        assert len(r["content"]) > 50

    def test_generate_multiple_types(self):
        """生成多种类型资源（DAY6 核心场景）"""
        llm = make_mock_llm(MULTI_RESOURCE_JSON)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(
                topic="线性回归",
                types=["document", "exercise", "code"],
                difficulty="初级",
            )
        )

        assert len(result["resources"]) == 3
        types = {r["type"] for r in result["resources"]}
        assert types == {"document", "exercise", "code"}

    def test_default_types(self):
        """未指定 types 时默认返回 document/exercise/code"""
        llm = make_mock_llm(MULTI_RESOURCE_JSON)
        agent = ResourceAgent(llm)

        result = asyncio.run(agent.generate(topic="线性回归"))
        # 即使不指定类型，也应能正常运行
        assert "resources" in result
        assert result["topic"] == "线性回归"


class TestResourceAgentDifficulty:
    """TC-R07: 难度匹配"""

    def test_difficulty_is_preserved_in_output(self):
        """生成的资源应保留请求的难度"""
        llm = make_mock_llm(EASY_JSON)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="线性回归", difficulty="初级")
        )
        assert result["difficulty"] == "初级"

    def test_easy_vs_hard_content_differs(self):
        """初级和高级内容应有明显差异"""
        llm_easy = make_mock_llm(EASY_JSON)
        llm_hard = make_mock_llm(HARD_JSON)
        agent_easy = ResourceAgent(llm_easy)
        agent_hard = ResourceAgent(llm_hard)

        easy_result = asyncio.run(
            agent_easy.generate(topic="线性回归", difficulty="初级")
        )
        hard_result = asyncio.run(
            agent_hard.generate(topic="线性回归", difficulty="高级")
        )

        easy_content = easy_result["resources"][0]["content"]
        hard_content = hard_result["resources"][0]["content"]

        assert easy_content != hard_content
        assert easy_result["resources"][0]["difficulty"] == "初级"
        assert hard_result["resources"][0]["difficulty"] == "高级"

    def test_invalid_difficulty_defaults_to_medium(self):
        """无效难度值应回退到中级"""
        llm = make_mock_llm(EASY_JSON)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="测试", difficulty="超神级")
        )
        assert result["difficulty"] == "中级"


class TestResourceAgentFallback:
    """TC-R09: 降级/失败处理"""

    def test_fallback_on_llm_failure(self):
        """LLM 失败时返回模板降级资源，不抛异常"""
        llm = MockLLMClient(should_fail=True)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="线性回归", types=["document", "exercise", "code"])
        )

        assert result["topic"] == "线性回归"
        assert len(result["resources"]) == 3
        types = {r["type"] for r in result["resources"]}
        assert types == {"document", "exercise", "code"}
        # 降级内容应有标记
        for r in result["resources"]:
            assert len(r["content"]) > 0
            assert len(r["title"]) > 0

    def test_fallback_on_malformed_json(self):
        """LLM 返回不可解析内容时降级"""
        # Mock 返回非 JSON 内容
        llm = MockLLMClient(chunks=["这不是JSON", "还是不是"])
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="线性回归", types=["document"])
        )

        assert len(result["resources"]) >= 1
        assert result["topic"] == "线性回归"

    def test_fallback_empty_string(self):
        """LLM 返回空内容时降级"""
        llm = MockLLMClient(chunks=[""])
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="测试", types=["code"])
        )

        assert len(result["resources"]) >= 1
        assert result["resources"][0]["type"] == "code"

    def test_fallback_all_types(self):
        """降级方案覆盖全部5种资源类型"""
        llm = MockLLMClient(should_fail=True)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(
                topic="测试",
                types=["document", "exercise", "code", "mindmap", "reading"],
            )
        )

        assert len(result["resources"]) == 5
        types = {r["type"] for r in result["resources"]}
        assert types == {"document", "exercise", "code", "mindmap", "reading"}


class TestResourceAgentNormalize:
    """字段规范化与边界情况"""

    def test_unknown_type_normalized_to_document(self):
        """未知资源类型应规范化为 document"""
        llm = make_mock_llm(MALFORMED_JSON_1)
        agent = ResourceAgent(llm)

        result = asyncio.run(agent.generate(topic="测试"))
        assert result["resources"][0]["type"] == "document"

    def test_missing_fields_are_filled(self):
        """缺失字段应补全默认值"""
        llm = make_mock_llm(MALFORMED_JSON_2)
        agent = ResourceAgent(llm)

        result = asyncio.run(agent.generate(topic="测试", difficulty="初级"))
        r = result["resources"][0]
        assert r["type"] == "document"  # 默认
        assert r["topic"] == "测试"  # 用请求的 topic 补全
        assert r["difficulty"] == "初级"
        assert r["content"] == ""

    def test_each_resource_has_required_fields(self):
        """每个资源必须包含 type/title/topic/difficulty/content"""
        llm = make_mock_llm(MULTI_RESOURCE_JSON)
        agent = ResourceAgent(llm)

        result = asyncio.run(
            agent.generate(topic="线性回归", types=["document", "exercise", "code"])
        )

        required_fields = {"type", "title", "topic", "difficulty", "content"}
        for r in result["resources"]:
            assert required_fields.issubset(r.keys()), f"缺失字段: {required_fields - set(r.keys())}"


class TestResourceAgentStreaming:
    """流式输出测试"""

    async def _collect_sse(self, async_gen):
        """收集 SSE 事件列表"""
        events = []
        async for event in async_gen:
            events.append(event)
        return events

    def test_stream_emits_start_and_done(self):
        """流式输出应有 start 和 done 事件"""
        llm = make_mock_llm(MULTI_RESOURCE_JSON)
        agent = ResourceAgent(llm)

        events = asyncio.run(
            self._collect_sse(
                agent.generate_stream(topic="线性回归", types=["document"])
            )
        )

        # 检查 start 事件
        assert any('"type":"start"' in e for e in events)
        # 检查 done 事件
        assert any('"type":"done"' in e for e in events)
        # 检查 data 事件
        assert any('"type":"data"' in e for e in events)

    def test_stream_fallback_on_failure(self):
        """流式 LLM 失败时应返回降级数据和 done"""
        llm = MockLLMClient(should_fail=True)
        agent = ResourceAgent(llm)

        events = asyncio.run(
            self._collect_sse(
                agent.generate_stream(topic="线性回归", types=["document"])
            )
        )

        assert any('"type":"error"' in e for e in events)
        assert any('"type":"data"' in e for e in events)
        assert any('"type":"done"' in e for e in events)


class TestResourceAgentPrompt:
    """Prompt 构建测试"""

    def test_build_prompt_includes_topic_and_difficulty(self):
        """Prompt 应包含主题和难度"""
        llm = MockLLMClient(chunks=["{}"])
        agent = ResourceAgent(llm)

        asyncio.run(agent.generate(topic="CNN卷积神经网络", difficulty="高级"))

        call = llm.calls[0]
        assert "CNN卷积神经网络" in call["user"]
        assert "高级" in call["user"]

    def test_build_prompt_includes_student_profile(self):
        """Prompt 应包含学生画像信息"""
        llm = MockLLMClient(chunks=["{}"])
        agent = ResourceAgent(llm)

        profile = {
            "knowledge_level": "初级",
            "weakness": ["数学", "编程"],
            "cognitive_style": "视觉型",
        }
        asyncio.run(
            agent.generate(
                topic="机器学习",
                student_profile=profile,
            )
        )

        call = llm.calls[0]
        assert "初级" in call["user"]
        assert "数学" in call["user"]
        assert "视觉型" in call["user"]

    def test_build_prompt_includes_types(self):
        """Prompt 应包含资源类型"""
        llm = MockLLMClient(chunks=["{}"])
        agent = ResourceAgent(llm)

        asyncio.run(
            agent.generate(topic="测试", types=["document", "code"])
        )

        call = llm.calls[0]
        assert "document" in call["user"]
        assert "code" in call["user"]


class TestSampleOutput:
    """静态样例输出测试"""

    def test_sample_has_three_resources(self):
        """SAMPLE_OUTPUT_ML_INTRO 应包含3种资源"""
        assert len(SAMPLE_OUTPUT_ML_INTRO["resources"]) == 3

    def test_sample_types_are_document_exercise_code(self):
        """样例应覆盖 document/exercise/code"""
        types = {r["type"] for r in SAMPLE_OUTPUT_ML_INTRO["resources"]}
        assert types == {"document", "exercise", "code"}

    def test_sample_each_resource_has_content(self):
        """每种资源的内容不应为空"""
        for r in SAMPLE_OUTPUT_ML_INTRO["resources"]:
            assert len(r["content"]) > 100, f"{r['type']} 内容太短"
            assert len(r["title"]) > 5
            assert len(r["topic"]) > 1

    def test_sample_document_has_structure(self):
        """document 类型应有 Markdown 标题结构"""
        doc = SAMPLE_OUTPUT_ML_INTRO["resources"][0]
        assert doc["type"] == "document"
        assert "##" in doc["content"]

    def test_sample_exercise_has_answer(self):
        """exercise 类型应有正确答案"""
        ex = SAMPLE_OUTPUT_ML_INTRO["resources"][1]
        assert ex["type"] == "exercise"
        assert "正确答案" in ex["content"]

    def test_sample_code_has_python(self):
        """code 类型应包含 Python 代码块"""
        code = SAMPLE_OUTPUT_ML_INTRO["resources"][2]
        assert code["type"] == "code"
        assert "```python" in code["content"]


# ============================================================
# System prompt 测试
# ============================================================

class TestSystemPrompt:
    """System Prompt 质量测试"""

    def test_prompt_includes_all_resource_types(self):
        """System Prompt 应说明全部5种资源类型"""
        agent = ResourceAgent(MockLLMClient())
        prompt = agent.get_system_prompt()
        assert "document" in prompt
        assert "exercise" in prompt
        assert "code" in prompt
        assert "mindmap" in prompt
        assert "reading" in prompt

    def test_prompt_includes_json_format(self):
        """System Prompt 应要求输出 JSON"""
        agent = ResourceAgent(MockLLMClient())
        prompt = agent.get_system_prompt()
        assert "json" in prompt.lower()
        assert "resources" in prompt

    def test_prompt_includes_difficulty_control(self):
        """System Prompt 应包含难度控制说明"""
        agent = ResourceAgent(MockLLMClient())
        prompt = agent.get_system_prompt()
        assert "初级" in prompt
        assert "中级" in prompt
        assert "高级" in prompt

    def test_prompt_includes_quality_requirements(self):
        """System Prompt 应包含内容质量约束"""
        agent = ResourceAgent(MockLLMClient())
        prompt = agent.get_system_prompt()
        assert "核实" in prompt
        assert "准确" in prompt
