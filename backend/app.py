"""
EduAgent FastAPI 入口
"""
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.logger import setup_logging
from database import init_db
from api.response import (
    ApiError,
    api_error_handler,
    http_exception_handler,
    ok,
    validation_exception_handler,
)

# ---- 日志系统最先初始化 ----
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EduAgent Backend",
    description="个性化学习多智能体系统 API",
    version="0.1.0",
)

# ---- CORS 配置 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# ---- 注册各模块路由 ----
from api.profile_api import router as profile_router
from api.planner_api import router as planner_router
from api.pipeline_api import router as pipeline_router
from api.resource_api import router as resource_router
from api.tutor_api import router as tutor_router
from api.evaluate_api import router as evaluate_router
from api.task_api import router as task_router

app.include_router(profile_router, prefix="/api/profile", tags=["画像"])
app.include_router(planner_router, prefix="/api/planner", tags=["规划"])
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["编排"])
app.include_router(resource_router, prefix="/api/resource", tags=["资源"])
app.include_router(tutor_router, prefix="/api/tutor", tags=["辅导"])
app.include_router(evaluate_router, prefix="/api/evaluate", tags=["评估"])
app.include_router(task_router, prefix="/api/task", tags=["任务"])


# ---- 启动事件 ----
@app.on_event("startup")
async def startup():
    """应用启动时自动初始化数据库表"""
    init_db()
    logger.info("数据库表初始化完成")


@app.get("/")
async def root():
    """健康检查"""
    logger.info("健康检查请求")
    return ok({"status": "ok", "service": "EduAgent Backend"})


logger.info("EduAgent Backend 路由注册完成")
