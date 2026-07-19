"""Shared API response helpers.

Phase-1 compatibility keeps object fields at the top level while the formal
contract moves clients to success/data/message.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from api.error_codes import code_for_status, default_message_for, default_status_for
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def ok(data: Any = None, message: str = "ok") -> dict:
    """Return the unified success envelope with temporary top-level compat."""
    response = {
        "success": True,
        "data": data,
        "message": message,
    }
    if isinstance(data, dict):
        for key, value in data.items():
            if key not in response:
                response[key] = value
    return response


def error_payload(code: str, message: str | None = None) -> dict:
    return {
        "success": False,
        "error": True,
        "code": code,
        "message": message or default_message_for(code),
    }


def fail(
    code: str,
    message: str | None = None,
    status_code: int | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code or default_status_for(code),
        content=error_payload(code, message),
    )


def sse_error(code: str, message: str) -> str:
    """Format an SSE error event (delegates to core.sse)."""
    from core.sse import sse_error as _sse_error
    return _sse_error(code, message)


def sse_done() -> str:
    """Format the SSE done event (delegates to core.sse)."""
    from core.sse import sse_done as _sse_done
    return _sse_done()


class ApiError(Exception):
    """Application error that maps directly to the unified error contract."""

    def __init__(
        self,
        code: str,
        message: str | None = None,
        status_code: int | None = None,
    ):
        self.code = code
        self.message = message or default_message_for(code)
        self.status_code = status_code or default_status_for(code)
        super().__init__(self.message)


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return fail(exc.code, exc.message, exc.status_code)


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return fail(code_for_status(exc.status_code), detail, exc.status_code)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    first_error: Optional[dict] = exc.errors()[0] if exc.errors() else None
    message = first_error.get("msg", "参数校验失败") if first_error else "参数校验失败"
    return fail("VALIDATION_ERROR", message, 422)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error: %s %s", request.method, request.url.path)
    return fail("INTERNAL_SERVER_ERROR", "服务器内部错误，请稍后重试", 500)
