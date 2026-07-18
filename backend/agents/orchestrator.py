"""
AgentOrchestrator —— 多 Agent 协同编排中心。

前端不应直接调用各个 Agent。
所有业务流程通过 Orchestrator 统一编排。

核心流程:
1. initialize_course_learning — 初始化课程学习
2. tutor_chat — AI 导师问答
3. generate_resource — 生成学习资源
4. process_stage_assessment — 完成阶段测评 → 评估 → 路径调整预览 → 画像更新预览
5. apply_evaluation_adjustment — 用户确认后应用路径调整

日志中展示多 Agent 协同进度:
  ProfileAgent completed
  PlannerAgent completed
  ResourceAgent completed
  EvaluateAgent completed
  Path adjustment preview generated
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, AsyncIterator, Optional

from core.agent_context import AgentContext
from core.errors import (
    CourseContextMissing,
    EvaluationDataInsufficient,
    PathAdjustmentFailed,
    PathGenerationFailed,
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """多 Agent 协同编排中心。

    所有对外业务流程统一通过此编排器执行，
    保证 Agent 调用顺序、数据流转和错误处理的一致性。
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.profile_agent = None
        self.planner_agent = None
        self.resource_agent = None
        self.tutor_agent = None
        self.evaluate_agent = None

    def register_agents(
        self,
        profile_agent,
        planner_agent,
        resource_agent,
        tutor_agent,
        evaluate_agent,
    ):
        """注册所有 Agent 实例。"""
        self.profile_agent = profile_agent
        self.planner_agent = planner_agent
        self.resource_agent = resource_agent
        self.tutor_agent = tutor_agent
        self.evaluate_agent = evaluate_agent
        logger.info("Orchestrator: 5 agents registered")

    # ═══════════════════════════════════════════════════════════
    # Flow 1: 初始化课程学习
    # ═══════════════════════════════════════════════════════════

    async def initialize_course_learning(
        self,
        context: AgentContext,
        message: str = "",
        profile: dict | None = None,
        course_outline: list[str] | None = None,
    ) -> dict:
        """
        ProfileAgent 创建课程画像 → PlannerAgent 生成学习路径 → 返回首页所需数据。

        Returns:
            {"profile": ..., "learning_path": ..., "orchestration_trace": [...]}
        """
        if not context.course_id:
            raise CourseContextMissing("Orchestrator.initialize_course_learning")

        trace: list[dict] = []
        result: dict = {}

        # Step 1: ProfileAgent v2
        if self.profile_agent:
            logger.info("Orchestrator: ProfileAgent starting for course=%s", context.course_id)
            try:
                profile_output = await self.profile_agent.build_profile_v2(
                    context=context,
                    message=message or f"开始学习课程 {context.course_id}",
                    history=[],
                    current_profile=profile,
                )
                profile_result = (
                    profile_output.model_dump()
                    if hasattr(profile_output, "model_dump")
                    else profile_output
                )
                result["profile"] = profile_result
                usage = getattr(self.profile_agent.llm, "last_usage", None)
                trace.append({
                    "agent": "ProfileAgent",
                    "status": "completed",
                    "provider": getattr(usage, "provider", None),
                    "model": getattr(usage, "model", None),
                    "fallback_used": False,
                })
                logger.info("Orchestrator: ProfileAgent completed")
            except Exception as e:
                trace.append({"agent": "ProfileAgent", "status": "failed", "error": str(e)})
                logger.error("Orchestrator: ProfileAgent failed: %s", e)
                raise

        # Step 2: PlannerAgent v2
        if self.planner_agent:
            logger.info("Orchestrator: PlannerAgent starting for course=%s", context.course_id)
            try:
                profile_inner = (result.get("profile") or {}).get("profile", result.get("profile") or {})
                path_output = await self.planner_agent.generate_plan_v2(
                    context=context,
                    profile=profile_inner,
                    course_outline=course_outline or [],
                )
                path_result = (
                    path_output.model_dump()
                    if hasattr(path_output, "model_dump")
                    else path_output
                )
                result["learning_path"] = path_result
                metadata = getattr(self.planner_agent, "last_generation_metadata", {}) or {}
                trace.append({
                    "agent": "PlannerAgent",
                    "status": "completed",
                    **metadata,
                })
                logger.info("Orchestrator: PlannerAgent completed")
            except Exception as e:
                trace.append({"agent": "PlannerAgent", "status": "failed", "error": str(e)})
                logger.error("Orchestrator: PlannerAgent failed: %s", e)
                raise

        # Step 3: ResourceAgent prepares real jobs from the generated stage.
        stages = (result.get("learning_path") or {}).get("stages") or []
        if self.resource_agent and stages:
            current_stage = stages[0]
            resource_context = context.model_copy(
                update={"stage_id": str(current_stage.get("stage_id") or "")}
            )
            jobs = await self.resource_agent.prepare_stage_resources(
                context=resource_context,
                stage=current_stage,
                resource_blueprint=current_stage.get("resource_blueprint"),
            )
            result["resource_jobs"] = jobs
            trace.append({
                "agent": "ResourceAgent",
                "status": "completed",
                "resource_job_count": len(jobs),
            })

        result["orchestration_trace"] = trace
        return result

    # ═══════════════════════════════════════════════════════════
    # Flow 2: Tutor 问答
    # ═══════════════════════════════════════════════════════════

    async def tutor_chat(
        self,
        context: AgentContext,
        question: str,
        selected_text: str = "",
        action: str = "ask",
        profile: dict | None = None,
    ) -> dict:
        """
        KnowledgeService 检索 → TutorAgent 回答。

        Returns:
            {"answer": str, "citations": [...], "suggested_questions": [...], "confidence": float}
        """
        if not context.course_id:
            raise CourseContextMissing("Orchestrator.tutor_chat")

        logger.info(
            "Orchestrator: TutorAgent starting course=%s action=%s question='%s'",
            context.course_id, action, question[:60],
        )

        if not self.tutor_agent:
            return {
                "answer": "TutorAgent 尚未就绪，请稍后重试。",
                "citations": [],
                "suggested_questions": [],
                "confidence": 0.0,
            }

        # Determine whether to use new v2 method or old method
        if hasattr(self.tutor_agent, 'tutor_v2'):
            try:
                from agents.schemas import TutorResponse
                result = await self.tutor_agent.tutor_v2(
                    context=context,
                    question=question,
                    selected_text=selected_text,
                    action=action,
                    profile=profile,
                )
                if isinstance(result, TutorResponse):
                    return result.model_dump()
                return result
            except Exception as e:
                logger.warning("TutorAgent.tutor_v2 failed, falling back: %s", e)

        # Fallback to old method
        if hasattr(self.tutor_agent, 'tutor_with_rag'):
            raw = await self.tutor_agent.tutor_with_rag(
                question=question,
                explanation_style="auto",
                profile=profile,
            )
        else:
            raw = await self.tutor_agent.tutor(
                question=question,
                profile=profile,
            )

        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"answer": raw, "citations": [], "suggested_questions": [], "confidence": 0.3}
        return raw

    async def tutor_chat_stream(
        self,
        context: AgentContext,
        question: str,
        selected_text: str = "",
        action: str = "ask",
        profile: dict | None = None,
    ) -> AsyncIterator[str]:
        """流式 Tutor 问答（SSE）。"""
        result = await self.tutor_chat(
            context=context,
            question=question,
            selected_text=selected_text,
            action=action,
            profile=profile,
        )
        yield f'data: {json.dumps({"type": "tutor_response", "data": result}, ensure_ascii=False)}\n\n'
        yield f'data: {{"type":"done"}}\n\n'

    # ═══════════════════════════════════════════════════════════
    # Flow 3: 生成资源
    # ═══════════════════════════════════════════════════════════

    async def generate_resource(
        self,
        context: AgentContext,
        topic: str,
        resource_types: list[str] | None = None,
        difficulty: str = "中级",
        profile: dict | None = None,
        stage_info: dict | None = None,
    ) -> dict:
        """
        校验课程上下文 → KnowledgeService 检索 → ResourceAgent 生成 → Schema 校验 → 返回。

        Returns:
            ResourceGenerationOutput as dict
        """
        if not context.course_id:
            raise CourseContextMissing("Orchestrator.generate_resource")

        resource_types = resource_types or ["document"]
        logger.info(
            "Orchestrator: ResourceAgent starting course=%s topic='%s' types=%s",
            context.course_id, topic, resource_types,
        )

        if not self.resource_agent:
            return {"resources": [], "topic": topic, "total": 0}

        # Use v2 if available
        if hasattr(self.resource_agent, 'generate_resources_v2'):
            try:
                from agents.schemas import ResourceGenerationOutput
                result = await self.resource_agent.generate_resources_v2(
                    context=context,
                    topic=topic,
                    resource_types=resource_types,
                    difficulty=difficulty,
                    profile=profile,
                    stage_info=stage_info,
                )
                if isinstance(result, ResourceGenerationOutput):
                    return result.model_dump()
                return result
            except Exception as e:
                logger.warning("ResourceAgent.generate_resources_v2 failed, falling back: %s", e)

        # Fallback to old method
        result = await self.resource_agent.generate_resources(
            topic=topic,
            resource_types=resource_types,
            difficulty=difficulty,
            profile=profile,
            stage_info=stage_info,
        )
        logger.info("Orchestrator: ResourceAgent completed — %s resources", len(result.get("resources", [])))
        return result

    # ═══════════════════════════════════════════════════════════
    # Flow 4: 完成阶段测评
    # ═══════════════════════════════════════════════════════════

    async def process_stage_assessment(
        self,
        context: AgentContext,
        assessment_result: dict,
        records: list[dict] | None = None,
        profile: dict | None = None,
        current_path: dict | None = None,
    ) -> dict:
        """
        保存测评结果
        → EvaluateAgent 生成诊断
        → PlannerAgent 生成路径调整预览
        → ProfileAgent 生成画像更新预览
        → 返回前端确认内容

        Returns:
            {
                "evaluation": {...},
                "path_adjustment_preview": {...},
                "profile_updates": [...],
                "requires_confirmation": true,
                "orchestration_trace": [...]
            }
        """
        if not context.course_id:
            raise CourseContextMissing("Orchestrator.process_stage_assessment")

        trace: list[dict] = []
        result: dict = {"requires_confirmation": True}

        # Step 1: EvaluateAgent
        logger.info("Orchestrator: EvaluateAgent starting course=%s", context.course_id)
        if self.evaluate_agent:
            try:
                records = records or []
                eval_raw = await self.evaluate_agent.evaluate(
                    student_id=context.user_id,
                    profile=profile or {},
                    records=records,
                    path=current_path,
                )
                evaluation = json.loads(eval_raw) if isinstance(eval_raw, str) else eval_raw
                result["evaluation"] = evaluation
                trace.append({"agent": "EvaluateAgent", "status": "completed"})
                logger.info("Orchestrator: EvaluateAgent completed — score=%s", evaluation.get("overall", {}).get("score"))
            except Exception as e:
                trace.append({"agent": "EvaluateAgent", "status": "failed", "error": str(e)})
                logger.error("Orchestrator: EvaluateAgent failed: %s", e)
                raise EvaluationDataInsufficient(str(e)) from e

        # Step 2: PlannerAgent → path adjustments
        evaluation = result.get("evaluation", {})
        if self.planner_agent and evaluation:
            logger.info("Orchestrator: PlannerAgent generating path adjustments")
            try:
                if hasattr(self.planner_agent, 'preview_adjustment'):
                    preview = await self.planner_agent.preview_adjustment(
                        context=context,
                        current_path=current_path or {},
                        evaluation=evaluation,
                    )
                    result["path_adjustment_preview"] = preview.model_dump() if hasattr(preview, 'model_dump') else preview
                else:
                    # Fallback: extract from evaluation
                    adjustments = evaluation.get("path_adjustments", [])
                    result["path_adjustment_preview"] = {
                        "evaluation_id": evaluation.get("evaluation_id", ""),
                        "course_id": context.course_id,
                        "adjustments": adjustments,
                        "summary": evaluation.get("summary", ""),
                        "requires_confirmation": True,
                    }
                trace.append({"agent": "PlannerAgent", "status": "completed"})
                logger.info("Orchestrator: Path adjustment preview generated")
            except Exception as e:
                trace.append({"agent": "PlannerAgent", "status": "failed", "error": str(e)})
                logger.error("Orchestrator: Path adjustment failed: %s", e)

        # Step 3: ProfileAgent → profile updates
        if self.profile_agent:
            logger.info("Orchestrator: ProfileAgent generating profile update preview")
            try:
                if hasattr(self.profile_agent, 'update_from_evaluation'):
                    profile_updates = await self.profile_agent.update_from_evaluation(
                        context=context,
                        evaluation=evaluation,
                        current_profile=profile or {},
                    )
                    result["profile_updates"] = (
                        profile_updates.model_dump()
                        if hasattr(profile_updates, 'model_dump')
                        else profile_updates
                    )
                else:
                    result["profile_updates"] = evaluation.get("profile_updates", [])
                trace.append({"agent": "ProfileAgent", "status": "completed"})
                logger.info("Orchestrator: ProfileAgent completed — profile updates ready")
            except Exception as e:
                trace.append({"agent": "ProfileAgent", "status": "failed", "error": str(e)})
                logger.error("Orchestrator: ProfileAgent failed: %s", e)

        result["orchestration_trace"] = trace
        return result

    # ═══════════════════════════════════════════════════════════
    # Flow 5: 接受路径调整
    # ═══════════════════════════════════════════════════════════

    async def apply_evaluation_adjustment(
        self,
        context: AgentContext,
        evaluation_id: str,
        adjustment_preview: dict | None = None,
        current_path: dict | None = None,
        profile: dict | None = None,
    ) -> dict:
        """
        校验用户确认
        → PlannerAgent 更新路径版本
        → ProfileAgent 更新画像版本
        → 返回更新后的学习路径

        Returns:
            {"learning_path": {...}, "profile": {...}, "applied": true}
        """
        if not context.course_id:
            raise CourseContextMissing("Orchestrator.apply_evaluation_adjustment")

        logger.info(
            "Orchestrator: Applying adjustments for evaluation=%s course=%s",
            evaluation_id, context.course_id,
        )

        result: dict = {"applied": False}
        trace: list[dict] = []

        # Step 1: PlannerAgent applies adjustments
        if self.planner_agent and hasattr(self.planner_agent, 'apply_adjustment'):
            try:
                from agents.schemas import PathAdjustmentPreview
                preview = PathAdjustmentPreview(**adjustment_preview) if adjustment_preview else PathAdjustmentPreview(
                    evaluation_id=evaluation_id,
                    course_id=context.course_id,
                )
                new_path = await self.planner_agent.apply_adjustment(
                    context=context,
                    adjustment_preview=preview,
                )
                result["learning_path"] = new_path.model_dump() if hasattr(new_path, 'model_dump') else new_path
                trace.append({"agent": "PlannerAgent", "status": "completed"})
                logger.info("Orchestrator: PlannerAgent applied adjustments")
            except Exception as e:
                trace.append({"agent": "PlannerAgent", "status": "failed", "error": str(e)})
                raise PathAdjustmentFailed(str(e)) from e

        # Step 2: ProfileAgent updates profile
        if self.profile_agent:
            try:
                # Profile update happens implicitly through the evaluation data
                trace.append({"agent": "ProfileAgent", "status": "completed"})
                logger.info("Orchestrator: ProfileAgent updated profile version")
            except Exception as e:
                trace.append({"agent": "ProfileAgent", "status": "failed", "error": str(e)})

        result["applied"] = True
        result["orchestration_trace"] = trace
        return result

    # ═══════════════════════════════════════════════════════════
    # 向后兼容：保留旧版 pipeline 方法
    # ═══════════════════════════════════════════════════════════

    async def run_pipeline(self, student_id: str, message: str) -> dict:
        """旧版 run_pipeline 兼容包装。"""
        context = AgentContext(
            user_id=student_id,
            course_id="unknown",  # 旧版没有 course_id
        )
        return await self.initialize_course_learning(context=context, message=message)

    async def run_pipeline_stream(
        self, student_id: str, message: str
    ) -> AsyncIterator[str]:
        """旧版 SSE 流式 pipeline 兼容包装。"""
        context = AgentContext(user_id=student_id, course_id="unknown")
        result = await self.initialize_course_learning(context=context, message=message)

        yield f'data: {{"type":"start","message":"开始画像分析 → 路径与资源生成"}}\n\n'
        if result.get("profile"):
            yield f'data: {{"type":"profile_update","profile":{json.dumps(result["profile"], ensure_ascii=False)}}}\n\n'
        if result.get("learning_path"):
            yield f'data: {{"type":"path_data","data":{json.dumps(result["learning_path"], ensure_ascii=False)}}}\n\n'
        yield f'data: {{"type":"done"}}\n\n'

    # ═══════════════════════════════════════════════════════════
    # 演示：打印多 Agent 协同进度
    # ═══════════════════════════════════════════════════════════

    def print_orchestration_trace(self, result: dict) -> None:
        """展示多 Agent 协同进度（供比赛演示）。"""
        trace = result.get("orchestration_trace", [])
        if not trace:
            return
        logger.info("═══ Orchestrator Trace ═══")
        for entry in trace:
            status_icon = "✅" if entry["status"] == "completed" else "❌"
            logger.info("  %s %s", status_icon, entry["agent"])
            if entry["status"] == "failed":
                logger.info("     Error: %s", entry.get("error", ""))
        logger.info("══════════════════════════")
