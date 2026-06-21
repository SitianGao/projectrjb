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
    generic_exception_handler,
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
app.add_exception_handler(Exception, generic_exception_handler)


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
app.include_router(resource_router, prefix="/api/resources", tags=["资源兼容"])
app.include_router(tutor_router, prefix="/api/tutor", tags=["辅导"])
app.include_router(evaluate_router, prefix="/api/evaluate", tags=["评估"])
app.include_router(task_router, prefix="/api/task", tags=["任务"])


# ---- 启动事件 ----
@app.on_event("startup")
async def startup():
    """应用启动时自动初始化数据库表 + RAG 组件状态检查"""
    # 1. 数据库初始化
    init_db()
    logger.info("数据库表初始化完成")

    # 2. RAG 组件状态检查（Day 13: 确保知识库可连通）
    try:
        from rag.vector_store import default_store
        count = default_store.count()
        logger.info(f"RAG 向量库就绪: collection='{default_store.collection_name}', 文档数={count}")
    except Exception as e:
        logger.warning(f"RAG 向量库未就绪（首次请求时将自动初始化）: {e}")

    try:
        from rag.embedding import default_embedding
        logger.info(f"RAG 嵌入模型已配置: {default_embedding.model_name}（首次使用时加载）")
    except Exception as e:
        logger.warning(f"RAG 嵌入模型配置异常: {e}")

    try:
        from rag.knowledge_loader import DEFAULT_KNOWLEDGE_DIR
        import os
        if os.path.isdir(DEFAULT_KNOWLEDGE_DIR):
            files = [f for f in os.listdir(DEFAULT_KNOWLEDGE_DIR)
                     if f.endswith(('.md', '.json'))]
            logger.info(f"知识库目录就绪: {DEFAULT_KNOWLEDGE_DIR}（{len(files)} 个文件）")
        else:
            logger.warning(f"知识库目录不存在: {DEFAULT_KNOWLEDGE_DIR}")
    except Exception as e:
        logger.warning(f"知识库目录检查失败: {e}")

    # 3. 安全过滤模块状态
    try:
        from safety.content_filter import default_filter
        logger.info("内容安全过滤模块已加载")
    except Exception as e:
        logger.error(f"内容安全过滤模块加载失败: {e}")


@app.get("/")
async def root():
    """健康检查"""
    logger.info("健康检查请求")
    return ok({"status": "ok", "service": "EduAgent Backend"})


logger.info("EduAgent Backend 路由注册完成")
