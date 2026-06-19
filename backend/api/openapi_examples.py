"""Reusable OpenAPI response examples for the backend API."""

from __future__ import annotations

from copy import deepcopy

from api.error_codes import get_error_spec


SUCCESS_EXAMPLE = {
    "success": True,
    "data": {},
    "message": "ok",
}

TASK_SUCCESS_EXAMPLE = {
    "success": True,
    "data": {
        "task_id": "task_abc12345",
        "status": "pending",
        "progress": 0,
        "message": "资源生成任务已创建",
        "phase": "queued",
        "result": None,
        "error": None,
        "created_at": "2026-06-19T10:00:00Z",
        "updated_at": "2026-06-19T10:00:00Z",
        "started_at": None,
        "finished_at": None,
        "duration_ms": None,
        "progress_history": [
            {
                "progress": 0,
                "message": "资源生成任务已创建",
                "phase": "queued",
                "at": "2026-06-19T10:00:00Z",
            }
        ],
    },
    "message": "资源生成任务已创建",
}

SSE_STREAM_EXAMPLE = (
    'data: {"type":"start","message":"开始处理"}\n\n'
    'data: {"type":"delta","content":"...","delta":"..."}\n\n'
    'data: {"type":"data","data":{}}\n\n'
    'data: {"type":"error","code":"ERROR_CODE","message":"错误描述"}\n\n'
    'data: {"type":"done"}\n\n'
)


def error_example(code: str) -> dict:
    spec = get_error_spec(code)
    return {
        "success": False,
        "error": True,
        "code": spec.code,
        "message": spec.message,
    }


def json_responses(*error_codes: str, success_example: dict | None = None) -> dict:
    responses = {
        200: {
            "description": "统一成功响应",
            "content": {
                "application/json": {
                    "example": deepcopy(success_example or SUCCESS_EXAMPLE),
                }
            },
        },
        422: {
            "description": "统一参数错误",
            "content": {
                "application/json": {
                    "example": error_example("VALIDATION_ERROR"),
                }
            },
        },
        500: {
            "description": "统一服务端错误",
            "content": {
                "application/json": {
                    "example": error_example("INTERNAL_SERVER_ERROR"),
                }
            },
        },
    }

    for code in error_codes:
        spec = get_error_spec(code)
        responses[spec.status_code] = {
            "description": f"{spec.code}: {spec.message}",
            "content": {
                "application/json": {
                    "example": error_example(spec.code),
                }
            },
        }
    return responses


def sse_responses(*error_codes: str) -> dict:
    responses = {
        200: {
            "description": "SSE stream: start/delta/data/error/done",
            "content": {
                "text/event-stream": {
                    "example": SSE_STREAM_EXAMPLE,
                }
            },
        },
        422: {
            "description": "统一参数错误",
            "content": {
                "application/json": {
                    "example": error_example("VALIDATION_ERROR"),
                }
            },
        },
    }
    for code in error_codes:
        spec = get_error_spec(code)
        responses[spec.status_code] = {
            "description": f"SSE error event: {spec.code}",
            "content": {
                "text/event-stream": {
                    "example": f'data: {{"type":"error","code":"{spec.code}","message":"{spec.message}"}}\n\ndata: {{"type":"done"}}\n\n',
                }
            },
        }
    return responses
