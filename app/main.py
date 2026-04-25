import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, reset_settings_cache
from app.core.exceptions import AppError
from app.core.redis_client import get_redis
from app.api.routes import auth, health, projects, reports, tasks, users, workspaces

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    s = get_settings()
    if s.environment != "test":
        try:
            get_redis().ping()
        except Exception:  # noqa: BLE001
            log.warning("redis unavailable at startup; continuing")
    yield
    reset_settings_cache()


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title=s.app_name,
        version="1.0.0",
        description="Multi-tenant project management and workflow REST API (Enterprise Task & Workflow Management).",
        lifespan=lifespan,
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:  # noqa: ARG001
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
        log.exception("unhandled: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Internal server error"},
        )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next) -> Any:  # type: ignore[no-untyped-def]
        req_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if s.environment in ("local", "test") else [s.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=s.api_prefix)
    app.include_router(auth.router, prefix=s.api_prefix)
    app.include_router(users.router, prefix=s.api_prefix)
    app.include_router(workspaces.router, prefix=s.api_prefix)
    app.include_router(projects.router, prefix=s.api_prefix)
    app.include_router(tasks.router, prefix=s.api_prefix)
    app.include_router(reports.router, prefix=s.api_prefix)

    return app


app = create_app()
