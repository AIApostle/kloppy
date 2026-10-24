"""FastAPI application factory."""

import logging
import time
import uuid

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .observability import request_id_context
from .routes import assistant, dashboard, integrations, knowledge, qloo, settings as settings_routes
from .routes.auth import router as auth_router

logger = logging.getLogger("kloppy.api")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")
    allowed_origins = list(
        dict.fromkeys(
            origin.strip().rstrip("/")
            for origin in (
                settings.frontend_origin,
                *settings.frontend_origins.split(","),
            )
            if origin.strip()
        )
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_api_request(request: Request, call_next):
        request_id = uuid.uuid4().hex
        request_token = request_id_context.set(request_id)
        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as error:
            route = request.scope.get("route")
            route_path = getattr(route, "path", "unmatched")
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.error(
                "api_request_failed request_id=%s method=%s route=%s status_code=500 duration_ms=%.1f error_type=%s",
                request_id,
                request.method,
                route_path,
                duration_ms,
                type(error).__name__,
            )
            raise
        finally:
            request_id_context.reset(request_token)

        response.headers["X-Request-ID"] = request_id
        duration_ms = (time.perf_counter() - started_at) * 1000
        route = request.scope.get("route")
        route_path = getattr(route, "path", "unmatched")
        log_method = logger.info if response.status_code < 400 else (
            logger.warning if response.status_code < 500 else logger.error
        )
        log_method(
            "api_request_completed request_id=%s method=%s route=%s status_code=%s duration_ms=%.1f",
            request_id,
            request.method,
            route_path,
            response.status_code,
            duration_ms,
        )
        return response

    for router in (
        auth_router,
        dashboard.router,
        integrations.router,
        knowledge.router,
        qloo.router,
        settings_routes.router,
        assistant.router,
    ):
        app.include_router(router, prefix=settings.api_prefix)

    @app.get("/health", tags=["system"])
    @app.get("/ping", tags=["system"])
    @app.get("/keepalive", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
