"""Pydantic contracts grouped by API domain."""

from .assistant import ChatRequest, ChatResponse
from .auth import AuthRequest, SessionResponse
from .dashboard import DashboardResponse
from .integrations import Integration, IntegrationUpdate
from .settings import ProfileUpdate

__all__ = [
    "AuthRequest",
    "ChatRequest",
    "ChatResponse",
    "DashboardResponse",
    "Integration",
    "IntegrationUpdate",
    "ProfileUpdate",
    "SessionResponse",
]
