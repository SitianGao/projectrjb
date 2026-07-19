"""EduAgent FastAPI 入口。"""

import logging
import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.openapi_examples import json_responses
from api.response import (
    ApiError,
    api_error_handler,
    generic_exception_handler,
    http_exception_handler,
    ok,
    validation_exception_handler,
)
from database import SessionLocal, init_db
from utils.logger import setup_logging


setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EduAgent Backend",
    description="个性化学习多智能体系统 API",
    version="0.1.0",
)

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
from api.auth_api import router as auth_router
from api.judge_api import router as judge_router
from api.session_api import router as session_router
from api.course_profile_api import router as course_profile_router
from api.classroom_api import router as classroom_router
from api.course_learning_api import router as course_learning_router
from api.ppt_api import router as ppt_router

app.include_router(profile_router, prefix="/api/profile", tags=["画像"])
app.include_router(planner_router, prefix="/api/planner", tags=["规划"])
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["编排"])
app.include_router(resource_router, prefix="/api/resource", tags=["资源"])
app.include_router(resource_router, prefix="/api/resources", tags=["资源兼容"])
app.include_router(tutor_router, prefix="/api/tutor", tags=["辅导"])
app.include_router(evaluate_router, prefix="/api/evaluate", tags=["评估"])
app.include_router(task_router, prefix="/api/task", tags=["任务"])
app.include_router(auth_router, prefix="/api/auth", tags=["账号与课程"])
app.include_router(judge_router, prefix="/api/judge", tags=["在线判题"])
app.include_router(session_router, prefix="/api/session", tags=["会话启动"])
app.include_router(course_profile_router, prefix="/api", tags=["课程画像"])
app.include_router(classroom_router, prefix="/api/classrooms", tags=["互动课堂"])
app.include_router(course_learning_router, prefix="/api/courses", tags=["课程学习"])
app.include_router(ppt_router, prefix="/api/ppt", tags=["PPT 生成"])


@app.on_event("startup")
async def startup():
    """应用启动时自动初始化数据库表和 RAG 状态。"""
    init_db()
    logger.info("数据库表初始化完成")

    try:
        from services.auth_service import auth_service

        db = SessionLocal()
        try:
            auth_service.seed_demo_users(db)
        finally:
            db.close()
    except Exception as exc:
        logger.warning("演示账号初始化失败（不影响已有数据）: %s", exc)

    if os.getenv("INIT_DEMO_COURSE", "true").lower() not in ("0", "false", "no", "off"):
        try:
            from scripts.init_demo_course import init_demo_course

            init_demo_course()
            logger.info("演示课程初始化完成")
        except Exception as exc:
            logger.warning("演示课程初始化失败（不影响正常使用）: %s", exc)

    try:
        from rag.vector_store import default_store

        count = default_store.count()
        logger.info("RAG 向量库就绪: collection='%s', 文档数=%s", default_store.collection_name, count)
    except Exception as exc:
        logger.warning("RAG 向量库未就绪（首次请求时将自动初始化）: %s", exc)

    try:
        from rag.embedding import default_embedding

        logger.info("RAG 嵌入模型已配置: %s（首次使用时加载）", default_embedding.model_name)
    except Exception as exc:
        logger.warning("RAG 嵌入模型配置异常: %s", exc)

    try:
        from rag.knowledge_loader import DEFAULT_KNOWLEDGE_DIR

        if os.path.isdir(DEFAULT_KNOWLEDGE_DIR):
            files = [
                name
                for name in os.listdir(DEFAULT_KNOWLEDGE_DIR)
                if name.endswith((".md", ".json"))
            ]
            logger.info("知识库目录就绪: %s（%s 个文件）", DEFAULT_KNOWLEDGE_DIR, len(files))
        else:
            logger.warning("知识库目录不存在: %s", DEFAULT_KNOWLEDGE_DIR)
    except Exception as exc:
        logger.warning("知识库目录检查失败: %s", exc)

    try:
        from safety.content_filter import default_filter  # noqa: F401

        logger.info("内容安全过滤模块已加载")
    except Exception as exc:
        logger.error("内容安全过滤模块加载失败: %s", exc)


@app.get("/")
async def root():
    """健康检查。"""
    logger.info("健康检查请求")
    return ok({"status": "ok", "service": "EduAgent Backend"})


@app.get("/api/health", responses=json_responses("DATABASE_UNAVAILABLE"))
async def api_health():
    """后端健康检查，供前端联调和 E2E 验收使用。"""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise ApiError("DATABASE_UNAVAILABLE") from exc
    finally:
        db.close()

    return ok({
        "status": "ok",
        "service": "EduAgent Backend",
        "database": "ok",
    })


logger.info("EduAgent Backend 路由注册完成")
