"""Unified SSE protocol — single source of truth for all streaming endpoints."""

import json, time
from typing import Optional, AsyncIterator
from contextvars import ContextVar

from fastapi.responses import StreamingResponse

_abort_flag: ContextVar[bool] = ContextVar("sse_abort_flag", default=False)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sse_event(event_type: str, **payload) -> str:
    data = {"type": event_type, "ts": _now_iso(), **payload}
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def sse_error(code: str, message: str, recoverable: bool = False) -> str:
    return sse_event("error", code=code, message=message, recoverable=recoverable)


def sse_done(**extra) -> str:
    return sse_event("done", **extra)


def sse_progress(phase: str, percent: int, message: str = "", **extra) -> str:
    return sse_event("progress", phase=phase, percent=percent, message=message, **extra)


class SseStream:
    @staticmethod
    def cancelled() -> bool:
        return _abort_flag.get()

    @staticmethod
    def abort() -> None:
        _abort_flag.set(True)


class StreamingSseResponse:
    def __new__(cls, generator: AsyncIterator[str], **kw) -> StreamingResponse:
        async def _safe():
            _abort_flag.set(False)
            try:
                async for event in generator:
                    if event is not None:
                        yield event
            finally:
                _abort_flag.set(False)

        return StreamingResponse(_safe(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        })
