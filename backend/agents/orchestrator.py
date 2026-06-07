"""
Agent 编排器 —— 基于 LangGraph 的多 Agent 协同调度
"""
from typing import TypedDict, Optional


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
        """注册所有 Agent 实例"""
        self.profile_agent = profile_agent
        self.planner_agent = planner_agent
        self.resource_agent = resource_agent
        self.tutor_agent = tutor_agent
        self.evaluate_agent = evaluate_agent

    async def run_pipeline(self, student_id: str, message: str) -> dict:
        """执行完整流水线：画像 → 路径 + 资源"""
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

        # Step 2: 路径 + 资源（并行）
        if self.planner_agent and self.resource_agent:
            import asyncio
            path_result, resource_result = await asyncio.gather(
                self._run_planner(state),
                self._run_resource(state),
            )
            state["learning_path"] = path_result
            state["resources"] = resource_result

        return {
            "profile": state["profile"],
            "learning_path": state["learning_path"],
            "resources": state["resources"],
        }

    async def _run_profile(self, state: StudentState) -> dict:
        """执行画像 Agent"""
        # TODO: 对接队员B的 ProfileAgent
        return {}

    async def _run_planner(self, state: StudentState) -> dict:
        """执行规划 Agent"""
        # TODO: 对接队员B的 PlannerAgent
        return {}

    async def _run_resource(self, state: StudentState) -> dict:
        """执行资源 Agent"""
        # TODO: 对接队员B的 ResourceAgent
        return {}
