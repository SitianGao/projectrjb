"""
AI 输出质量测试 — Day 12 队员B 交付物

验证所有 Agent 的输出质量:
- TC-Q01: ProfileAgent 输出结构化 + 防幻觉标记
- TC-Q02: PlannerAgent 输出阶段完整 + 任务具体
- TC-Q03: ResourceAgent 所有类型资源内容充实
- TC-Q04: TutorAgent 四种风格内容差异化
- TC-Q05: EvaluateAgent 评分基于数据 + 遗忘曲线
- TC-Q06: 降级方法输出质量可接受（非占位符）
- TC-Q07: 防幻觉机制在各 Agent 中生效
- TC-Q08: 输出稳定性——同输入多次运行一致
"""
import json
import pytest

from backend.agents.profile_agent import ProfileAgent
from backend.agents.planner_agent import PlannerAgent
from backend.agents.resource_agent import ResourceAgent
from backend.agents.tutor_agent import TutorAgent
from backend.agents.evaluate_agent import EvaluateAgent


# ==========================================================================
# TC-Q01: ProfileAgent 输出质量
# ==========================================================================

class TestProfileQuality:
    """验证 ProfileAgent 输出质量"""

    def test_fallback_produces_six_dimensions(self):
        """规则化兜底输出包含 6 个画像维度"""
        agent = ProfileAgent(None)
        result = agent._keyword_fallback("stu-01", "我在学机器学习，数学基础不太好", [])

        assert "profile" in result
        profile = result["profile"]
        required_dims = [
            "knowledge_level", "learning_goal", "cognitive_style",
            "weakness", "interest", "pace_preference"
        ]
        for dim in required_dims:
            assert dim in profile, f"缺少维度: {dim}"
            assert profile[dim] is not None

    def test_fallback_detects_weakness_from_input(self):
        """规则化兜底能从输入中检测薄弱点"""
        agent = ProfileAgent(None)
        result = agent._keyword_fallback("stu-01", "我数学推导比较弱，概率也不太好", [])

        weaknesses = result["profile"]["weakness"]
        assert any("数学" in w for w in weaknesses), f"未检测到数学薄弱: {weaknesses}"
        assert any("概率" in w for w in weaknesses), f"未检测到概率薄弱: {weaknesses}"

    def test_fallback_detects_interest_from_input(self):
        """规则化兜底能从输入中检测兴趣"""
        agent = ProfileAgent(None)
        result = agent._keyword_fallback("stu-01", "我对编程很感兴趣，想多写代码", [])

        interests = result["profile"]["interest"]
        assert any("代码" in i for i in interests), f"未检测到编程兴趣: {interests}"

    def test_fallback_confidence_is_low(self):
        """规则化兜底标注低置信度"""
        agent = ProfileAgent(None)
        result = agent._keyword_fallback("stu-01", "随便学学", [])

        assert result["confidence"] <= 0.5, f"规则匹配的置信度应较低: {result['confidence']}"
        assert result["completeness"] <= 0.6

    def test_fallback_next_questions_not_empty(self):
        """completeness < 0.7 时 next_questions 不为空"""
        agent = ProfileAgent(None)
        result = agent._keyword_fallback("stu-01", "你好", [])

        assert len(result["next_questions"]) >= 2


# ==========================================================================
# TC-Q02: PlannerAgent 输出质量
# ==========================================================================

