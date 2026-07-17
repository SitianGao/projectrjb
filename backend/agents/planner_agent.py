"""
PlannerAgent —— 学习路径规划智能体

根据学生画像和课程知识体系，生成分阶段个性化学习路径。

输出结构（对齐 docs/design.md §10.4.3）:
    goal: str               — 学习总目标
    stages: list[dict]      — 阶段列表
        title: str          — 阶段名称
        objectives: str     — 阶段学习目标
        topics: list[str]   — 涵盖知识点
        tasks: list[dict]   — 阶段任务
            task: str       — 任务描述
            resource_type: str — 推荐资源类型
            estimated_hours: float
    current_stage: int      — 当前所在阶段（从 1 开始）
    estimated_days: int     — 预计总天数
"""
import json
import asyncio
from typing import Optional, List, Dict

from .base_agent import BaseAgent

<<<<<<< Updated upstream
=======
# ── 新架构导入 ──
from core.agent_context import AgentContext
from agents.schemas import (
    LearningPathOutput,
    StageData,
    LearningTask,
    PathAdjustmentPreview,
    PathAdjustment,
)
from agents.prompts.planner_prompts import (
    PLANNER_SYSTEM_PROMPT,
    PATH_ADJUSTMENT_PROMPT,
)

try:
    from config import LLM_STRICT_MODE
except ModuleNotFoundError:
    from backend.config import LLM_STRICT_MODE

>>>>>>> Stashed changes

