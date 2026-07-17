"""Agent 输出 Schema 校验测试。"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.schemas import (
    # Resource schemas
    DocumentContent,
    SectionData,
    ExerciseContent,
    ExerciseQuestion,
    QuestionOption,
    MindmapContent,
    MindmapNode,
    PptContent,
    SlideData,
    # Evaluation schemas
    EvaluationOutput,
    EvalDataSummary,
    EvalOverall,
    EvalDimensions,
    WeaknessDetail,
    # Planner schemas
    LearningPathOutput,
    StageData,
    LearningTask,
    PathAdjustmentPreview,
    PathAdjustment,
    # Resource meta
    ResourceMeta,
    ResourceGenerationOutput,
)


class TestDocumentSchema:
    """Document resource schema validation."""

    def test_valid_document(self):
        doc = DocumentContent(
            learning_objectives=["理解梯度下降"],
            sections=[
                SectionData(
                    heading="损失函数",
                    paragraphs=["损失函数衡量..."],
                    examples=["MSE 示例"],
                    key_points=["损失函数越小越好"],
                )
            ],
            summary="梯度下降核心总结",
            common_mistakes=["混淆损失函数和评估指标"],
            review_questions=["学习率的作用是什么？"],
        )
        assert doc.learning_objectives[0] == "理解梯度下降"
        assert len(doc.sections) == 1
        assert doc.sections[0].heading == "损失函数"

    def test_minimal_document(self):
        """最小有效 document。"""
        doc = DocumentContent()
        assert doc.learning_objectives == []
        assert doc.sections == []
        assert doc.summary == ""


class TestExerciseSchema:
    """Exercise resource schema validation."""

    def test_valid_exercise(self):
        ex = ExerciseContent(
            instructions="请完成以下练习",
            questions=[
                ExerciseQuestion(
                    id="q1",
                    type="single_choice",
                    stem="学习率过大会导致？",
                    options=[
                        QuestionOption(key="A", text="收敛缓慢"),
                        QuestionOption(key="B", text="震荡不收敛"),
                    ],
                    correct_answer=["B"],
                    explanation="学习率过大导致参数更新步长过大",
                    difficulty="medium",
                    knowledge_point_ids=["kp_learning_rate"],
                )
            ],
        )
        assert len(ex.questions) == 1
        assert ex.questions[0].correct_answer == ["B"]

    def test_exercise_rejects_markdown(self):
        """Exercise 不接受 Markdown 字符串作为 content。"""
        # ExerciseContent 必须是一个对象，不是字符串
        with pytest.raises(Exception):
            # Pydantic 应该拒绝将纯字符串解析为 ExerciseContent
            ExerciseContent.model_validate("## 这不是一个合法的练习题 JSON")


class TestMindmapSchema:
    """Mindmap resource schema validation."""

    def test_valid_mindmap(self):
        mm = MindmapContent(
            root=MindmapNode(
                id="root",
                label="梯度下降",
                description="核心优化算法",
                children=[
                    MindmapNode(id="loss", label="损失函数", description="衡量误差"),
                ],
            )
        )
        assert mm.root.label == "梯度下降"
        assert len(mm.root.children) == 1

    def test_nested_mindmap(self):
        """多层嵌套导图。"""
        mm = MindmapContent(
            root=MindmapNode(
                id="root",
                label="AI",
                children=[
                    MindmapNode(
                        id="ml",
                        label="机器学习",
                        children=[
                            MindmapNode(id="supervised", label="监督学习"),
                            MindmapNode(id="unsupervised", label="无监督学习"),
                        ],
                    )
                ],
            )
        )
        assert len(mm.root.children[0].children) == 2


class TestPptSchema:
    """PPT resource schema validation."""

    def test_valid_ppt(self):
        ppt = PptContent(
            theme="神经网络入门",
            slides=[
                SlideData(
                    slide_number=1,
                    title="神经网络与反向传播",
                    layout="title",
                    speaker_notes="面向中级学习者",
                ),
                SlideData(
                    slide_number=2,
                    title="学习目标",
                    layout="content",
                ),
            ],
        )
        assert len(ppt.slides) == 2
        assert ppt.slides[0].layout == "title"


class TestEvaluationSchema:
    """Evaluation output schema validation."""

    def test_valid_evaluation(self):
        ev = EvaluationOutput(
            evaluation_id="eval_001",
            user_id="u1",
            course_id="ai_deep_learning_demo",
            data_summary=EvalDataSummary(
                unique_tasks_completed=7,
                questions_answered=15,
                tests_completed=1,
                learning_minutes=128,
            ),
            overall=EvalOverall(
                score=72,
                confidence=0.75,
                level="基础掌握",
            ),
            dimensions=EvalDimensions(
                knowledge_mastery=70,
                test_accuracy=68,
                task_completion=35,
                learning_consistency=80,
            ),
            weaknesses=[
                WeaknessDetail(
                    knowledge_point_id="kp_learning_rate",
                    name="学习率选择",
                    score=48,
                    priority="high",
                    evidence=["最近5道相关题目答错3道"],
                    recommended_actions=[
                        {"type": "exercise", "title": "学习率专项练习", "estimated_minutes": 20}
                    ],
                )
            ],
            summary="薄弱点在学习率选择",
        )
        assert ev.overall.score == 72
        assert len(ev.weaknesses) == 1
        assert ev.weaknesses[0].priority == "high"
        assert len(ev.weaknesses[0].evidence) >= 1

    def test_scores_clamped(self):
        """分数必须在 0-100 范围内。"""
        with pytest.raises(Exception):
            EvalOverall(score=150)
        with pytest.raises(Exception):
            EvalDimensions(knowledge_mastery=-10)


class TestPlannerSchema:
    """Planner output schema validation."""

    def test_valid_path(self):
        path = LearningPathOutput(
            course_id="ai_deep_learning_demo",
            version=1,
            goal="掌握深度学习基础",
            stages=[
                StageData(
                    stage_id="stage_1",
                    title="AI基础",
                    order=1,
                    status="active",
                    learning_objectives=["理解AI基本概念"],
                    knowledge_point_ids=["kp_ai_concept"],
                    topics=["人工智能基本概念"],
                    tasks=[
                        LearningTask(
                            task_id="task_1_doc",
                            task_type="document",
                            title="AI基础核心讲义",
                            estimated_minutes=30,
                            status="not_started",
                        )
                    ],
                )
            ],
            current_stage=1,
            estimated_days=14,
        )
        assert len(path.stages) == 1
        assert path.stages[0].tasks[0].task_type == "document"

    def test_path_with_four_stages(self):
        """测试四阶段路径（演示课程标准结构）。"""
        stages = []
        for i, title in enumerate(["AI基础", "梯度下降", "神经网络", "CNN"], 1):
            stages.append(StageData(
                stage_id=f"stage_{i}",
                title=title,
                order=i,
                status="locked" if i > 1 else "active",
                learning_objectives=[f"掌握{title}"],
                tasks=[
                    LearningTask(
                        task_id=f"task_{i}_goal",
                        task_type="goal",
                        title=f"{title}学习目标",
                        estimated_minutes=10,
                    ),
                    LearningTask(
                        task_id=f"task_{i}_doc",
                        task_type="document",
                        title=f"{title}核心讲义",
                        estimated_minutes=30,
                    ),
                ],
            ))
        path = LearningPathOutput(
            course_id="ai_deep_learning_demo",
            version=1,
            stages=stages,
        )
        assert len(path.stages) == 4
        assert path.stages[1].status == "locked"


class TestResourceMeta:
    """Resource meta schema validation."""

    def test_resource_meta_missing_type_fails(self):
        """缺少 resource_type 应失败。"""
        with pytest.raises(Exception):
            ResourceMeta(title="无类型资源")