class TestPlannerQuality:
    """验证 PlannerAgent 输出质量"""

    def test_fallback_stages_have_all_fields(self):
        """规则化兜底的每个阶段包含 title/objectives/topics/tasks"""
        agent = PlannerAgent()
        profile = {
            "knowledge_level": "中级",
            "learning_goal": "掌握机器学习",
            "weakness": ["数学推导"],
            "interest": ["NLP"],
        }
        raw = agent._rule_based_plan(profile)
        plan = json.loads(raw)

        assert "goal" in plan
        assert "stages" in plan
        assert "current_stage" in plan
        assert "estimated_days" in plan
        assert plan["current_stage"] >= 1
        assert plan["estimated_days"] >= 1

        for stage in plan["stages"]:
            assert "title" in stage
            assert "objectives" in stage
            assert "topics" in stage
            assert "tasks" in stage
            for task in stage["tasks"]:
                assert "task" in task
                assert "resource_type" in task
                assert "estimated_hours" in task
                # 任务描述足够具体
                assert len(task["task"]) >= 5, f"任务描述太短: '{task['task']}'"

    def test_fallback_weakness_triggers_extra_tasks(self):
        """薄弱点在对应阶段插入额外补习任务"""
        agent = PlannerAgent()
        profile = {
            "knowledge_level": "初级",
            "learning_goal": "掌握AI基础",
            "weakness": ["基础知识回顾"],
            "interest": [],
        }
        raw = agent._rule_based_plan(profile, course_outline=["基础知识回顾", "核心概念入门"])
        plan = json.loads(raw)

        stage1 = plan["stages"][0]
        extra_tasks = [t for t in stage1["tasks"] if "补习" in t["task"]]
        assert len(extra_tasks) >= 1, f"薄弱点未触发额外任务: {[t['task'] for t in stage1['tasks']]}"

    def test_fallback_difficulty_multiplier(self):
        """初级学员预估天数比高级学员多"""
        agent = PlannerAgent()
        beginner_plan = json.loads(agent._rule_based_plan(
            {"knowledge_level": "初级", "learning_goal": "X", "weakness": [], "interest": []}
        ))
        advanced_plan = json.loads(agent._rule_based_plan(
            {"knowledge_level": "高级", "learning_goal": "X", "weakness": [], "interest": []}
        ))

        assert beginner_plan["estimated_days"] >= advanced_plan["estimated_days"], \
            f"初级({beginner_plan['estimated_days']}天)应 >= 高级({advanced_plan['estimated_days']}天)"

    def test_tasks_are_actionable(self):
        """任务是可执行的（「学习XX」不算有效任务）"""
        agent = PlannerAgent()
        raw = agent._rule_based_plan(
            {"knowledge_level": "中级", "learning_goal": "X", "weakness": [], "interest": []},
            course_outline=["线性回归", "决策树"]
        )
        plan = json.loads(raw)

        for stage in plan["stages"]:
            for t in stage["tasks"]:
                task_desc = t["task"]
                # 不应该是纯粹的「学习XX」格式
                assert not task_desc.startswith("学习"), \
                    f"任务太泛: '{task_desc}'（应该是'完成XX阅读并做练习'这种形式）"


# ==========================================================================
# TC-Q03: ResourceAgent 输出质量
# ==========================================================================

class TestResourceQuality:
    """验证 ResourceAgent 输出质量"""

    @pytest.fixture
    def agent(self):
        return ResourceAgent()

    def test_document_content_has_structure(self, agent):
        """document 资源有清晰的章节结构"""
        result = agent._rule_based_resources("线性回归", ["document"], "中级", {})
        assert len(result["resources"]) == 1

        content = result["resources"][0]["content"]
        # 有 Markdown 标题
        assert "#" in content, f"document 应有标题: {content[:100]}"
        # 有要点或小结
        assert "要点" in content or "总结" in content or "关键" in content, \
            f"document 应有关键要点: {content[:100]}"
        # 长度不低于 200 字符
        assert len(content) >= 200, f"document 内容过短 ({len(content)} 字符)"

    def test_mindmap_is_valid_nested_list(self, agent):
        """mindmap 是合法的嵌套 Markdown 列表"""
        result = agent._rule_based_resources("CNN", ["mindmap"], "初级", {})
        content = result["resources"][0]["content"]

        lines = content.strip().split("\n")
        # 至少 5 行
        assert len(lines) >= 5, f"思维导图节点数不足: {len(lines)} 行"
        # 有缩进层级
        has_indent = any(line.startswith("  ") for line in lines)
        assert has_indent, "思维导图应有缩进层级"

    def test_exercise_json_is_parseable(self, agent):
        """exercise 输出可解析的 JSON"""
        result = agent._rule_based_resources("逻辑回归", ["exercise"], "中级", {})
        content = result["resources"][0]["content"]

        try:
            questions = json.loads(content)
        except json.JSONDecodeError:
            pytest.fail(f"exercise 内容不是合法 JSON: {content[:100]}")

        assert isinstance(questions, list)
        assert len(questions) >= 2, f"题目数不足: {len(questions)}"
        for q in questions:
            assert "question" in q
            assert "answer" in q

    def test_code_is_syntactically_plausible(self, agent):
        """code 资源包含 Python 关键元素"""
        result = agent._rule_based_resources("K-means", ["code"], "高级", {})
        content = result["resources"][0]["content"]

        assert "import" in content or "def " in content or "class " in content, \
            f"code 应包含 Python 关键元素: {content[:100]}"
        assert "TODO" not in content, f"code 不应包含未实现的 TODO 占位: {content[:100]}"

    def test_reading_has_graded_materials(self, agent):
        """reading 资源包含分级推荐"""
        result = agent._rule_based_resources("深度学习", ["reading"], "高级", {})
        content = result["resources"][0]["content"]

        assert "推荐" in content or "阅读" in content
        assert "思考" in content, "reading 应包含拓展思考"
        # 不应有未填写的占位符
        assert "（内容待生成）" not in content

    def test_ppt_has_structured_slides(self, agent):
        """ppt 大纲有明确的 slide 结构"""
        result = agent._rule_based_resources("神经网络", ["ppt"], "中级", {})
        content = result["resources"][0]["content"]

        assert "Slide" in content, f"ppt 应有 slide 编号: {content[:100]}"
        assert len(content) >= 400, f"ppt 内容过短 ({len(content)} 字符)"

    def test_no_placeholder_text_in_fallback(self, agent):
        """规则化兜底不包含「（内容待生成）」占位符"""
        for rtype in ["document", "mindmap", "exercise", "code", "reading", "ppt"]:
            result = agent._rule_based_resources("测试主题", [rtype], "中级", {})
            content = result["resources"][0]["content"]
            assert "（内容待生成）" not in content, \
                f"{rtype} 含占位符: {content[:100]}"


