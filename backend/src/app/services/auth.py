"""Supabase Auth service.

This module is the only application boundary that calls Supabase Auth.
"""

from dataclasses import dataclass
from typing import Any

from supabase import Client, create_client
from supabase_auth.errors import AuthApiError

from ..config import settings
from ..observability import log_external_call


class AuthConfigurationError(RuntimeError):
    """Raised when the server cannot safely initialize Supabase Auth."""


class AuthProviderError(RuntimeError):
    """Raised for an upstream Supabase Auth failure."""


@dataclass(frozen=True)
class AuthSession:
    """Safe session fields returned to the API layer."""

    access_token: str | None
    refresh_token: str | None
    expires_at: int | None
    user_id: str
    email: str | None
    name: str
    email_confirmed: bool


class SupabaseAuthService:
    """Small, typed boundary around the Supabase Python Auth client."""

    def __init__(self, client: Client) -> None:
        self._client = client

    @classmethod
    def from_settings(cls) -> "SupabaseAuthService":
        if not settings.supabase_url or not settings.supabase_publishable_key:
            raise AuthConfigurationError(
                "Supabase Auth is not configured. Set SUPABASE_PROJECT_URL and "
                "SUPABASE_ANON_KEY."
            )
        try:
            client = create_client(settings.supabase_url, settings.supabase_publishable_key)
        except Exception as error:
            raise AuthConfigurationError("Supabase Auth could not be initialized.") from error
        return cls(client)

    def signup(self, email: str, password: str, name: str | None) -> AuthSession:
        try:
            with log_external_call("supabase", "auth.sign_up"):
                response = self._client.auth.sign_up(
                    {
                        "email": email,
                        "password": password,
                        "options": {"data": {"name": name}} if name else {},
                    }
                )
        except AuthApiError as error:
            raise AuthProviderError("Unable to create the account.") from error
        return self._session_from_response(response, fallback_email=email, fallback_name=name)

    def login(self, email: str, password: str) -> AuthSession:
        try:
            with log_external_call("supabase", "auth.sign_in_with_password"):
                response = self._client.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
        except AuthApiError as error:
            raise AuthProviderError("Invalid email or password.") from error
        session = self._session_from_response(response, fallback_email=email, fallback_name=None)
        if session.access_token is None:
            raise AuthProviderError("Invalid email or password.")
        return session

    @staticmethod
    def _session_from_response(
        response: Any, fallback_email: str, fallback_name: str | None
    ) -> AuthSession:
        user = response.user
        metadata = user.user_metadata or {}
        name = metadata.get("name") or fallback_name or fallback_email.split("@", 1)[0]
        confirmed = bool(user.email_confirmed_at or user.confirmed_at)
        session = response.session
        return AuthSession(
            access_token=session.access_token if session else None,
            refresh_token=session.refresh_token if session else None,
            expires_at=session.expires_at if session else None,
            user_id=user.id,
            email=user.email,
            name=str(name),
            email_confirmed=confirmed,
        )
