"""API router composition."""

from fastapi import APIRouter

from .routes import assistant, dashboard, integrations, knowledge, qloo, settings
from .routes.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(dashboard.router)
api_router.include_router(integrations.router)
api_router.include_router(knowledge.router)
api_router.include_router(settings.router)
api_router.include_router(assistant.router)
api_router.include_router(qloo.router)