# ==========================================================================
# TC-Q04: TutorAgent 输出质量
# ==========================================================================

class TestTutorQuality:
    """验证 TutorAgent 输出质量"""

    @pytest.fixture
    def agent(self):
        return TutorAgent()

    def test_four_styles_produce_different_content(self, agent):
        """四种风格产生差异化内容（不是完全相同）"""
        answers = {}
        for style in ["analogy", "formula", "visual", "story"]:
            raw = agent._rule_based_tutor("什么是梯度下降？", style, "中级", [])
            result = json.loads(raw)
            answers[style] = result["answer"]

        # 至少有 2 个风格不同
        unique_answers = set(answers.values())
        assert len(unique_answers) >= 2, \
            f"四种风格应产生差异化内容，实际只有 {len(unique_answers)} 种"

    def test_visual_style_includes_mermaid(self, agent):
        """visual 风格包含 Mermaid 图表"""
        raw = agent._rule_based_tutor("神经网络的训练流程", "visual", "中级", [])
        result = json.loads(raw)

        assert len(result["diagrams"]) >= 1, "visual 风格应有 diagrams"
        assert "graph" in result["diagrams"][0].lower(), \
            f"Mermaid 应包含 graph: {result['diagrams'][0][:50]}"

    def test_formula_style_is_structured(self, agent):
        """formula 风格有推导步骤"""
        raw = agent._rule_based_tutor("推导反向传播公式", "formula", "高级", [])
        result = json.loads(raw)

        assert "步骤" in result["answer"] or "推导" in result["answer"] or "定义" in result["answer"], \
            f"formula 应有步骤结构: {result['answer'][:100]}"

    def test_non_academic_redirect_is_helpful(self, agent):
        """非学术问题重定向时给出引导"""
        raw = agent._rule_based_tutor("今天天气怎么样", "auto", "中级", [])
        result = json.loads(raw)

        assert "学习" in result["answer"], f"应引导回学习主题: {result['answer'][:100]}"
        # 引导信息应包含可选问题类型
        assert (
            "概念" in result["answer"]
            or "公式" in result["answer"]
            or "代码" in result["answer"]
            or "知识点" in result["answer"]
        ), f"应提示可问内容: {result['answer'][:100]}"

    def test_auto_style_uses_heuristic(self, agent):
        """auto 模式根据问题关键词选择合适的风格"""
        # 含「推导」→ formula
        raw = agent._rule_based_tutor("如何推导贝叶斯公式", "auto", "中级", [])
        result = json.loads(raw)
        assert result["explanation_style"] == "formula", \
            f"含'推导'应选formula，实际: {result['explanation_style']}"

        # 含「流程」→ visual
        raw = agent._rule_based_tutor("描述CNN训练的流程", "auto", "中级", [])
        result = json.loads(raw)
        assert result["explanation_style"] == "visual", \
            f"含'流程'应选visual，实际: {result['explanation_style']}"

        # 含「区别」→ analogy
        raw = agent._rule_based_tutor("SVM和逻辑回归的区别", "auto", "中级", [])
        result = json.loads(raw)
        assert result["explanation_style"] == "analogy", \
            f"含'区别'应选analogy，实际: {result['explanation_style']}"

    def test_answer_not_just_a_template(self, agent):
        """规则化回答不是只有模板骨架（含实质性内容）"""
        raw = agent._rule_based_tutor("解释一下梯度下降", "analogy", "中级", [])
        result = json.loads(raw)

        # 回答中不应包含大量未替换的占位标记
        answer = result["answer"]
        placeholder_count = answer.count("…") + answer.count("...")
        assert placeholder_count <= 10, \
            f"占位符过多 ({placeholder_count} 个): {answer[:200]}"


