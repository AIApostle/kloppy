"""API router composition."""

from fastapi import APIRouter

from .routes import assistant, auth, dashboard, integrations, settings

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(integrations.router)
api_router.include_router(settings.router)
api_router.include_router(assistant.router)
