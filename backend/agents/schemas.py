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
    """课程级学习画像。"""
    user_id: str
    course_id: str
    version: int = Field(default=1, ge=1)
    knowledge_foundation: KnowledgeFoundation = Field(default_factory=KnowledgeFoundation)
    learning_goal: str = ""
    cognitive_style: str = "案例驱动型"
    preferred_resources: list[str] = Field(default_factory=lambda: ["mindmap", "exercise", "document"])
    weak_points: list[WeakPoint] = Field(default_factory=list)
    interest_directions: list[str] = Field(default_factory=list)
    update_reason: str = ""
    updated_at: str = ""


class ProfileOutput(BaseModel):
    """ProfileAgent build_profile 输出。"""
    profile: CourseProfile
    completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=lambda: ["dialogue"])
    next_questions: list[str] = Field(default_factory=list)
    can_start_journey: bool = False


# ═══════════════════════════════════════════════════════════════════════
# PlannerAgent
# ═══════════════════════════════════════════════════════════════════════

class LearningTask(BaseModel):
    task_id: str
    task_type: str  # document | exercise | mindmap | code | assessment
    title: str
    description: str = ""
    estimated_minutes: int = Field(default=30, ge=5, le=480)
    difficulty: str = "初级"
    status: str = "not_started"
    prerequisite_task_ids: list[str] = Field(default_factory=list)


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


class LearningPathOutput(BaseModel):
    """PlannerAgent 输出 —— 学习路径合同。"""
    course_id: str
    version: int = Field(default=1, ge=1)
    goal: str = ""
    stages: list[StageData] = Field(default_factory=list)
    current_stage: int = Field(default=1, ge=1)
    estimated_days: int = Field(default=14, ge=1)
    adaptation: dict = Field(default_factory=dict)


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


class ResourceMeta(BaseModel):
    """单个资源的公共元数据。"""
    resource_id: str = ""
    user_id: str = ""
    course_id: str = ""
    stage_id: str = ""
    task_id: str = ""
    knowledge_point_ids: list[str] = Field(default_factory=list)
    resource_type: str  # document | exercise | mindmap | ppt
    title: str
    summary: str = ""
    difficulty: str = "中级"
    estimated_minutes: int = Field(default=30, ge=1)
    status: str = "completed"
    version: int = Field(default=1, ge=1)
    content: dict = Field(default_factory=dict)


class ResourceGenerationOutput(BaseModel):
    """ResourceAgent 批量生成输出。"""
    resources: list[ResourceMeta] = Field(default_factory=list)
    topic: str = ""
    difficulty: str = "中级"
    total: int = 0


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
    score: int = Field(default=0, ge=0, le=100)
    previous_score: Optional[int] = None
    score_delta: Optional[int] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    level: str = ""
    short_term_trend: str = "stable"
    long_term_trend: str = "stable"


class EvalDimensions(BaseModel):
    knowledge_mastery: int = Field(default=0, ge=0, le=100)
    test_accuracy: int = Field(default=0, ge=0, le=100)
    task_completion: int = Field(default=0, ge=0, le=100)
    learning_consistency: int = Field(default=0, ge=0, le=100)


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


class EvaluationOutput(BaseModel):
    """EvaluateAgent 输出 —— 完整评估报告。"""
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
    profile_updates: list[dict] = Field(default_factory=list)
    generated_at: str = ""
