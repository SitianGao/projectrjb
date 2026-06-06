"""
EduAgent FastAPI 入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="EduAgent Backend",
    description="个性化学习多智能体系统 API",
    version="0.1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "service": "EduAgent Backend"}


# TODO: 注册各模块路由
# from api.profile_api import router as profile_router
# from api.planner_api import router as planner_router
# from api.resource_api import router as resource_router
# from api.tutor_api import router as tutor_router
# from api.evaluate_api import router as evaluate_router
# from api.task_api import router as task_router
#
# app.include_router(profile_router, prefix="/api/profile", tags=["画像"])
# app.include_router(planner_router, prefix="/api/planner", tags=["规划"])
# app.include_router(resource_router, prefix="/api/resource", tags=["资源"])
# app.include_router(tutor_router, prefix="/api/tutor", tags=["辅导"])
# app.include_router(evaluate_router, prefix="/api/evaluate", tags=["评估"])
# app.include_router(task_router, prefix="/api/task", tags=["任务"])
