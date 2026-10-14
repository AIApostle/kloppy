"""Authentication request and response contracts."""

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
