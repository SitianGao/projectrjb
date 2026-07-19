"""
多智能体系统 Pydantic 输出 Schema。

所有 Agent 的 LLM 输出必须通过这些 Schema 校验后才能入库或返回前端。
不允许将未校验的自然语言文本直接保存到数据库。

设计依据：赛题要求的 5+ 种资源类型、结构化评估、路径合同。
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════
# ProfileAgent
# ═══════════════════════════════════════════════════════════════════════

class KnowledgeFoundation(BaseModel):
    """知识基础——各学科/领域的掌握程度 0-100。"""
    python: int = Field(default=50, ge=0, le=100)
    linear_algebra: int = Field(default=50, ge=0, le=100)
    calculus: int = Field(default=50, ge=0, le=100)
    machine_learning: int = Field(default=35, ge=0, le=100)
    deep_learning: int = Field(default=30, ge=0, le=100)


class WeakPoint(BaseModel):
    knowledge_point_id: str
    name: str = ""
    score: int = Field(default=50, ge=0, le=100)


class CourseProfile(BaseModel):
    """课程级学习画像 —— 至少 10 个维度。"""
    user_id: str
    course_id: str
    version: int = Field(default=1, ge=1)

    # ── 基础信息 ──
    major: str = ""
    grade: str = ""

    # ── 知识基础 ──
    knowledge_foundation: KnowledgeFoundation = Field(default_factory=KnowledgeFoundation)

    # ── 学习目标与历史 ──
    learning_goal: str = ""
    learning_history: list[str] = Field(default_factory=list)

    # ── 认知风格 ──
    cognitive_style: str = "案例驱动型"

    # ── 薄弱点 ──
    weak_points: list[WeakPoint] = Field(default_factory=list)

    # ── 资源与兴趣 ──
    preferred_resources: list[str] = Field(default_factory=lambda: ["mindmap", "exercise", "document"])
    assessment_preference: str = ""
    interest_directions: list[str] = Field(default_factory=list)

    # ── 时间与周期 ──
    session_duration_minutes: int | None = None
    sessions_per_week: int | None = None
    weekly_available_hours: float | None = None
    target_duration_weeks: int | None = None
    preferred_study_time: str = ""

    # ── 元数据 ──
    completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    update_reason: str = ""
    updated_at: str = ""


class ProfileOutput(BaseModel):
    """ProfileAgent build_profile_v2 结构化输出。"""
    profile: CourseProfile
    profile_patch: dict = Field(default_factory=dict)
    completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=lambda: ["dialogue"])
    missing_dimensions: list[str] = Field(default_factory=list)
    next_questions: list[str] = Field(default_factory=list)
    assistant_reply: str = ""
    can_start_journey: bool = False


# ═══════════════════════════════════════════════════════════════════════
# PlannerAgent
# ═══════════════════════════════════════════════════════════════════════

class LearningTask(BaseModel):
    task_id: str
    task_type: str  # document | exercise | mindmap | code | assessment | interactive_classroom | weakness_fix
    title: str
    description: str = ""
    estimated_minutes: int = Field(default=30, ge=5, le=480)
    difficulty: str = "初级"
    status: str = "not_started"
    prerequisite_task_ids: list[str] = Field(default_factory=list)
    # ── v3 个性化字段 ──
    dynamic_source: Optional[str] = None  # "evaluation_weakness:<kp>" | "profile_gap:<area>" | "interest:<dir>" | null
    unlock_condition: Optional[str] = None  # 人类可读的解锁条件，如"完成前置任务 X"


class StageData(BaseModel):
    stage_id: str
    title: str
    order: int = Field(ge=1)
    description: str = ""
    status: str = "locked"  # locked | active | completed
    learning_objectives: list[str] = Field(default_factory=list)
    knowledge_point_ids: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    estimated_days: int = 3
    unlock_conditions: list[str] = Field(default_factory=list)
    tasks: list[LearningTask] = Field(default_factory=list)
    resource_blueprint: list[dict] = Field(default_factory=list)
    # ── v3 个性化字段 ──
    adaptation_reason: str = ""  # "为什么为你这样安排"——引用画像/评估数据


class LearningPathOutput(BaseModel):
    """PlannerAgent 输出 —— 学习路径合同。"""
    course_id: str
    version: int = Field(default=1, ge=1)
    goal: str = ""
    stages: list[StageData] = Field(default_factory=list)
    current_stage: int = Field(default=1, ge=1)
    estimated_days: int = Field(default=14, ge=1)
    adaptation: dict = Field(default_factory=dict)
    # ── v3 个性化字段 ──
    adaptation_summary: str = ""  # 整体路径个性化设计思路


class PathAdjustment(BaseModel):
    """单条路径调整建议。"""
    action: str  # insert_task | reorder_stage | add_review | skip_stage
    stage_id: Optional[str] = None
    knowledge_point_id: Optional[str] = None
    reason: str = ""
    suggested_task: Optional[LearningTask] = None
    impact: str = ""  # 影响描述（给用户看）


class PathAdjustmentPreview(BaseModel):
    """路径调整预览（用户确认前）。"""
    evaluation_id: str
    course_id: str
    adjustments: list[PathAdjustment] = Field(default_factory=list)
    summary: str = ""
    requires_confirmation: bool = True


# ═══════════════════════════════════════════════════════════════════════
# TutorAgent
# ═══════════════════════════════════════════════════════════════════════

class TutorResponse(BaseModel):
    """TutorAgent 回答输出。"""
    answer: str
    citations: list[dict] = Field(default_factory=list)
    knowledge_point_ids: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation_style: str = "auto"


# ═══════════════════════════════════════════════════════════════════════
# ResourceAgent
# ═══════════════════════════════════════════════════════════════════════

class SectionData(BaseModel):
    heading: str
    paragraphs: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)


class DocumentContent(BaseModel):
    learning_objectives: list[str] = Field(default_factory=list)
    sections: list[SectionData] = Field(default_factory=list)
    summary: str = ""
    common_mistakes: list[str] = Field(default_factory=list)
    review_questions: list[str] = Field(default_factory=list)


class QuestionOption(BaseModel):
    key: str  # "A" | "B" | "C" | "D"
    text: str


class ExerciseQuestion(BaseModel):
    id: str
    type: str = "single_choice"  # single_choice | multiple_choice | short_answer | true_false
    stem: str
    options: list[QuestionOption] = Field(default_factory=list)
    correct_answer: list[str] = Field(default_factory=list)
    explanation: str = ""
    difficulty: str = "medium"
    knowledge_point_ids: list[str] = Field(default_factory=list)


class ExerciseContent(BaseModel):
    instructions: str = ""
    questions: list[ExerciseQuestion] = Field(default_factory=list)


class MindmapNode(BaseModel):
    id: str
    label: str
    description: str = ""
    children: list["MindmapNode"] = Field(default_factory=list)


class MindmapContent(BaseModel):
    root: MindmapNode


class SlideElement(BaseModel):
    type: str = "text"  # text | image | bullet_list | code
    content: str = ""


class SlideData(BaseModel):
    slide_number: int = Field(ge=1)
    title: str
    layout: str = "content"  # title | content | two_column | summary
    speaker_notes: str = ""
    elements: list[SlideElement] = Field(default_factory=list)


class PptContent(BaseModel):
    theme: str = ""
    slides: list[SlideData] = Field(default_factory=list)


class ResourcePreview(BaseModel):
    """Deterministic preview stats generated after validation."""
    schema_version: int = 1
    question_count: int = 0
    slide_count: int = 0
    branch_count: int = 0
    node_count: int = 0
    scene_count: int = 0
    interaction_count: int = 0
    estimated_minutes: int = 0
    file_count: int = 0
    test_count: int = 0


class SourceProvenance(BaseModel):
    grounded: bool = False
    retrieval_query: str = ""
    knowledge_base_id: str = ""
    knowledge_base_version: str = ""
    collection_name: str = ""
    retrieved_documents: list[dict] = Field(default_factory=list)
    fallback_used: bool = False
    fallback_reason: str | None = None
    provenance_status: str = "legacy_orphan"  # legacy_orphan | current_validated


class GenerationMeta(BaseModel):
    agent_name: str = "ResourceAgent"
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    run_id: str = ""
    request_id: str = ""
    duration_ms: int = 0
    fallback_used: bool = False
    generated_at: str = ""


class ResourceMeta(BaseModel):
    """单个资源的公共元数据 — ResourceEnvelope。"""
    resource_id: str = ""
    user_id: str = ""
    course_id: str = ""
    path_id: str = ""
    stage_id: str = ""
    stage_title: str = ""
    task_id: str = ""
    resource_type: str  # document | exercise | mindmap | ppt | interactive_classroom | code
    schema_version: int = 1
    title: str
    summary: str = ""
    topic: str = ""
    difficulty: str = "中级"
    status: str = "ready"  # draft | generating | ready | failed
    content: dict = Field(default_factory=dict)
    preview: ResourcePreview = Field(default_factory=ResourcePreview)
    artifacts: dict = Field(default_factory=dict)
    source_provenance: SourceProvenance = Field(default_factory=SourceProvenance)
    generation_meta: GenerationMeta = Field(default_factory=GenerationMeta)
    knowledge_point_ids: list[str] = Field(default_factory=list)
    estimated_minutes: int = Field(default=30, ge=1)
    version: int = Field(default=1, ge=1)
    created_at: str = ""
    updated_at: str = ""


class ResourceGenerationOutput(BaseModel):
    """ResourceAgent 批量生成输出。"""
    resources: list[ResourceMeta] = Field(default_factory=list)
    topic: str = ""
    difficulty: str = "中级"
    total: int = 0
    knowledge_sources: list[dict] = Field(default_factory=list)
    generation_meta: GenerationMeta = Field(default_factory=GenerationMeta)


# ═══════════════════════════════════════════════════════════════════════
# Per-type content schemas (Pydantic validation before save)
# ═══════════════════════════════════════════════════════════════════════

class DocumentContent(BaseModel):
    learning_objectives: list[str] = Field(default_factory=list)
    sections: list[SectionData] = Field(default_factory=list)
    summary: str = ""
    common_mistakes: list[str] = Field(default_factory=list)
    review_questions: list[str] = Field(default_factory=list)

class ExerciseContent(BaseModel):
    instructions: str = ""
    questions: list[ExerciseQuestion] = Field(default_factory=list)

class MindmapContent(BaseModel):
    root: MindmapNode

class PptContent(BaseModel):
    theme: str = ""
    slides: list[SlideData] = Field(default_factory=list)

class InteractiveClassroomContent(BaseModel):
    classroom_id: str = ""
    title: str = ""
    summary: str = ""
    scenes: list[dict] = Field(default_factory=list)
    estimated_minutes: int = 25
    difficulty: str = "中级"
    knowledge_point_ids: list[str] = Field(default_factory=list)

class CodeContent(BaseModel):
    """旧版代码内容 Schema（向后兼容）。"""
    language: str = "python"
    code: str = ""
    explanation: str = ""
    output: str = ""
    test_cases: list[dict] = Field(default_factory=list)


class EditableParameter(BaseModel):
    """可调实验参数。"""
    name: str = ""                # 变量名 "learning_rate"
    label: str = ""               # 中文标签 "学习率"
    default_value: float | int | str = 0.01
    allowed_values: list = Field(default_factory=list)
    explanation: str = ""


class CodeExperimentStep(BaseModel):
    """代码实验步骤。"""
    step_id: str = ""
    title: str = ""
    instruction: str = ""
    code_snippet: str = ""
    expected_result: str = ""
    hint: str | None = None


class CodeExperimentContent(BaseModel):
    """交互式代码实验内容 Schema。

    支持五种实验模式：
    - code_guide: 代码导读型（分步拆解代码）
    - param_experiment: 参数实验型（调参观察结果）
    - code_completion: 关键代码补全型
    - error_diagnosis: 错误诊断型
    - mini_project: 小型项目型
    """
    # 基本信息
    title: str = ""
    scenario: str = ""
    experiment_mode: str = "code_guide"  # code_guide | param_experiment | code_completion | error_diagnosis | mini_project
    difficulty: str = "中级"
    estimated_minutes: int = 30

    # 学习目标
    learning_objectives: list[str] = Field(default_factory=list)
    knowledge_points: list[str] = Field(default_factory=list)
    prerequisite_knowledge: list[str] = Field(default_factory=list)

    # 实验步骤（代码导读型核心）
    steps: list[CodeExperimentStep] = Field(default_factory=list)

    # 完整代码 & 可编辑参数
    starter_code: str = ""
    editable_parameters: list[EditableParameter] = Field(default_factory=list)

    # 观察与诊断
    observation_questions: list[str] = Field(default_factory=list)
    common_errors: list[str] = Field(default_factory=list)
    expected_phenomena: list[str] = Field(default_factory=list)

    # 代码补全型
    blanks: list[dict] = Field(default_factory=list)

    # 错误诊断型
    buggy_code: str = ""
    bug_description: str = ""
    fix_hint: str = ""

    # 可视化
    visualization_type: str | None = None

    # 个性化
    personalization_reason: str = ""

    # 向后兼容旧字段
    language: str = "python"
    code: str = ""
    explanation: str = ""
    output: str = ""
    test_cases: list[dict] = Field(default_factory=list)


# Content schema registry
CONTENT_SCHEMAS = {
    "document": DocumentContent,
    "exercise": ExerciseContent,
    "mindmap": MindmapContent,
    "ppt": PptContent,
    "interactive_classroom": InteractiveClassroomContent,
    "code": CodeExperimentContent,
}


def validate_resource_content(resource_type: str, content: dict) -> tuple[bool, str, dict]:
    """Validate content against its type schema. Returns (valid, error, preview)."""
    schema_class = CONTENT_SCHEMAS.get(resource_type)
    if schema_class is None:
        return True, "", {}  # Unknown types pass through

    try:
        validated = schema_class(**content) if isinstance(content, dict) else schema_class.model_validate_json(str(content))
        preview = generate_content_preview(resource_type, validated)
        return True, "", preview
    except Exception as e:
        return False, str(e)[:200], {}


def generate_content_preview(resource_type: str, content) -> dict:
    """Generate deterministic preview stats from validated content."""
    preview = {}
    if resource_type == "document":
        preview["estimated_minutes"] = max(5, sum(len(s.paragraphs) for s in (content.sections or [])) * 3)
    elif resource_type == "exercise":
        preview["question_count"] = len(content.questions or [])
    elif resource_type == "mindmap":
        preview["branch_count"] = _count_mindmap_nodes(content.root) - 1 if content.root else 0
        preview["node_count"] = _count_mindmap_nodes(content.root) if content.root else 0
    elif resource_type == "ppt":
        preview["slide_count"] = len(content.slides or [])
    elif resource_type == "interactive_classroom":
        preview["scene_count"] = len(content.scenes or [])
        preview["interaction_count"] = sum(1 for s in (content.scenes or []) if s.get("scene_type") in ("simulation", "quiz", "discussion"))
    elif resource_type == "code":
        # 优先使用实验模式字段
        exp_code = getattr(content, 'starter_code', '') or getattr(content, 'code', '')
        preview["file_count"] = 1 if exp_code else 0
        preview["test_count"] = len(getattr(content, 'test_cases', []) or [])
        preview["step_count"] = len(getattr(content, 'steps', []) or [])
        preview["param_count"] = len(getattr(content, 'editable_parameters', []) or [])
        preview["experiment_mode"] = getattr(content, 'experiment_mode', 'code_guide')
    preview.setdefault("schema_version", 1)
    return preview


def _count_mindmap_nodes(node) -> int:
    if not node:
        return 0
    count = 1
    for child in (node.children or []):
        count += _count_mindmap_nodes(child)
    return count


# ═══════════════════════════════════════════════════════════════════════
# EvaluateAgent
# ═══════════════════════════════════════════════════════════════════════

class EvalDataSummary(BaseModel):
    unique_tasks_completed: int = 0
    questions_answered: int = 0
    tests_completed: int = 0
    wrongbook_reviews: int = 0
    learning_minutes: int = 0


class EvalOverall(BaseModel):
    score: Optional[int] = Field(default=None, ge=0, le=100)  # None when insufficient data
    previous_score: Optional[int] = None
    score_delta: Optional[int] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    level: str = ""
    short_term_trend: str = "insufficient_data"
    long_term_trend: str = "insufficient_data"


class EvalDimensions(BaseModel):
    knowledge_mastery: Optional[int] = Field(default=None, ge=0, le=100)
    test_accuracy: Optional[int] = Field(default=None, ge=0, le=100)
    task_completion: Optional[int] = Field(default=None, ge=0, le=100)
    learning_consistency: Optional[int] = Field(default=None, ge=0, le=100)


class WeaknessDetail(BaseModel):
    knowledge_point_id: str
    name: str
    score: int = Field(default=50, ge=0, le=100)
    priority: str = "medium"  # high | medium | low
    evidence: list[str] = Field(default_factory=list)
    recommended_actions: list[dict] = Field(default_factory=list)


class StrengthDetail(BaseModel):
    knowledge_point_id: str
    name: str
    score: int = Field(default=80, ge=0, le=100)


class ProfileUpdateSuggestion(BaseModel):
    """EvaluateAgent 提出的画像更新建议。只建议，不直接修改。"""
    field: str                                           # 画像字段名
    old_value: str = ""
    new_value: str = ""
    reason: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)


class PathAdjustmentSuggestion(BaseModel):
    """EvaluateAgent 提出的路径调整建议。"""
    action: str                                          # insert_remedial_task | review_prerequisite | reduce_difficulty | increase_difficulty | postpone_stage | unlock_stage
    knowledge_point: str = ""
    reason: str = ""
    priority: str = "medium"                             # high | medium | low
    target_stage_id: str = ""
    target_task_id: str = ""
    suggested_resource_type: str = "exercise"
    evidence_refs: list[str] = Field(default_factory=list)


class EvaluationOutput(BaseModel):
    """EvaluateAgent 输出 —— 完整评估报告（第3轮扩展）。"""
    evaluation_id: str
    user_id: str
    course_id: str
    scope: dict = Field(default_factory=dict)
    data_summary: EvalDataSummary = Field(default_factory=EvalDataSummary)
    overall: EvalOverall = Field(default_factory=EvalOverall)
    dimensions: EvalDimensions = Field(default_factory=EvalDimensions)
    strengths: list[StrengthDetail] = Field(default_factory=list)
    weaknesses: list[WeaknessDetail] = Field(default_factory=list)
    summary: str = ""
    recommendations: list[str] = Field(default_factory=list)
    path_adjustments: list[PathAdjustment] = Field(default_factory=list)
    path_adjustment_suggestions: list[PathAdjustmentSuggestion] = Field(default_factory=list)
    profile_updates: list[dict] = Field(default_factory=list)
    profile_update_suggestions: list[ProfileUpdateSuggestion] = Field(default_factory=list)
    intervention_actions: list[dict] = Field(default_factory=list)
    generated_at: str = ""
