"""Unit tests for PlannerAgent v01 —— LLM-based learning path planner.

覆盖测试项: TC-L01 ~ TC-L06（见 docs/test_plan.md §3.2）
"""
import json
import sys
import os
import pytest
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from agents.planner_agent import PlannerAgent


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
    """创建一个返回指定 JSON 的 Mock LLM（分多 chunk 流式返回）"""
    raw = json.dumps(json_obj, ensure_ascii=False)
    chunk_size = max(1, len(raw) // 3)
    chunks = [raw[i:i + chunk_size] for i in range(0, len(raw), chunk_size)]
    return MockLLMClient(chunks=chunks)


# ============================================================
# 测试画像数据
# ============================================================

BEGINNER_PROFILE = {
    "knowledge_level": "初级，大二学生，Python基础入门，数学薄弱",
    "learning_goal": "掌握机器学习基础算法，能完成Kaggle入门赛",
    "cognitive_style": "视觉型（偏好图解/视频）",
    "weakness": ["数学推导", "概率论"],
    "interest": ["计算机视觉", "NLP"],
    "pace_preference": "中速均衡型",
    "learning_history": [],
}

ADVANCED_PROFILE = {
    "knowledge_level": "中高级，大三计算机专业，Java/Python熟练，ML概念有科普级了解",
    "learning_goal": "6个月内系统掌握ML/DL核心算法，Kaggle参赛，重点NLP方向",
    "cognitive_style": "动手型（偏好代码实现）",
    "weakness": ["数学推导"],
    "interest": ["NLP", "大语言模型", "对话系统", "Kaggle竞赛"],
    "pace_preference": "快速概览型",
    "learning_history": [],
}

MINIMAL_PROFILE = {
    "knowledge_level": "中级",
    "learning_goal": "了解AI基础概念",
    "cognitive_style": "未明确",
    "weakness": [],
    "interest": [],
    "pace_preference": "中速均衡型",
    "learning_history": [],
}

EMPTY_PROFILE = {
    "knowledge_level": "",
    "learning_goal": "",
    "weakness": [],
    "interest": [],
}

SPARSE_PROFILE = {
    "knowledge_level": "中级",
    "learning_goal": "了解机器学习",
}


# ============================================================
# LLM 模拟返回数据
# ============================================================

VALID_PATH_JSON = {
    "goal": "掌握机器学习基础算法，能完成Kaggle入门赛",
    "stages": [
        {
            "stage_id": 1,
            "title": "数学基础补强",
            "description": "针对数学推导和概率论的薄弱环节进行专项补强",
            "objectives": [
                "掌握线性代数中矩阵运算和特征值分解的核心概念",
                "理解概率论中条件概率、贝叶斯公式和常见分布",
                "能够用Python实现基础数学运算",
            ],
            "topics": ["线性代数基础", "概率论与统计", "微积分要点"],
            "tasks": [
                {
                    "task_id": "1-1",
                    "type": "study",
                    "description": "学习线性代数核心概念：矩阵、向量、特征值",
                    "estimated_minutes": 60,
                    "resource_types": ["document", "mindmap", "video"],
                },
                {
                    "task_id": "1-2",
                    "type": "exercise",
                    "description": "完成概率论基础练习题",
                    "estimated_minutes": 45,
                    "resource_types": ["document", "exercise"],
                },
            ],
            "estimated_days": 5,
            "difficulty": "初级",
            "prerequisites": [],
        },
        {
            "stage_id": 2,
            "title": "机器学习核心算法",
            "description": "系统学习主流监督学习与无监督学习算法",
            "objectives": [
                "理解并实现线性回归、逻辑回归、决策树等基础算法",
                "掌握模型评估方法与超参数调优技巧",
            ],
            "topics": ["线性回归", "决策树与随机森林", "模型评估"],
            "tasks": [
                {
                    "task_id": "2-1",
                    "type": "study",
                    "description": "学习线性回归原理与推导",
                    "estimated_minutes": 60,
                    "resource_types": ["document", "code"],
                },
            ],
            "estimated_days": 7,
            "difficulty": "中级",
            "prerequisites": [1],
        },
        {
            "stage_id": 3,
            "title": "综合实战：Kaggle入门赛",
            "description": "结合计算机视觉兴趣方向完成Kaggle竞赛项目",
            "objectives": [
                "独立完成一个完整的Kaggle竞赛流程",
                "产出可展示的项目成果",
            ],
            "topics": ["Kaggle竞赛", "特征工程", "模型集成"],
            "tasks": [
                {
                    "task_id": "3-1",
                    "type": "project",
                    "description": "完成Kaggle入门级竞赛项目",
                    "estimated_minutes": 180,
                    "resource_types": ["document", "code", "exercise"],
                },
            ],
            "estimated_days": 5,
            "difficulty": "高级",
            "prerequisites": [2],
        },
    ],
    "current_stage": 1,
    "total_estimated_days": 17,
    "difficulty_level": "中级",
    "adaptation_notes": "针对学生数学薄弱安排第一阶段基础补强，结合计算机视觉兴趣安排实战项目",
}

INCREMENTAL_PATH_JSON = {
    "goal": "掌握机器学习基础算法",
    "stages": [
        {
            "stage_id": 1,
            "title": "数学基础补强",
            "description": "已完成",
            "objectives": ["掌握线性代数基础"],
            "topics": ["线性代数"],
            "tasks": [{"task_id": "1-1", "type": "study", "description": "学习线性代数", "estimated_minutes": 60, "resource_types": ["document"]}],
            "estimated_days": 5,
            "difficulty": "初级",
            "prerequisites": [],
        },
        {
            "stage_id": 2,
            "title": "核心算法（调整后）",
            "description": "根据评估反馈增加了复习任务",
            "objectives": ["深入理解SVM和神经网络"],
            "topics": ["SVM", "神经网络"],
            "tasks": [
                {"task_id": "2-1", "type": "review", "description": "复习线性代数知识点", "estimated_minutes": 30, "resource_types": ["document"]},
                {"task_id": "2-2", "type": "study", "description": "学习SVM原理", "estimated_minutes": 90, "resource_types": ["document", "exercise"]},
            ],
            "estimated_days": 6,
            "difficulty": "中级",
            "prerequisites": [1],
        },
    ],
    "current_stage": 2,
    "total_estimated_days": 11,
    "difficulty_level": "中级",
    "adaptation_notes": "根据评估反馈在阶段2中增加了线性代数复习任务",
}


# ============================================================
# TC-L01: 生成学习路径
# ============================================================

class TestBuildPath:
    """TC-L01: 基于画像生成学习路径"""

    def test_generate_with_valid_profile(self):
        """有效画像 → 返回结构化路径"""
        llm = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm)

        result = asyncio.run(
            agent.build_path(student_id="stu_001", profile=BEGINNER_PROFILE)
        )

        assert result["student_id"] == "stu_001"
        assert len(result["goal"]) > 0
        assert len(result["stages"]) >= 2
        assert result["current_stage"] == 1
        assert result["total_estimated_days"] > 0

    def test_stages_have_required_fields(self):
        """每个阶段必须包含核心字段"""
        llm = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))

        for stage in result["stages"]:
            assert "stage_id" in stage
            assert "title" in stage and len(stage["title"]) > 0
            assert "description" in stage
            assert "objectives" in stage and len(stage["objectives"]) > 0
            assert "topics" in stage and len(stage["topics"]) > 0
            assert "tasks" in stage and len(stage["tasks"]) > 0
            assert "estimated_days" in stage
            assert "difficulty" in stage
            assert "prerequisites" in stage

    def test_stage_ids_are_sequential(self):
        """stage_id 应从 1 开始连续递增"""
        llm = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))
        ids = [s["stage_id"] for s in result["stages"]]
        assert ids == list(range(1, len(ids) + 1)), f"stage_id 不连续: {ids}"

    def test_difficulty_non_decreasing(self):
        """阶段难度应非递减"""
        llm = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))
        diff_order = {"初级": 0, "中级": 1, "高级": 2}
        difficulties = [diff_order.get(s.get("difficulty", "中级"), 1) for s in result["stages"]]
        for i in range(1, len(difficulties)):
            assert difficulties[i] >= difficulties[i - 1], f"阶段 {i+1} 难度低于前一阶段"

    def test_last_stage_is_project_or_advanced(self):
        """最后阶段应为综合实战或高级内容"""
        llm = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))
        last_stage = result["stages"][-1]
        last_title = last_stage.get("title", "").lower()
        last_diff = last_stage.get("difficulty", "")
        has_project_task = any(
            t.get("type") == "project" for t in last_stage.get("tasks", [])
        )
        assert last_diff == "高级" or has_project_task or "综合" in last_title or "实战" in last_title


