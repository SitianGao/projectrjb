"""
EduAgent FastAPI 入口

启动流程：
1. 日志系统初始化
2. LLM 客户端创建（自动检测 DeepSeek/OpenAI 配置）
3. ProfileService 初始化（注册到 profile_api 依赖注入）
4. 数据库初始化（创建表）
5. 路由注册
6. 启动 uvicorn
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.logger import setup_logging
from database import init_db

# ---- 日志系统最先初始化 ----
setup_logging()
logger = logging.getLogger(__name__)


# ---- 应用生命周期 ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理：
    - startup: 初始化 LLM 客户端 → ProfileService → 数据库
    - shutdown: 清理资源
    """
    # ---- startup ----
    logger.info("===== EduAgent Backend 启动中 =====")

    # 1. 数据库初始化
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.warning("数据库初始化失败: %s (可能已存在表)", e)

    # 2. LLM 客户端初始化
    from agents.llm_client import create_llm_client
    from api.profile_api import init_profile_service

    llm_client = create_llm_client()
    if llm_client.provider == "none":
        logger.warning(
            "⚠ 未配置 LLM API Key（DEEPSEEK_API_KEY / OPENAI_API_KEY）。"
            "画像 API 将不可用，但测试仍可运行。"
        )
    init_profile_service(llm_client)

    # 3. 其他 Service 初始化（后续阶段补充）
    # from api.planner_api import init_planner_service
    # init_planner_service(llm_client)
    # ... tutor, resource, evaluate ...

    logger.info("===== EduAgent Backend 启动完成 =====")

    yield  # ---- 应用运行中 ----

    # ---- shutdown ----
    logger.info("===== EduAgent Backend 关闭中 =====")
    # 预留：关闭 LLM 客户端连接池、清理临时文件等


app = FastAPI(
    title="EduAgent Backend",
    description="个性化学习多智能体系统 API",
    version="0.1.0",
    lifespan=lifespan,
)

# ---- CORS 配置 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- 注册各模块路由 ----
from api.profile_api import router as profile_router
from api.planner_api import router as planner_router
from api.resource_api import router as resource_router
from api.tutor_api import router as tutor_router
from api.evaluate_api import router as evaluate_router
from api.task_api import router as task_router

app.include_router(profile_router, prefix="/api/profile", tags=["画像"])
app.include_router(planner_router, prefix="/api/planner", tags=["规划"])
app.include_router(resource_router, prefix="/api/resource", tags=["资源"])
app.include_router(tutor_router, prefix="/api/tutor", tags=["辅导"])
app.include_router(evaluate_router, prefix="/api/evaluate", tags=["评估"])
app.include_router(task_router, prefix="/api/task", tags=["任务"])


@app.get("/")
async def root():
    """健康检查"""
    logger.info("健康检查请求")
    return {"status": "ok", "service": "EduAgent Backend"}


logger.info("EduAgent Backend 路由注册完成")
