"""
Agent 编排器 —— 多 Agent 协同调度

协同流程（v0.1）：
1. ProfileAgent  → 构建/更新学生画像
2. PlannerAgent  → 基于画像生成学习路径
3. ResourceAgent → Day 6（并行）
4. TutorAgent / EvaluateAgent → 按需触发
"""
import json
import logging
from typing import TypedDict, Optional, AsyncIterator

logger = logging.getLogger(__name__)


class StudentState(TypedDict):
    """学生状态 —— 在 Agent 之间流转的共享数据"""
    student_id: str
    message: str
    profile: Optional[dict]
    learning_path: Optional[dict]
    resources: Optional[list]
    chat_history: list


class AgentOrchestrator:
    """
    Agent 编排器

    协同流程：
    1. ProfileAgent  → 构建/更新学生画像
    2. PlannerAgent + ResourceAgent → 并行：生成路径 + 生成资源
    3. 结果推送给前端
    4. TutorAgent / EvaluateAgent → 按需触发（用户主动）
    5. 评估结果 → 反馈调整路径和资源
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        # Agent 实例在注册后赋值
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
        """注册所有 Agent 实例（未实现的 Agent 传 None）"""
        self.profile_agent = profile_agent
        self.planner_agent = planner_agent
        self.resource_agent = resource_agent
        self.tutor_agent = tutor_agent
        self.evaluate_agent = evaluate_agent

    # ================================================================
    #  非流式流水线（供内部 / 程序化调用）
    # ================================================================

    async def run_pipeline(self, student_id: str, message: str) -> dict:
        """执行完整流水线：画像 → 路径（+ 资源，如有）"""
        state = StudentState(
            student_id=student_id,
            message=message,
            profile=None,
            learning_path=None,
            resources=None,
            chat_history=[],
        )

        # Step 1: 画像（必须先执行）
        if self.profile_agent:
            state["profile"] = await self._run_profile(state)

        # Step 2: 路径（依赖画像结果）
        if self.planner_agent:
            state["learning_path"] = await self._run_planner(state)

        # Step 3: 资源（如有 ResourceAgent 则并行执行；Day 6 启用）
        if self.resource_agent:
            state["resources"] = await self._run_resource(state)

        return {
            "profile": state["profile"],
            "learning_path": state["learning_path"],
            "resources": state["resources"],
        }

    # ================================================================
    #  SSE 流式流水线（供 /api/pipeline/generate 使用）
    # ================================================================

    async def run_pipeline_stream(
        self, student_id: str, message: str
    ) -> AsyncIterator[str]:
        """
        SSE 流式执行流水线：画像 → 路径。

        产出 SSE 事件：
            data: {"type":"start","message":"..."}
            data: {"type":"profile_update","profile":{...}}
            data: {"type":"path_data","data":{...}}
            data: {"type":"error","code":"...","message":"..."}
            data: {"type":"done"}
        """
        yield f'data: {{"type":"start","message":"开始画像分析 → 路径生成"}}\n\n'

        state = StudentState(
            student_id=student_id,
            message=message,
            profile=None,
            learning_path=None,
            resources=None,
            chat_history=[],
        )

        # ---- 阶段 1：画像 ----
        if not self.profile_agent:
            yield f'data: {{"type":"error","code":"AGENT_NOT_READY","message":"ProfileAgent 未注册"}}\n\n'
            yield f'data: {{"type":"done"}}\n\n'
            return

        try:
            logger.info(f"[Orchestrator] 开始画像构建: student={student_id}")
            profile_result = await self._run_profile(state)
            state["profile"] = profile_result

            profile_json = json.dumps(profile_result, ensure_ascii=False)
            yield f'data: {{"type":"profile_update","profile":{profile_json}}}\n\n'
            logger.info(f"[Orchestrator] 画像构建完成: student={student_id}")

        except Exception as e:
            logger.error(f"[Orchestrator] 画像构建失败: {e}")
            yield f'data: {{"type":"error","code":"PROFILE_FAILED","message":"画像构建失败: {str(e)}"}}\n\n'
            yield f'data: {{"type":"done"}}\n\n'
            return

        # ---- 阶段 2：路径 ----
        if not self.planner_agent:
            yield f'data: {{"type":"done"}}\n\n'
            return

        try:
            logger.info(f"[Orchestrator] 开始路径生成: student={student_id}")
            path_result = await self._run_planner(state)
            state["learning_path"] = path_result

            path_json = json.dumps(path_result, ensure_ascii=False)
            yield f'data: {{"type":"path_data","data":{path_json}}}\n\n'
            logger.info(f"[Orchestrator] 路径生成完成: student={student_id}")

        except Exception as e:
            logger.error(f"[Orchestrator] 路径生成失败: {e}")
            yield f'data: {{"type":"error","code":"PATH_FAILED","message":"路径生成失败: {str(e)}"}}\n\n'

        yield f'data: {{"type":"done"}}\n\n'

    # ================================================================
    #  各阶段实现
    # ================================================================

    async def _run_profile(self, state: StudentState) -> dict:
        """执行画像 Agent —— 调用 ProfileAgent.build_profile()"""
        result = await self.profile_agent.build_profile(
            student_id=state["student_id"],
            message=state["message"],
            history=state.get("chat_history"),
        )
        return result

    async def _run_planner(self, state: StudentState) -> dict:
        """执行规划 Agent —— 调用 PlannerAgent.build_path()"""
        profile = state.get("profile", {})
        # profile 是 ProfileAgent 输出，含外层 "profile" 字段
        profile_inner = profile.get("profile", profile) if isinstance(profile, dict) else {}
        result = await self.planner_agent.build_path(
            student_id=state["student_id"],
            profile=profile_inner,
        )
        return result

    async def _run_resource(self, state: StudentState) -> dict:
        """执行资源 Agent（Day 6 实现）"""
        # TODO: Day 6 — 对接 ResourceAgent
        return {}
