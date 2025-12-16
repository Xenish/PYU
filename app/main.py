from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.services.llm_policy import LLMQuotaExceeded, LLMJobBudgetExceeded
from app.observability.logging import init_logging
from app.observability.middleware import RequestContextMiddleware, RequestLoggingMiddleware


def create_app() -> FastAPI:
    init_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(api_router)

    @app.exception_handler(LLMQuotaExceeded)
    async def handle_quota_exceeded(request, exc):  # type: ignore[override]
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    @app.exception_handler(LLMJobBudgetExceeded)
    async def handle_budget_exceeded(request, exc):  # type: ignore[override]
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    return app


app = create_app()
