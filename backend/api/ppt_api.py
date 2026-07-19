"""
PPT 生成 API
- POST /api/ppt/generate          生成 PPT（异步任务）
- GET  /api/ppt/status/{sid}      查询 PPT 生成状态
- GET  /api/ppt/{resource_id}     获取 PPT 资源详情
- GET  /api/ppt/{resource_id}/download  下载 PPT 文件
"""
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.openapi_examples import json_responses
from api.response import ApiError, ok
from database import SessionLocal, get_db
from api.auth_api import require_user
from deps import ppt_generation_service, resource_service
from models.auth import Course, User
from models.resource import Resource

router = APIRouter()


class PptGenerateRequest(BaseModel):
    """PPT 生成请求"""
    topic: str = Field(..., examples=["卷积神经网络 CNN"])
    difficulty: str = Field(default="中级", examples=["初级", "中级", "高级"])
    course_id: Optional[str] = None
    task_id: Optional[str] = None
    stage_id: Optional[str] = None
    template_id: Optional[str] = None
    search: bool = Field(default=False, description="是否联网搜索")
    ai_image: bool = Field(default=True, description="是否 AI 配图")


def _require_owned_course(
    db: Session,
    user: User,
    *,
    course_id: Optional[str],
) -> Course:
    """验证课程所有权"""
    query = db.query(Course).filter(Course.user_id == user.id)
    if course_id:
        query = query.filter(Course.id == course_id)
    elif user.active_course_id:
        query = query.filter(Course.id == user.active_course_id)
    course = query.order_by(Course.updated_at.desc()).first()
    if not course:
        raise ApiError(
            "COURSE_SCOPE_MISMATCH",
            "课程不存在或不属于当前登录用户",
            status_code=404,
        )
    return course


@router.post(
    "/generate",
    responses=json_responses("PPT_GENERATE_FAILED", "PPT_NOT_ENABLED"),
)
async def generate_ppt(
    request: PptGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """生成 PPT，返回 task_id；前端轮询 /api/task/{task_id}/status。"""
    from deps import task_service

    course = _require_owned_course(db, user, course_id=request.course_id)

    task = task_service.create("PPT 生成任务已创建", owner_user_id=user.id)

    async def run_ppt_task():
        db = SessionLocal()
        try:
            def update_progress(progress: int, phase: str, message: str):
                task_service.update(
                    task["task_id"],
                    status="running",
                    progress=progress,
                    phase=phase,
                    message=message,
                )

            update_progress(5, "started", "PPT 生成任务已开始")

            # 获取学生画像
            from deps import profile_service
            profile_service.get_or_create_student(db, course.student_id)
            profile = profile_service.get_profile(db, course.student_id)

            # 获取关卡信息
            stage_info = None
            if request.stage_id:
                from services.resource_service import _build_stage_info
                from models.learning_path import LearningPath
                path = (
                    db.query(LearningPath)
                    .filter(
                        LearningPath.course_id == course.id,
                        LearningPath.student_id == course.student_id,
                        LearningPath.status != "archived",
                    )
                    .order_by(
                        (LearningPath.status == "active").desc(),
                        LearningPath.version.desc(),
                    )
                    .first()
                )
                if path:
                    stage_info = _build_stage_info(path, request.topic, stage_id=request.stage_id)

            update_progress(20, "generating_outline", "正在生成个性化 PPT 大纲")

            # 调用 PPT 生成服务
            result = await ppt_generation_service.generate_ppt_for_task(
                db=db,
                user_id=str(user.id),
                course_id=str(course.id),
                task_id=request.task_id or "default_task",
                topic=request.topic,
                difficulty=request.difficulty,
                profile=profile,
                stage_info=stage_info,
                on_progress=update_progress,
            )

            task_service.update(
                task["task_id"],
                status="done",
                progress=100,
                phase="completed",
                message="PPT 生成完成",
                result=result,
            )

        except Exception as exc:
            task_service.update(
                task["task_id"],
                status="failed",
                progress=100,
                phase="failed",
                message="PPT 生成失败",
                error={"code": "PPT_GENERATE_FAILED", "message": str(exc)},
            )
        finally:
            db.close()

    background_tasks.add_task(run_ppt_task)
    return ok(task, "PPT 生成任务已创建")


@router.get(
    "/status/{sid}",
    responses=json_responses("PPT_STATUS_QUERY_FAILED"),
)
async def get_ppt_status(
    sid: str,
    user=Depends(require_user),
):
    """查询 PPT 生成状态（通过星火 API 的 sid）"""
    try:
        status = await ppt_generation_service.query_generation_status(sid)
        return ok(status)
    except Exception as exc:
        raise ApiError("PPT_STATUS_QUERY_FAILED", str(exc), status_code=500)


@router.get(
    "/{resource_id}",
    responses=json_responses("PPT_NOT_FOUND"),
)
async def get_ppt_resource(
    resource_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """获取 PPT 资源详情"""
    resource = resource_service.get_resource_detail(
        db,
        user=user,
        resource_id=resource_id,
    )
    if not resource:
        raise ApiError("PPT_NOT_FOUND")
    if resource.get("type") != "ppt":
        raise ApiError("PPT_NOT_FOUND", "资源类型不是 PPT", status_code=400)
    return ok(resource)


@router.get(
    "/{resource_id}/download",
    responses=json_responses("PPT_NOT_FOUND", "PPT_FILE_NOT_FOUND"),
)
async def download_ppt(
    resource_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    """下载 PPT 文件"""
    # 获取资源
    resource = (
        db.query(Resource)
        .filter(Resource.id == resource_id, Resource.type == "ppt")
        .first()
    )
    if not resource:
        raise ApiError("PPT_NOT_FOUND")

    # 验证所有权
    course = (
        db.query(Course)
        .filter(
            Course.student_id == resource.student_id,
            Course.user_id == user.id,
        )
        .first()
    )
    if not course:
        raise ApiError("PPT_NOT_FOUND", "无权访问此资源", status_code=403)

    # 解析文件路径
    import json
    content = {}
    try:
        content = json.loads(resource.content) if resource.content else {}
    except (json.JSONDecodeError, TypeError):
        pass

    file_path = content.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise ApiError("PPT_FILE_NOT_FOUND", "PPT 文件不存在", status_code=404)

    # 返回文件
    filename = content.get("file_name", f"{resource.topic}.pptx")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
