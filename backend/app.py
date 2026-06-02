"""
FastAPI 后端入口
功能：
    - 提供多智能体系统接口
    - 接收用户输入，返回学习路径、资源、知识和评估结果
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from agents.agent_orchestrator import AgentOrchestrator

app = FastAPI(title="EduAgent Backend", version="0.1")

# ==========================
# 请求体模型
# ==========================
class UserRequest(BaseModel):
    student_id: str
    user_input: Dict  # 学生画像输入
    topic: str        # 学习主题
    action: str = "full_pipeline"  # 可选：full_pipeline / record_learning / evaluate
    record: Dict = None  # 如果 action=record_learning, 需要 {"resource": str, "score": float}


# ==========================
# 全局 Orchestrator 存储
# ==========================
orchestrators: Dict[str, AgentOrchestrator] = {}

def get_orchestrator(student_id: str):
    if student_id not in orchestrators:
        orchestrators[student_id] = AgentOrchestrator(student_id)
    return orchestrators[student_id]


# ==========================
# 接口：运行完整流程
# ==========================
@app.post("/run")
def run_pipeline(req: UserRequest):
    agent = get_orchestrator(req.student_id)

    if req.action == "full_pipeline":
        result = agent.run_full_pipeline(req.user_input, req.topic)
        return {"status": "success", "data": result}

    elif req.action == "record_learning":
        if not req.record:
            return {"status": "error", "message": "record missing"}
        agent.record_learning(req.record.get("resource"), req.record.get("score"))
        return {"status": "success", "message": "record added"}

    elif req.action == "evaluate":
        result = agent.evaluate()
        return {"status": "success", "evaluation": result}

    else:
        return {"status": "error", "message": f"unknown action {req.action}"}


# ==========================
# 健康检查
# ==========================
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend running"}