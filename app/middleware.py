from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Xóa context cũ để tránh rò rỉ giữa các request
        clear_contextvars()

        # 2. Lấy x-request-id từ headers hoặc sinh mới dạng req-<8-char-hex>
        correlation_id = request.headers.get("x-request-id")
        if not correlation_id:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        # 3. Gắn correlation_id vào structlog contextvars và request state
        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # 4. Trả correlation_id và thời gian xử lý về header
        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = f"{duration_ms:.2f}"

        return response
