"""
依赖注入模块 —— 模块级单例，串联 Agent → Service → API

用法：
    from deps import profile_service
    from database import get_db
    from fastapi import Depends

    @router.post("/chat")
    async def chat(db = Depends(get_db)):
        ...
        await profile_service.chat_stream(db, ...)
"""
from agents.llm_client import LLMClient
from agents.profile_agent import ProfileAgent
from agents.planner_agent import PlannerAgent
from agents.resource_agent import ResourceAgent
from agents.tutor_agent import TutorAgent
from agents.orchestrator import AgentOrchestrator
from rag import default_retriever
from services.profile_service import ProfileService
from services.planner_service import PlannerService
from services.resource_service import ResourceService
from services.tutor_service import TutorService
from services.evaluate_service import EvaluateService
from services.task_service import TaskService
from database import get_db

# ── 全局单例 ──────────────────────────────────
llm_client = LLMClient()

profile_agent = ProfileAgent(llm_client)
profile_service = ProfileService(profile_agent, get_db)

planner_agent = PlannerAgent(llm_client)
planner_service = PlannerService(planner_agent, get_db, profile_service)

resource_agent = ResourceAgent(llm_client)
resource_service = ResourceService(resource_agent, profile_service)

tutor_agent = TutorAgent(llm_client)
tutor_service = TutorService(llm_client, profile_service, tutor_agent, default_retriever)
evaluate_service = EvaluateService(profile_service)
task_service = TaskService()

orchestrator = AgentOrchestrator(llm_client)
orchestrator.register_agents(
    profile_agent,
    planner_agent,
    resource_agent,
    tutor_agent,
    None,  # evaluate_agent — Day 10
)