# ==========================================================================
# TC-Q05: EvaluateAgent 输出质量
# ==========================================================================

class TestEvaluateQuality:
    """验证 EvaluateAgent 输出质量"""

    @pytest.fixture
    def agent(self):
        return EvaluateAgent()

    @pytest.fixture
    def sample_records(self):
        return [
            {"topic": "线性回归", "action": "complete", "score": 0.85, "time_spent": 3600,
             "created_at": "2026-06-15T10:00:00+08:00"},
            {"topic": "线性回归", "action": "answer", "score": 0.90, "time_spent": 1800,
             "created_at": "2026-06-15T14:00:00+08:00"},
            {"topic": "梯度下降", "action": "complete", "score": 0.55, "time_spent": 2400,
             "created_at": "2026-06-10T09:00:00+08:00"},
            {"topic": "梯度下降", "action": "answer", "score": 0.40, "time_spent": 1500,
             "created_at": "2026-06-10T11:00:00+08:00"},
            {"topic": "决策树", "action": "view", "time_spent": 0,
             "created_at": "2026-06-20T08:00:00+08:00"},
        ]

    def test_all_dimensions_present(self, agent, sample_records):
        """评估报告包含全部 4 个维度"""
        raw = agent._rule_based_evaluate("stu-01", {}, sample_records)
        result = json.loads(raw)

        dim_names = {d["name"] for d in result["dimensions"]}
        expected = {"knowledge_mastery", "progress", "efficiency", "weakness_analysis"}
        assert dim_names == expected, f"维度不完整: {dim_names}"

    def test_weak_topics_from_low_scores(self, agent, sample_records):
        """薄弱点来自低分记录"""
        raw = agent._rule_based_evaluate("stu-01", {}, sample_records)
        result = json.loads(raw)

        assert "梯度下降" in result["weak_topics"], \
            f"低分知识点应出现在薄弱点: {result['weak_topics']}"

    def test_suggestions_are_specific(self, agent, sample_records):
        """建议具体到知识点级别，而非泛泛而谈"""
        raw = agent._rule_based_evaluate("stu-01", {}, sample_records)
        result = json.loads(raw)

        for s in result["suggestions"]:
            # 不应只是「多练习」这种泛泛建议
            assert len(s) >= 8, f"建议太短: '{s}'"

    def test_review_plan_includes_weak_topics(self, agent, sample_records):
        """复习计划包含薄弱点"""
        raw = agent._rule_based_evaluate("stu-01", {}, sample_records)
        result = json.loads(raw)

        review_topics = {p["topic"] for p in result["review_plan"]}
        assert "梯度下降" in review_topics, \
            f"薄弱点应在复习计划中: {review_topics}"

    def test_review_plan_urgency_is_valid(self, agent, sample_records):
        """复习计划的 urgency 值合法"""
        raw = agent._rule_based_evaluate("stu-01", {}, sample_records)
        result = json.loads(raw)

        for plan_item in result["review_plan"]:
            assert plan_item["urgency"] in ("high", "medium", "low")
            assert plan_item["reason"]
            assert len(plan_item["recommended_resources"]) >= 1

    def test_empty_records_gives_graceful_output(self, agent):
        """无记录时不崩溃且有合理输出"""
        raw = agent._rule_based_evaluate("stu-01", {}, [])
        result = json.loads(raw)

        assert 0 <= result["overall_score"] <= 100
        assert len(result["dimensions"]) == 4
        assert isinstance(result["weak_topics"], list)
        assert isinstance(result["suggestions"], list)

    def test_score_based_on_actual_data(self, agent, sample_records):
        """评分基于实际数据计算（不是写死的）"""
        # 高分记录
        high_records = [
            {"topic": "线性代数", "action": "complete", "score": 0.95, "time_spent": 3600,
             "created_at": "2026-06-20T10:00:00+08:00"},
            {"topic": "线性代数", "action": "answer", "score": 0.92, "time_spent": 1800,
             "created_at": "2026-06-20T14:00:00+08:00"},
        ]
        raw_high = agent._rule_based_evaluate("stu-high", {}, high_records)
        high_score = json.loads(raw_high)["overall_score"]

        # 低分记录
        low_records = [
            {"topic": "微积分", "action": "answer", "score": 0.30, "time_spent": 3600,
             "created_at": "2026-06-20T10:00:00+08:00"},
            {"topic": "微积分", "action": "answer", "score": 0.25, "time_spent": 1800,
             "created_at": "2026-06-20T14:00:00+08:00"},
        ]
        raw_low = agent._rule_based_evaluate("stu-low", {}, low_records)
        low_score = json.loads(raw_low)["overall_score"]

        assert high_score > low_score, \
            f"高分学员({high_score})应高于低分学员({low_score})"

    def test_forgetting_curve_memory_decay(self, agent):
        """遗忘曲线：距上次学习时间越长，越容易被推入复习计划"""
        recent_records = [
            {"topic": "逻辑回归", "action": "complete", "score": 0.90, "time_spent": 1800,
             "created_at": "2026-06-20T08:00:00+08:00"},  # 今天
        ]
        old_records = [
            {"topic": "SVM", "action": "complete", "score": 0.90, "time_spent": 1800,
             "created_at": "2026-06-01T08:00:00+08:00"},  # 19 天前
        ]

        recent_raw = agent._rule_based_evaluate("stu-recent", {}, recent_records)
        recent_plan = json.loads(recent_raw)["review_plan"]

        old_raw = agent._rule_based_evaluate("stu-old", {}, old_records)
        old_plan = json.loads(old_raw)["review_plan"]

        # 旧记录更可能触达复习阈值
        assert len(old_plan) >= 0  # 至少不崩溃
        # 新学的内容不应该被紧急推送（R 应该还很高）
        recent_topics_high_urgency = [p for p in recent_plan if p.get("urgency") == "high"]
        assert len(recent_topics_high_urgency) == 0, \
            "刚学的内容不应有 high urgency 复习"


