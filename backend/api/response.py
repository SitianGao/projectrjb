"""Shared API response helpers.

Phase-1 compatibility keeps object fields at the top level while the formal
contract moves clients to success/data/message.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


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


def error_payload(code: str, message: str) -> dict:
    return {
        "success": False,
        "error": True,
        "code": code,
        "message": message,
    }


def fail(code: str, message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_payload(code, message))


class ApiError(Exception):
    """Application error that maps directly to the unified error contract."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def code_for_status(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
    }
    return mapping.get(status_code, "HTTP_ERROR")


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
