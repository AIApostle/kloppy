"""Shared API schemas."""

from pydantic import BaseModel, EmailStr, Field


class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = Field(default=None, min_length=2, max_length=80)


class SessionResponse(BaseModel):
    token: str | None = None
    refresh_token: str | None = None
    expires_at: int | None = None
    authenticated: bool
    message: str | None = None
    user: dict[str, str | bool | None]


class Integration(BaseModel):
    id: str
    name: str
    kind: str
    category: str
    description: str
    status: str
    connected: bool


class IntegrationUpdate(BaseModel):
    connected: bool


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    workspace: str = Field(min_length=2, max_length=80)
    digest_enabled: bool


class DashboardResponse(BaseModel):
    campaign: dict
    segments: list[dict]
    integration_count: int
