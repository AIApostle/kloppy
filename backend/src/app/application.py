"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import assistant, dashboard, integrations, knowledge, settings as settings_routes
from .routes.auth import router as auth_router


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
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (
        auth_router,
        dashboard.router,
        integrations.router,
        knowledge.router,
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
