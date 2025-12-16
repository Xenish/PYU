import time
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.observability.logging import generate_request_id, set_context, clear_context, get_logger
from app.observability import metrics


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        req_id = generate_request_id()
        set_context(request_id=req_id, component="api")
        request.state.request_id = req_id
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:  # noqa: BLE001
            response = Response(status_code=500)
            raise
        finally:
            duration = time.perf_counter() - start
            path_template = request.scope.get("path", request.url.path)
            metrics.api_requests_total.labels(
                path=path_template, method=request.method, status=getattr(response, "status_code", 500)
            ).inc()
            metrics.api_request_duration_seconds.labels(
                path=path_template, method=request.method
            ).observe(duration)
            clear_context()
        response.headers["X-Request-ID"] = req_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        logger = get_logger("masper.api", component="api")
        logger.info("request.start", extra={"path": request.url.path, "method": request.method})
        response = await call_next(request)
        logger.info(
            "request.end",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status": response.status_code,
            },
        )
        return response