class PlannerAgent(BaseAgent):
    """根据画像规划个性化学习路径"""

    def __init__(self, llm_client=None):
        super().__init__(llm_client)

    def get_system_prompt(self) -> str:
        return PLANNER_SYSTEM_PROMPT

    # ------------------------------------------------------------------
    # 主入口（v1 —— 向后兼容）
    # ------------------------------------------------------------------
    async def generate_plan(
        self,
        profile: dict,
        goal_override: Optional[str] = None,
        course_outline: Optional[List[str]] = None,
    ) -> str:
        """
        生成学习路径 JSON。

        Args:
            profile: 学生画像 dict（至少含 knowledge_level, learning_goal, weakness, interest）
            goal_override: 手动覆盖学习目标（可选）
            course_outline: 课程大纲/知识点列表（可选）
        Returns:
            JSON 字符串
        """
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
        outline_text = json.dumps(course_outline or [], ensure_ascii=False)
        user_prompt = (
            f"学生画像:\n{profile_json}\n\n"
            f"课程大纲:\n{outline_text}\n\n"
            + (f"用户指定目标: {goal_override}\n\n" if goal_override else "")
            + "请根据以上信息生成个性化学习路径。"
        )

        if self.llm:
            try:
                chunks = []
                async for chunk in self.call_llm(user_prompt):
                    chunks.append(chunk)
                return "".join(chunks)
            except Exception:
                pass  # fall through to rule-based

        return self._rule_based_plan(profile, goal_override, course_outline)

    # ------------------------------------------------------------------
    # V2 主入口 —— 结构化输出
    # ------------------------------------------------------------------
    async def generate_plan_v2(
        self,
        *,
        context: AgentContext,
        profile: dict,
        course_outline: list[str] | None = None,
        current_path: dict | None = None,
        evaluation_feedback: dict | None = None,
    ) -> LearningPathOutput:
        """生成学习路径（v2：Pydantic 结构化输出）。

        Args:
            context: 统一 Agent 上下文（含 user_id, course_id 等）
            profile: 学生画像 dict
            course_outline: 课程大纲/知识点列表（可选）
            current_path: 当前学习路径（调整时保留已完成进度）
            evaluation_feedback: 最新评估反馈

        Returns:
            LearningPathOutput: 通过 Pydantic 校验的结构化路径
        """
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
        outline_text = json.dumps(course_outline or [], ensure_ascii=False)
        current_path_text = json.dumps(current_path or {}, ensure_ascii=False)
        feedback_text = json.dumps(evaluation_feedback or {}, ensure_ascii=False)

        user_prompt = (
            f"课程ID: {context.course_id}\n"
            f"学生画像:\n{profile_json}\n\n"
            f"课程大纲:\n{outline_text}\n\n"
            f"当前学习路径（调整时保留已完成进度）:\n{current_path_text}\n\n"
            f"最新评估反馈（优先补强薄弱点和到期复习项）:\n{feedback_text}\n\n"
            f"请根据以上信息生成个性化学习路径；如果存在评估反馈，必须说明并落实路径调整。"
        )

        if self.llm:
            try:
                return await self.call_llm_json(
                    context=context,
                    user_prompt=user_prompt,
                    response_model=LearningPathOutput,
                )
            except Exception:
                if LLM_STRICT_MODE:
                    raise

        if LLM_STRICT_MODE:
            raise RuntimeError("严格模式：讯飞星火未配置，拒绝规则路径降级")

        return self._rule_based_plan_v2(
            context=context,
            profile=profile,
            course_outline=course_outline,
            current_path=current_path,
            evaluation_feedback=evaluation_feedback,
        )

    # ------------------------------------------------------------------
    # 路径调整预览（V2）
    # ------------------------------------------------------------------
    async def preview_adjustment(
        self,
        *,
        context: AgentContext,
        current_path: dict,
        evaluation: dict,
    ) -> PathAdjustmentPreview:
        """根据评估结果生成路径调整预览（不自动应用）。

        展示将如何调整路径，等待用户确认后再调用 apply_adjustment。

        Args:
            context: 统一 Agent 上下文
            current_path: 当前学习路径 dict
            evaluation: 评估报告 dict

        Returns:
            PathAdjustmentPreview: 调整建议列表 + 摘要
        """
        evaluation_id = evaluation.get("evaluation_id", "")
        current_path_json = json.dumps(current_path, ensure_ascii=False, indent=2)
        evaluation_json = json.dumps(evaluation, ensure_ascii=False, indent=2)

        user_prompt = PATH_ADJUSTMENT_PROMPT.format(
            current_path_json=current_path_json,
            evaluation_json=evaluation_json,
        )

        if self.llm:
            try:
                return await self.call_llm_json(
                    context=context,
                    user_prompt=user_prompt,
                    response_model=PathAdjustmentPreview,
                )
            except Exception:
                if LLM_STRICT_MODE:
                    raise

        # 规则化兜底
        return self._rule_based_adjustment_preview(
            context=context,
            evaluation_id=evaluation_id,
            current_path=current_path,
            evaluation=evaluation,
        )

    # ------------------------------------------------------------------
    # 应用路径调整（V2）
    # ------------------------------------------------------------------
    async def apply_adjustment(
        self,
        *,
        context: AgentContext,
        adjustment_preview: PathAdjustmentPreview,
    ) -> LearningPathOutput:
        """应用已确认的路径调整，生成新版本的学习路径。

        Args:
            context: 统一 Agent 上下文
            adjustment_preview: 用户确认的调整预览

        Returns:
            LearningPathOutput: 调整后的新路径版本
        """
        adjustments_json = json.dumps(
            [adj.model_dump() for adj in adjustment_preview.adjustments],
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = (
            f"课程ID: {context.course_id}\n"
            f"以下调整已由用户确认，请应用到学习路径中。\n\n"
            f"调整摘要: {adjustment_preview.summary}\n\n"
            f"待应用的调整:\n{adjustments_json}\n\n"
            f"请生成应用这些调整后的完整学习路径。"
        )

        if self.llm:
            try:
                return await self.call_llm_json(
                    context=context,
                    user_prompt=user_prompt,
                    response_model=LearningPathOutput,
                )
            except Exception:
                if LLM_STRICT_MODE:
                    raise

        return self._rule_based_plan_v2(
            context=context,
            profile={},
            course_outline=None,
            current_path=adjustment_preview.model_dump(),
            evaluation_feedback={"adjustments": adjustment_preview.model_dump()},
        )

    # ------------------------------------------------------------------
    # 规则化兜底 V2（返回 LearningPathOutput）
    # ------------------------------------------------------------------
    def _rule_based_plan_v2(
        self,
        *,
        context: AgentContext,
        profile: dict,
        course_outline: list[str] | None = None,
        current_path: dict | None = None,
        evaluation_feedback: dict | None = None,
    ) -> LearningPathOutput:
        """规则化路径生成 v2 —— 返回 Pydantic 模型。"""
        profile_inner = profile.get("profile", profile)
        knowledge = profile_inner.get("knowledge_level", "初级")
        goal = profile_inner.get("learning_goal", "掌握课程核心知识")
        weaknesses = list(profile_inner.get("weakness") or [])
        interests = list(profile_inner.get("interest") or [])

        if course_outline:
            topics = list(course_outline)
        else:
            topics = PlannerAgent._derive_stages_from_profile(
                goal, knowledge, weaknesses, interests
            )

        feedback_topics = [
            str(topic).strip()
            for topic in (evaluation_feedback or {}).get("weak_topics", [])
            if str(topic).strip() and str(topic).strip() != "暂未检测到明显薄弱点"
        ]
        topics = [*feedback_topics, *[t for t in topics if t not in feedback_topics]]

        stages: list[StageData] = []
        for i, topic in enumerate(topics, 1):
            stage_id = f"stage_{i}"
            tasks: list[LearningTask] = []

            if i == 1:
                tasks = [
                    LearningTask(
                        task_id=f"{stage_id}_task_1",
                        task_type="document",
                        title=f"浏览「{topic}」学习大纲并了解前置要求",
                        description=f"阅读课程大纲，了解「{topic}」的前置要求和学习目标",
                        estimated_minutes=30,
                        difficulty="初级",
                        status="not_started",
                    ),
                    LearningTask(
                        task_id=f"{stage_id}_task_2",
                        task_type="document",
                        title=f"阅读「{topic}」入门材料并完成概念预习",
                        description=f"通过入门材料对「{topic}」建立初步认知",
                        estimated_minutes=90,
                        difficulty="初级",
                        status="not_started",
                    ),
                ]
            elif i < len(topics):
                tasks = [
                    LearningTask(
                        task_id=f"{stage_id}_task_1",
                        task_type="document",
                        title=f"精读「{topic}」核心讲解并做笔记",
                        description=f"深入学习「{topic}」的核心概念和原理",
                        estimated_minutes=120,
                        difficulty="中级" if knowledge in ("中级", "中高级") else "初级",
                        status="not_started",
                    ),
                    LearningTask(
                        task_id=f"{stage_id}_task_2",
                        task_type="mindmap",
                        title=f"用思维导图梳理「{topic}」的知识框架",
                        description="将知识点组织成结构化思维导图，建立知识关联",
                        estimated_minutes=60,
                        difficulty="中级" if knowledge in ("中级", "中高级") else "初级",
                        status="not_started",
                    ),
                    LearningTask(
                        task_id=f"{stage_id}_task_3",
                        task_type="exercise",
                        title=f"完成「{topic}」基础练习题（至少 3 道）",
                        description="通过练习巩固所学知识，检验理解程度",
                        estimated_minutes=90,
                        difficulty="中级",
                        status="not_started",
                    ),
                ]
            else:
                tasks = [
                    LearningTask(
                        task_id=f"{stage_id}_task_1",
                        task_type="code",
                        title=f"「{topic}」综合实战项目",
                        description="将所学知识应用到实际项目中，完成综合练习",
                        estimated_minutes=180,
                        difficulty="中高级" if knowledge in ("中高级", "高级") else "中级",
                        status="not_started",
                    ),
                    LearningTask(
                        task_id=f"{stage_id}_task_2",
                        task_type="document",
                        title="撰写学习总结并梳理知识体系",
                        description="回顾整个学习过程，总结核心知识点和收获",
                        estimated_minutes=60,
                        difficulty="初级",
                        status="not_started",
                    ),
                ]

            # 为薄弱点插入额外任务
            for w in weaknesses:
                if w and w in topic:
                    review_task = LearningTask(
                        task_id=f"{stage_id}_task_review_{w[:8].replace(' ', '_')}",
                        task_type="exercise",
                        title=f"重点补习弱项: {w}（完成专项练习）",
                        description=f"针对薄弱点「{w}」进行强化练习",
                        estimated_minutes=60,
                        difficulty="初级",
                        status="not_started",
                    )
                    tasks.insert(1, review_task)

            # 添加阶段末评估任务
            tasks.append(LearningTask(
                task_id=f"{stage_id}_task_assessment",
                task_type="assessment",
                title=f"阶段{i}测评",
                description=f"完成「{topic}」阶段学习测评，检验掌握程度",
                estimated_minutes=45,
                difficulty="中级",
                status="not_started",
            ))

            stage = StageData(
                stage_id=stage_id,
                title=f"阶段{i}: {topic}",
                order=i,
                description=f"学完本阶段，你将能够理解并应用「{topic}」的核心内容",
                status="active" if i == 1 else "locked",
                learning_objectives=[
                    f"理解「{topic}」的核心概念和原理",
                    f"掌握「{topic}」的基本应用方法",
                ],
                knowledge_point_ids=[],
                topics=[topic],
                estimated_days=3,
                unlock_conditions=[] if i == 1 else [f"完成阶段{i - 1}所有任务"],
                tasks=tasks,
            )
            stages.append(stage)

        day_multiplier = {"初级": 1.5, "中级": 1.0, "中高级": 0.8, "高级": 0.7}
        multiplier = day_multiplier.get(knowledge, 1.0)
        estimated_days = max(1, int(len(stages) * 3 * multiplier))

        return LearningPathOutput(
            course_id=context.course_id,
            version=(current_path or {}).get("version", 0) + 1,
            goal=goal,
            stages=stages,
            current_stage=1,
            estimated_days=estimated_days,
            adaptation={
                "triggered": bool(feedback_topics),
                "weak_topics": feedback_topics,
                "previous_path_id": (current_path or {}).get("id"),
            },
        )

    # ------------------------------------------------------------------
    # 规则化调整预览（无需 LLM）
    # ------------------------------------------------------------------
    def _rule_based_adjustment_preview(
        self,
        *,
        context: AgentContext,
        evaluation_id: str,
        current_path: dict,
        evaluation: dict,
    ) -> PathAdjustmentPreview:
        """规则化路径调整预览。"""
        adjustments: list[PathAdjustment] = []
        weaknesses = evaluation.get("weaknesses", [])

        for w in weaknesses[:3]:
            kp_id = w.get("knowledge_point_id", "")
            kp_name = w.get("name", "")
            score = w.get("score", 50)

            if score < 60:
                adjustments.append(PathAdjustment(
                    action="insert_task",
                    knowledge_point_id=kp_id,
                    reason=f"知识点「{kp_name}」得分 {score}，需要复习强化",
                    suggested_task=LearningTask(
                        task_id=f"review_{kp_id}",
                        task_type="exercise",
                        title=f"复习巩固: {kp_name}",
                        description=f"针对薄弱知识点「{kp_name}」进行专项复习和练习",
                        estimated_minutes=60,
                        difficulty="初级",
                        status="not_started",
                    ),
                    impact=f"在当前学习路径中插入「{kp_name}」的复习任务",
                ))

        summary_parts = []
        if adjustments:
            summary_parts.append(f"检测到 {len(adjustments)} 个薄弱知识点需要强化")
        else:
            summary_parts.append("当前评估未发现需要调整的薄弱点")

        return PathAdjustmentPreview(
            evaluation_id=evaluation_id,
            course_id=context.course_id,
            adjustments=adjustments,
            summary="；".join(summary_parts),
            requires_confirmation=True,
        )

    # ------------------------------------------------------------------
    # 规则化兜底 v1（保持向后兼容，但输出更丰富的结构）
    # ------------------------------------------------------------------
    def _rule_based_plan(
        self,
        profile: dict,
        goal_override: Optional[str] = None,
        course_outline: Optional[List[str]] = None,
    ) -> str:
<<<<<<< Updated upstream
        """开发期无 API Key 时使用的规则化路径生成"""
=======
        """开发期无 API Key 时使用的规则化路径生成（v2: 画像驱动 + 丰富字段）"""
>>>>>>> Stashed changes
        profile_inner = profile.get("profile", profile)
        knowledge = profile_inner.get("knowledge_level", "初级")
        goal = goal_override or profile_inner.get("learning_goal", "掌握课程核心知识")
        weaknesses = profile_inner.get("weakness", [])
        topics = course_outline or [
            "基础知识回顾", "核心概念入门", "进阶技术实践", "综合项目实战"
        ]

        stages = []
        for i, topic in enumerate(topics, 1):
            stage_id = f"stage_{i}"
            tasks = []
            if i == 1:
                tasks = [
<<<<<<< Updated upstream
                    {"task": f"浏览{topic}大纲与前置要求", "resource_type": "document", "estimated_hours": 0.5},
                    {"task": f"完成{topic}预习阅读", "resource_type": "reading", "estimated_hours": 1.5},
                ]
            elif i < len(topics):
                tasks = [
                    {"task": f"学习{topic}核心讲解", "resource_type": "document", "estimated_hours": 2.0},
                    {"task": f"完成{topic}思维导图整理", "resource_type": "mindmap", "estimated_hours": 1.0},
                    {"task": f"练习{topic}基础习题", "resource_type": "exercise", "estimated_hours": 1.5},
                ]
            else:
                tasks = [
                    {"task": f"{topic}综合实践", "resource_type": "code", "estimated_hours": 3.0},
                    {"task": "撰写学习总结", "resource_type": "document", "estimated_hours": 1.0},
=======
                    {
                        "task_id": f"{stage_id}_task_1",
                        "task_type": "document",
                        "title": f"浏览「{topic}」学习大纲并了解前置要求",
                        "task": f"浏览「{topic}」学习大纲并了解前置要求",
                        "description": f"阅读课程大纲，了解「{topic}」的前置要求和学习目标",
                        "resource_type": "document",
                        "estimated_hours": 0.5,
                        "estimated_minutes": 30,
                        "difficulty": "初级",
                        "status": "not_started",
                        "prerequisite_task_ids": [],
                    },
                    {
                        "task_id": f"{stage_id}_task_2",
                        "task_type": "document",
                        "title": f"阅读「{topic}」入门材料并完成概念预习",
                        "task": f"阅读「{topic}」入门材料并完成概念预习",
                        "description": f"通过入门材料对「{topic}」建立初步认知",
                        "resource_type": "reading",
                        "estimated_hours": 1.5,
                        "estimated_minutes": 90,
                        "difficulty": "初级",
                        "status": "not_started",
                        "prerequisite_task_ids": [],
                    },
                ]
            elif i < len(topics):
                tasks = [
                    {
                        "task_id": f"{stage_id}_task_1",
                        "task_type": "document",
                        "title": f"精读「{topic}」核心讲解并做笔记",
                        "task": f"精读「{topic}」核心讲解并做笔记",
                        "description": f"深入学习「{topic}」的核心概念和原理",
                        "resource_type": "document",
                        "estimated_hours": 2.0,
                        "estimated_minutes": 120,
                        "difficulty": "中级" if knowledge in ("中级", "中高级") else "初级",
                        "status": "not_started",
                        "prerequisite_task_ids": [],
                    },
                    {
                        "task_id": f"{stage_id}_task_2",
                        "task_type": "mindmap",
                        "title": f"用思维导图梳理「{topic}」的知识框架",
                        "task": f"用思维导图梳理「{topic}」的知识框架",
                        "description": "将知识点组织成结构化思维导图，建立知识关联",
                        "resource_type": "mindmap",
                        "estimated_hours": 1.0,
                        "estimated_minutes": 60,
                        "difficulty": "中级" if knowledge in ("中级", "中高级") else "初级",
                        "status": "not_started",
                        "prerequisite_task_ids": [],
                    },
                    {
                        "task_id": f"{stage_id}_task_3",
                        "task_type": "exercise",
                        "title": f"完成「{topic}」基础练习题（至少 3 道）",
                        "task": f"完成「{topic}」基础练习题（至少 3 道）",
                        "description": "通过练习巩固所学知识，检验理解程度",
                        "resource_type": "exercise",
                        "estimated_hours": 1.5,
                        "estimated_minutes": 90,
                        "difficulty": "中级",
                        "status": "not_started",
                        "prerequisite_task_ids": [],
                    },
                ]
            else:
                tasks = [
                    {
                        "task_id": f"{stage_id}_task_1",
                        "task_type": "code",
                        "title": f"「{topic}」综合实战项目",
                        "task": f"「{topic}」综合实战项目",
                        "description": "将所学知识应用到实际项目中，完成综合练习",
                        "resource_type": "code",
                        "estimated_hours": 3.0,
                        "estimated_minutes": 180,
                        "difficulty": "中高级" if knowledge in ("中高级", "高级") else "中级",
                        "status": "not_started",
                        "prerequisite_task_ids": [],
                    },
                    {
                        "task_id": f"{stage_id}_task_2",
                        "task_type": "document",
                        "title": "撰写学习总结并梳理知识体系",
                        "task": "撰写学习总结并梳理知识体系",
                        "description": "回顾整个学习过程，总结核心知识点和收获",
                        "resource_type": "document",
                        "estimated_hours": 1.0,
                        "estimated_minutes": 60,
                        "difficulty": "初级",
                        "status": "not_started",
                        "prerequisite_task_ids": [],
                    },
>>>>>>> Stashed changes
                ]

            # 为薄弱点插入额外任务
            for w in weaknesses:
                if w and w in topic:
                    tasks.insert(1, {
<<<<<<< Updated upstream
                        "task": f"重点补习: {w}",
=======
                        "task_id": f"{stage_id}_task_review_{w[:8].replace(' ', '_')}",
                        "task_type": "exercise",
                        "title": f"重点补习弱项: {w}（完成专项练习）",
                        "task": f"重点补习弱项: {w}（完成专项练习）",
                        "description": f"针对薄弱点「{w}」进行强化练习",
>>>>>>> Stashed changes
                        "resource_type": "exercise",
                        "estimated_hours": 1.0,
                        "estimated_minutes": 60,
                        "difficulty": "初级",
                        "status": "not_started",
                        "prerequisite_task_ids": [],
                    })

            stages.append({
<<<<<<< Updated upstream
                "title": f"阶段{i}: {topic}",
                "objectives": f"学完本阶段，你将能够理解并应用{topic}的核心内容",
=======
                "stage_id": stage_id,
                "order": i,
                "title": f"阶段{i}: {topic}",
                "description": f"学完本阶段，你将能够理解并应用「{topic}」的核心内容",
                "objectives": f"学完本阶段，你将能够理解并应用「{topic}」的核心内容",
                "learning_objectives": [
                    f"理解「{topic}」的核心概念和原理",
                    f"掌握「{topic}」的基本应用方法",
                ],
                "knowledge_point_ids": [],
                "status": "active" if i == 1 else "locked",
                "estimated_days": 3,
                "unlock_conditions": [] if i == 1 else [f"完成阶段{i - 1}所有任务"],
>>>>>>> Stashed changes
                "topics": [topic],
                "tasks": tasks,
            })

        # 根据知识水平调整预估天数
        day_multiplier = {"初级": 1.5, "中级": 1.0, "高级": 0.7}
        multiplier = day_multiplier.get(knowledge, 1.0)
        estimated_days = max(1, int(len(stages) * 3 * multiplier))

        plan = {
            "course_id": (current_path or {}).get("course_id", "unknown"),
            "version": (current_path or {}).get("version", 0) + 1,
            "goal": goal,
            "stages": stages,
            "current_stage": 1,
            "estimated_days": estimated_days,
        }

        return json.dumps(plan, ensure_ascii=False, indent=2)
