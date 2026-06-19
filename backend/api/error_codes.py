"""Central error-code registry for API responses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorSpec:
    code: str
    message: str
    status_code: int


ERROR_SPECS: dict[str, ErrorSpec] = {
    "BAD_REQUEST": ErrorSpec("BAD_REQUEST", "请求参数不正确", 400),
    "VALIDATION_ERROR": ErrorSpec("VALIDATION_ERROR", "参数校验失败", 422),
    "UNAUTHORIZED": ErrorSpec("UNAUTHORIZED", "请先登录", 401),
    "FORBIDDEN": ErrorSpec("FORBIDDEN", "没有权限访问该资源", 403),
    "NOT_FOUND": ErrorSpec("NOT_FOUND", "资源不存在", 404),
    "CONFLICT": ErrorSpec("CONFLICT", "资源状态冲突", 409),
    "INTERNAL_SERVER_ERROR": ErrorSpec("INTERNAL_SERVER_ERROR", "服务器内部错误，请稍后重试", 500),
    "DATABASE_UNAVAILABLE": ErrorSpec("DATABASE_UNAVAILABLE", "数据库连接失败，请稍后重试", 503),
    "PROFILE_NOT_FOUND": ErrorSpec("PROFILE_NOT_FOUND", "学生画像未找到", 404),
    "PROFILE_UPDATE_EMPTY": ErrorSpec("PROFILE_UPDATE_EMPTY", "没有提供需要更新的字段", 400),
    "PROFILE_CHAT_FAILED": ErrorSpec("PROFILE_CHAT_FAILED", "画像对话失败，请稍后重试", 500),
    "PATH_NOT_FOUND": ErrorSpec("PATH_NOT_FOUND", "学习路径未找到，请先生成路径", 404),
    "PLANNER_GENERATE_FAILED": ErrorSpec("PLANNER_GENERATE_FAILED", "学习路径生成失败，请稍后重试", 500),
    "PIPELINE_GENERATE_FAILED": ErrorSpec("PIPELINE_GENERATE_FAILED", "端到端生成失败，请稍后重试", 500),
    "RESOURCE_NOT_FOUND": ErrorSpec("RESOURCE_NOT_FOUND", "学习资源不存在", 404),
    "RESOURCE_GENERATE_FAILED": ErrorSpec("RESOURCE_GENERATE_FAILED", "资源生成失败，请稍后重试", 500),
    "TASK_NOT_FOUND": ErrorSpec("TASK_NOT_FOUND", "任务不存在", 404),
    "TUTOR_CHAT_FAILED": ErrorSpec("TUTOR_CHAT_FAILED", "智能辅导失败，请稍后重试", 500),
    "EVALUATE_FAILED": ErrorSpec("EVALUATE_FAILED", "学习评估失败，请稍后重试", 500),
}

STATUS_CODE_TO_ERROR_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_SERVER_ERROR",
    503: "DATABASE_UNAVAILABLE",
}


def get_error_spec(code: str) -> ErrorSpec:
    return ERROR_SPECS.get(code, ErrorSpec(code, "请求处理失败", 400))


def default_message_for(code: str) -> str:
    return get_error_spec(code).message


def default_status_for(code: str) -> int:
    return get_error_spec(code).status_code


def code_for_status(status_code: int) -> str:
    return STATUS_CODE_TO_ERROR_CODE.get(status_code, "HTTP_ERROR")