# ============================================================
# TC-L02: 阶段目标明确
# ============================================================

class TestStageObjectives:
    """TC-L02: 每个阶段有明确的学习目标"""

    def test_each_stage_has_objectives(self):
        """每个阶段至少有一个 objective"""
        llm = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))

        for i, stage in enumerate(result["stages"]):
            assert len(stage["objectives"]) >= 1, f"stages[{i}] objectives 为空"

    def test_fallback_stages_have_objectives(self):
        """降级路径中每个阶段也应有 objectives"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))

        for stage in result["stages"]:
            assert len(stage["objectives"]) >= 1
            assert len(stage["objectives"][0]) > 5  # 不是空字符串


# ============================================================
# TC-L03: 难度适配
# ============================================================

class TestDifficultyAdaptation:
    """TC-L03: 初级/高级画像生成不同难度的路径"""

    def test_beginner_profile_generates_more_basic_stages(self):
        """初级画像 → 更多基础阶段"""
        llm_beginner = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm_beginner)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))

        # 初级阶段应包含"基础"或"补强"相关标题
        basic_stages = [
            s for s in result["stages"]
            if "基础" in s.get("title", "") or "补强" in s.get("title", "")
        ]
        assert len(basic_stages) >= 1, "初级画像应有基础补强阶段"

    def test_fallback_difficulty_by_knowledge_level(self):
        """降级模式下知识水平影响路径难度"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        beginner_result = asyncio.run(
            agent.build_path("stu_001", BEGINNER_PROFILE)
        )
        advanced_result = asyncio.run(
            agent.build_path("stu_002", ADVANCED_PROFILE)
        )

        # 初级画像 → 阶段更多（slow pace）
        # 高级 + 快速 → 阶段更少
        assert len(beginner_result["stages"]) >= len(advanced_result["stages"]), \
            f"初级阶段数({len(beginner_result['stages'])})应 >= 高级阶段数({len(advanced_result['stages'])})"

    def test_fallback_total_days_differs(self):
        """不同画像生成的路径总天数应不同"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        beginner_result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))
        advanced_result = asyncio.run(agent.build_path("stu_002", ADVANCED_PROFILE))

        # 快速概览的总天数应 ≤ 慢速深入的
        assert advanced_result["total_estimated_days"] <= beginner_result["total_estimated_days"], \
            f"快速型({advanced_result['total_estimated_days']})应 ≤ 中速型({beginner_result['total_estimated_days']})"


# ============================================================
# TC-L04: 路径数据结构一致性（持久化前提）
# ============================================================

class TestPathConsistency:
    """TC-L04: 路径数据结构一致，可序列化持久化"""

    def test_result_is_json_serializable(self):
        """build_path 结果可 JSON 序列化"""
        llm = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))
        serialized = json.dumps(result, ensure_ascii=False)
        deserialized = json.loads(serialized)

        assert deserialized["student_id"] == result["student_id"]
        assert len(deserialized["stages"]) == len(result["stages"])

    def test_fallback_result_is_json_serializable(self):
        """降级结果也可 JSON 序列化"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))
        json.dumps(result, ensure_ascii=False)  # 不应抛异常

    def test_empty_profile_still_works(self):
        """空画像也能生成路径（不崩溃），goal 可为空"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", EMPTY_PROFILE))
        assert len(result["stages"]) > 0
        # EMPTY_PROFILE 的 learning_goal 为空字符串，fallback 保留空值（合理行为）

    def test_sparse_profile_works(self):
        """仅有 knowledge_level 和 learning_goal 也能生成路径"""
        llm = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", SPARSE_PROFILE))
        assert len(result["stages"]) > 0
        assert len(result["goal"]) > 0


# ============================================================
# TC-L05: 路径动态调整
# ============================================================

class TestDynamicAdjustment:
    """TC-L05: 根据评估反馈和已有路径进行动态调整"""

    def test_incremental_update_with_current_path(self):
        """传入已有路径 → LLM 收到增量更新 prompt"""
        llm = make_mock_llm(INCREMENTAL_PATH_JSON)
        agent = PlannerAgent(llm)

        existing_path = {
            "goal": "掌握ML基础",
            "stages": [VALID_PATH_JSON["stages"][0]],
            "current_stage": 2,
        }
        result = asyncio.run(
            agent.build_path(
                student_id="stu_001",
                profile=BEGINNER_PROFILE,
                current_path=existing_path,
            )
        )

        # 应返回 student_id 和 stages
        assert result["student_id"] == "stu_001"
        assert len(result["stages"]) > 0

    def test_evaluation_feedback_includes_review_tasks(self):
        """传入评估反馈 → 生成路径应考虑反馈"""
        llm = make_mock_llm(INCREMENTAL_PATH_JSON)
        agent = PlannerAgent(llm)

        feedback = {
            "weak_topics": ["线性代数"],
            "suggestions": ["需要加强数学基础复习"],
        }
        result = asyncio.run(
            agent.build_path(
                student_id="stu_001",
                profile=BEGINNER_PROFILE,
                evaluation_feedback=feedback,
            )
        )

        assert len(result["stages"]) > 0
        # 检查 prompt 中包含了评估反馈
        call = llm.calls[0]
        assert "评估反馈" in call["user"] or "线性代数" in call["user"]

    def test_goal_passed_in_prompt(self):
        """传入 goal 参数 → user prompt 中应包含自定义目标"""
        llm = MockLLMClient(chunks=["{}"])
        agent = PlannerAgent(llm)

        custom_goal = "通过期末考试"
        asyncio.run(
            agent.build_path("stu_001", BEGINNER_PROFILE, goal=custom_goal)
        )

        call = llm.calls[0]
        assert custom_goal in call["user"], f"prompt 应包含自定义目标"


# ============================================================
# TC-L06: 无画像时的处理
# ============================================================

class TestMissingProfile:
    """TC-L06: 画像不完整时的降级处理"""

    def test_empty_profile_does_not_crash(self):
        """空画像不抛异常，正常降级"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", EMPTY_PROFILE))
        assert "stages" in result
        assert len(result["stages"]) > 0

    def test_missing_knowledge_level(self):
        """缺少 knowledge_level → 降级为默认"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        profile = {"learning_goal": "学ML", "weakness": [], "interest": []}
        result = asyncio.run(agent.build_path("stu_001", profile))

        assert len(result["stages"]) > 0

    def test_missing_optional_fields(self):
        """缺失 weakness/interest/pace 字段不崩溃"""
        llm = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm)

        profile = {"knowledge_level": "中级", "learning_goal": "学AI"}
        result = asyncio.run(agent.build_path("stu_001", profile))

        assert len(result["stages"]) > 0


# ============================================================
# 降级逻辑测试
# ============================================================

class TestFallback:
    """规则降级测试"""

    def test_fallback_includes_weakness_stage(self):
        """有薄弱点时降级路径第一个阶段应为补强"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))

        first_stage = result["stages"][0]
        assert "基础补强" in first_stage["title"] or any(
            w in first_stage.get("description", "")
            for w in BEGINNER_PROFILE.get("weakness", [])
        )

    def test_fallback_no_weakness_no_basic_stage(self):
        """无薄弱点时不应有补强阶段（开头即是核心）"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", MINIMAL_PROFILE))

        # 第一阶段不应该是基础补强
        if len(result["stages"]) > 0:
            first_title = result["stages"][0].get("title", "")
            assert "补强" not in first_title, f"无薄弱点不应有补强阶段: {first_title}"

    def test_fallback_fast_pace_has_fewer_stages(self):
        """快速节奏 → 阶段少"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        fast_profile = {
            "knowledge_level": "中级",
            "learning_goal": "学AI",
            "pace_preference": "快速概览型",
            "weakness": [],
            "interest": [],
        }
        slow_profile = {
            "knowledge_level": "中级",
            "learning_goal": "学AI",
            "pace_preference": "慢速深入型",
            "weakness": [],
            "interest": [],
        }

        fast_result = asyncio.run(agent.build_path("stu_001", fast_profile))
        slow_result = asyncio.run(agent.build_path("stu_002", slow_profile))

        assert len(fast_result["stages"]) < len(slow_result["stages"]), \
            f"快速({len(fast_result['stages'])})应 < 慢速({len(slow_result['stages'])})"

    def test_fallback_includes_interest_in_final_stage(self):
        """有兴趣方向时最后阶段应融合兴趣"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))
        last_stage = result["stages"][-1]

        interests = BEGINNER_PROFILE.get("interest", [])
        content_str = json.dumps(last_stage, ensure_ascii=False)
        assert any(interest in content_str for interest in interests), \
            f"最后阶段应融入兴趣方向: {interests}"


# ============================================================
# 流式输出测试
# ============================================================

class TestStreaming:
    """流式 SSE 输出测试"""

    async def _collect_sse(self, async_gen):
        events = []
        async for event in async_gen:
            events.append(event)
        return events

    def test_chat_emits_delta_and_data_and_done(self):
        """流式应包含 delta、data、done 事件"""
        llm = make_mock_llm(VALID_PATH_JSON)
        agent = PlannerAgent(llm)

        events = asyncio.run(
            self._collect_sse(
                agent.chat("stu_001", BEGINNER_PROFILE)
            )
        )

        assert any('"type":"delta"' in e for e in events)
        assert any('"type":"data"' in e for e in events)
        assert any('"type":"done"' in e for e in events)

    def test_chat_fallback_returns_data_and_done(self):
        """LLM 返回错误消息时 chat() 走降级分支返回 data + done"""
        # BaseAgent.call_llm 重试3次后 yield 错误字符串，不 raise
        # chat() 收到后 _parse_llm_json 失败 → else 分支 → 降级 data + done
        llm = MockLLMClient(chunks=["[生成失败: Mock LLM failure]"])
        agent = PlannerAgent(llm)

        events = asyncio.run(
            self._collect_sse(agent.chat("stu_001", BEGINNER_PROFILE))
        )

        assert any('"type":"data"' in e for e in events)
        assert any('"type":"done"' in e for e in events)


# ============================================================
# 路径有效性校验
# ============================================================

class TestValidatePath:
    """validate_path 静态方法测试"""

    def test_valid_path_passes(self):
        """有效路径通过校验"""
        is_valid, errors = PlannerAgent.validate_path(VALID_PATH_JSON)
        assert is_valid, f"有效路径不应有错误: {errors}"

    def test_missing_goal(self):
        """缺少 goal → 校验失败"""
        path = {"stages": [{"stage_id": 1, "title": "test", "objectives": ["o"], "topics": ["t"], "tasks": [{"description": "d"}], "estimated_days": 1}]}
        is_valid, errors = PlannerAgent.validate_path(path)
        assert not is_valid
        assert any("goal" in e for e in errors)

    def test_empty_stages(self):
        """空 stages → 校验失败"""
        path = {"goal": "test", "stages": []}
        is_valid, errors = PlannerAgent.validate_path(path)
        assert not is_valid
        assert any("stages" in e.lower() for e in errors)

    def test_stage_missing_title(self):
        """阶段缺少 title → 校验失败"""
        path = {
            "goal": "test",
            "stages": [{"stage_id": 1, "objectives": ["o"], "topics": ["t"], "tasks": [{"description": "d"}], "estimated_days": 1}],
        }
        is_valid, errors = PlannerAgent.validate_path(path)
        assert not is_valid
        assert any("title" in e for e in errors)

    def test_stage_missing_objectives(self):
        """阶段缺少 objectives → 校验失败"""
        path = {
            "goal": "test",
            "stages": [{"stage_id": 1, "title": "t", "objectives": [], "topics": ["x"], "tasks": [{"description": "d"}], "estimated_days": 1}],
        }
        is_valid, errors = PlannerAgent.validate_path(path)
        assert not is_valid

    def test_task_missing_description(self):
        """任务缺少 description → 校验失败"""
        path = {
            "goal": "test",
            "stages": [{"stage_id": 1, "title": "t", "objectives": ["o"], "topics": ["x"], "tasks": [{"estimated_minutes": 30}], "estimated_days": 1}],
        }
        is_valid, errors = PlannerAgent.validate_path(path)
        assert not is_valid
        assert any("description" in e for e in errors)

    def test_stage_id_not_int(self):
        """stage_id 非整数 → 校验失败"""
        path = {
            "goal": "test",
            "stages": [{"stage_id": "one", "title": "t", "objectives": ["o"], "topics": ["x"], "tasks": [{"description": "d"}], "estimated_days": 1}],
        }
        is_valid, errors = PlannerAgent.validate_path(path)
        assert not is_valid

    def test_stage_id_not_sequential(self):
        """stage_id 不连续 → 校验失败"""
        path = {
            "goal": "test",
            "stages": [
                {"stage_id": 1, "title": "s1", "objectives": ["o"], "topics": ["x"], "tasks": [{"description": "d"}], "estimated_days": 1},
                {"stage_id": 3, "title": "s3", "objectives": ["o"], "topics": ["x"], "tasks": [{"description": "d"}], "estimated_days": 1},
            ],
        }
        is_valid, errors = PlannerAgent.validate_path(path)
        assert not is_valid
        assert any("连续" in e for e in errors)

    def test_fallback_result_validates(self):
        """降级生成的路径应通过 validate_path"""
        llm = MockLLMClient(should_fail=True)
        agent = PlannerAgent(llm)

        result = asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))
        is_valid, errors = PlannerAgent.validate_path(result)
        assert is_valid, f"降级路径应通过校验: {errors}"


# ============================================================
# 核心知识点推断
# ============================================================

class TestInferCoreTopics:
    """_infer_core_topics 静态方法测试"""

    def test_ml_keywords_return_ml_topics(self):
        topics = PlannerAgent._infer_core_topics("我想学机器学习和深度学习")
        assert any("监督学习" in t for t in topics)

    def test_dev_keywords_return_dev_topics(self):
        topics = PlannerAgent._infer_core_topics("我想学后端开发")
        assert any("数据结构" in t or "API" in t for t in topics)

    def test_data_keywords_return_ds_topics(self):
        topics = PlannerAgent._infer_core_topics("我想做数据分析")
        assert any("数据分析" in t or "可视化" in t for t in topics)

    def test_unknown_goal_returns_default_topics(self):
        topics = PlannerAgent._infer_core_topics("随便学学")
        assert len(topics) == 6  # default 6 topics


# ============================================================
# System Prompt 质量测试
# ============================================================

class TestSystemPrompt:
    """System Prompt 质量测试"""

    def test_prompt_includes_six_dimensions(self):
        """Prompt 应提及画像6维度"""
        agent = PlannerAgent(MockLLMClient())
        prompt = agent.get_system_prompt()
        assert "knowledge_level" in prompt or "知识水平" in prompt
        assert "learning_goal" in prompt or "学习目标" in prompt
        assert "weakness" in prompt or "薄弱" in prompt
        assert "interest" in prompt or "兴趣" in prompt
        assert "cognitive_style" in prompt or "认知风格" in prompt
        assert "pace_preference" in prompt or "学习节奏" in prompt

    def test_prompt_includes_json_format(self):
        """Prompt 应要求输出 JSON"""
        agent = PlannerAgent(MockLLMClient())
        prompt = agent.get_system_prompt()
        assert "json" in prompt.lower()
        assert "stages" in prompt

    def test_prompt_includes_difficulty_adaptation(self):
        """Prompt 应包含难度自适应规则"""
        agent = PlannerAgent(MockLLMClient())
        prompt = agent.get_system_prompt()
        assert "初级" in prompt
        assert "高级" in prompt


# ============================================================
# Prompt 构建测试
# ============================================================

class TestPromptBuilding:
    """_build_user_prompt 测试"""

    def test_prompt_includes_profile(self):
        llm = MockLLMClient(chunks=["{}"])
        agent = PlannerAgent(llm)

        asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE))
        call = llm.calls[0]
        assert "学生画像" in call["user"]
        assert "初级" in call["user"]

    def test_prompt_includes_goal(self):
        llm = MockLLMClient(chunks=["{}"])
        agent = PlannerAgent(llm)

        asyncio.run(agent.build_path("stu_001", BEGINNER_PROFILE, goal="通过考试"))
        call = llm.calls[0]
        assert "通过考试" in call["user"]

    def test_prompt_includes_current_path(self):
        llm = MockLLMClient(chunks=["{}"])
        agent = PlannerAgent(llm)

        asyncio.run(
            agent.build_path("stu_001", BEGINNER_PROFILE, current_path={"stages": []})
        )
        call = llm.calls[0]
        assert "已有学习路径" in call["user"]

    def test_prompt_includes_evaluation_feedback(self):
        llm = MockLLMClient(chunks=["{}"])
        agent = PlannerAgent(llm)

        asyncio.run(
            agent.build_path(
                "stu_001", BEGINNER_PROFILE, evaluation_feedback={"weak_topics": ["数学"]}
            )
        )
        call = llm.calls[0]
        assert "评估反馈" in call["user"]
        assert "数学" in call["user"]
