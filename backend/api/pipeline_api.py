"""
统一流水线 API — 画像 → 路径端到端生成
- POST /api/pipeline/generate  画像分析 + 路径生成（SSE 流式）
"""
import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.response import sse_done, sse_error
from database import SessionLocal
from deps import orchestrator, profile_service, planner_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic 请求模型 ───────────────────────

class PipelineRequest(BaseModel):
    student_id: str
    message: str


# ── 端点实现 ─────────────────────────────────

@router.post("/generate")
async def pipeline_generate(request: PipelineRequest):
    """
    端到端流水线：画像分析 → 学习路径生成（SSE 流式）。

    事件类型：
    - start          开始
    - profile_update 画像结果
    - path_data      路径结果
    - error          错误
    - done           完成
    """

    async def event_generator():
        db = SessionLocal()
        try:
            # 确保学生存在
            profile_service.get_or_create_student(db, request.student_id)

            async for event in orchestrator.run_pipeline_stream(
                student_id=request.student_id,
                message=request.message,
            ):
                yield event

                # 检测 profile_update → 持久化画像
                if '"type":"profile_update"' in event:
                    try:
                        json_str = _extract_json(event)
                        payload = json.loads(json_str)
                        profile_data = payload.get("profile", {})
                        if profile_data:
                            profile_service.save_profile(
                                db, request.student_id, profile_data
                            )
                            logger.info(f"画像已持久化: student={request.student_id}")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"解析 profile_update 失败: {e}")

                # 检测 path_data → 持久化路径
                if '"type":"path_data"' in event:
                    try:
                        json_str = _extract_json(event)
                        payload = json.loads(json_str)
                        path_data = payload.get("data", {})
                        if path_data and path_data.get("stages"):
                            planner_service.save_path(
                                db, request.student_id, path_data
                            )
                            logger.info(f"路径已持久化: student={request.student_id}")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"解析 path_data 失败: {e}")

        except Exception:
            yield sse_error("PIPELINE_GENERATE_FAILED", "端到端生成失败，请稍后重试")
            yield sse_done()
        finally:
            db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _extract_json(event: str) -> str:
    """从 SSE 行中提取 JSON 字符串。"""
    prefix = "data: "
    s = event.strip()
    if s.startswith(prefix):
        s = s[len(prefix):]
    return s