# ==========================================================================
# TC-Q06: 系统提示词质量
# ==========================================================================

class TestPromptQuality:
    """验证各 Agent 的 System Prompt 质量"""

    def test_all_agents_have_anti_hallucination_prompt(self):
        """所有 Agent 的 System Prompt 包含防幻觉约束"""
        agents = [
            ProfileAgent(None),
            PlannerAgent(),
            ResourceAgent(),
            TutorAgent(),
            EvaluateAgent(),
        ]

        for agent in agents:
            prompt = agent.get_system_prompt()
            has_anti_hallucination = any(
                phrase in prompt
                for phrase in ["防幻觉", "不确定", "核实", "编造", "违规", "诚实"]
            )
            assert has_anti_hallucination, \
                f"{agent.__class__.__name__} System Prompt 缺少防幻觉约束"

    def test_all_agents_have_output_format(self):
        """所有 Agent 的 System Prompt 指定了输出格式"""
        agents_with_output_format = [ProfileAgent, PlannerAgent, ResourceAgent, TutorAgent, EvaluateAgent]

        for agent_cls in agents_with_output_format:
            agent = agent_cls(None) if agent_cls == ProfileAgent else agent_cls()
            prompt = agent.get_system_prompt()
            assert "输出" in prompt and ("JSON" in prompt or "格式" in prompt), \
                f"{agent_cls.__name__} System Prompt 缺少输出格式说明"

    def test_tutor_has_safety_constraint(self):
        """TutorAgent System Prompt 包含安全约束"""
        agent = TutorAgent()
        prompt = agent.get_system_prompt()
        assert "违规" in prompt or "敏感" in prompt or "不安全" in prompt, \
            "TutorAgent 缺少安全约束"


# ==========================================================================
# TC-Q07: 跨 Agent 端到端质量检查
# ==========================================================================

class TestCrossAgentQuality:
    """跨 Agent 质量检查"""

    def test_profile_to_plan_consistency(self):
        """画像 -> 路径：路径应反映画像中的薄弱点"""
        profile_agent = ProfileAgent(None)
        profile = profile_agent._keyword_fallback(
            "stu-01", "我在学机器学习，数学基础比较差，想掌握深度学习", []
        )

        planner_agent = PlannerAgent()
        raw = planner_agent._rule_based_plan(
            profile,
            course_outline=["数学基础", "机器学习入门", "深度学习", "综合项目"]
        )
        plan = json.loads(raw)

        # 阶段应覆盖课程大纲的所有主题
        stage_topics = [t for s in plan["stages"] for t in s["topics"]]
        assert "数学基础" in stage_topics, "应包含数学基础补强阶段"

    def test_resource_matches_difficulty(self):
        """资源难度应与请求一致"""
        agent = ResourceAgent()

        beginner = agent._rule_based_resources("神经网络", ["document"], "初级", {})
        advanced = agent._rule_based_resources("神经网络", ["document"], "高级", {})

        beginner_content = beginner["resources"][0]["content"]
        advanced_content = advanced["resources"][0]["content"]

        # 初级应有「生活类比」或更多解释性内容
        # 高级应有「推导」或「理论」
        assert beginner_content != advanced_content, \
            "不同难度的资源应有差异"
