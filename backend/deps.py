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
from services.profile_service import ProfileService
from services.planner_service import PlannerService
from database import get_db

# ── 全局单例 ──────────────────────────────────
llm_client = LLMClient()

profile_agent = ProfileAgent(llm_client)
profile_service = ProfileService(profile_agent, get_db)

planner_agent = PlannerAgent(llm_client)
planner_service = PlannerService(planner_agent, get_db, profile_service)
