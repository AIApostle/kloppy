"""Authenticated Supabase storage for profile and approval preferences."""

from typing import Any

import httpx

from ..config import settings
from ..observability import log_external_call
from ..schemas.settings import ProfileUpdate, UserSettings


class SettingsStoreError(RuntimeError):
    """Supabase settings storage is unavailable or rejected a request."""


class SettingsAuthenticationError(SettingsStoreError):
    """The supplied Supabase access token is missing, expired, or invalid."""


def _headers(access_token: str) -> dict[str, str]:
    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise SettingsStoreError("Supabase settings storage is not configured.")
    return {
        "apikey": settings.supabase_publishable_key,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def _user_id(access_token: str) -> str:
    """Verify the bearer token with Supabase Auth; never trust a client user ID."""
    headers = _headers(access_token)
    try:
        with log_external_call("supabase", "auth.get_user") as call:
            response = httpx.get(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
                headers=headers,
                timeout=10,
            )
            call.status_code = response.status_code
            response.raise_for_status()
            user_id = response.json().get("id")
    except httpx.HTTPStatusError as error:
        if error.response.status_code in {401, 403}:
            raise SettingsAuthenticationError("Authentication could not be verified.") from error
        raise SettingsStoreError("Supabase Auth could not verify the session right now.") from error
    except (httpx.HTTPError, ValueError, AttributeError) as error:
        raise SettingsStoreError("Supabase Auth could not verify the session right now.") from error
    if not isinstance(user_id, str) or not user_id:
        raise SettingsAuthenticationError("Authentication could not be verified.")
    return user_id


def _request_settings(access_token: str, method: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    user_id = _user_id(access_token)
    headers = _headers(access_token)
    url = f"{settings.supabase_url.rstrip('/')}/rest/v1/user_settings"
    params = {"on_conflict": "user_id", "select": "name,workspace,digest_enabled,permission_policy"}
    request_headers = {**headers, "Prefer": "resolution=merge-duplicates,return=representation"}
    try:
        if method == "GET":
            with log_external_call("supabase", "user_settings.select") as call:
                response = httpx.get(
                    url,
                    headers=headers,
                    params={"user_id": f"eq.{user_id}", **{"select": params["select"]}},
                    timeout=10,
                )
                call.status_code = response.status_code
                response.raise_for_status()
                rows = response.json()
            if rows:
                return UserSettings.model_validate(rows[0]).model_dump()
            # Persist conservative defaults on first access, so execution always
            # has a server-side policy to check.
            return _request_settings(
                access_token,
                "UPSERT",
                {"user_id": user_id, **UserSettings().model_dump()},
            )
        with log_external_call("supabase", "user_settings.upsert") as call:
            response = httpx.post(
                url,
                headers=request_headers,
                params=params,
                json={**(body or {}), "user_id": user_id},
                timeout=10,
            )
            call.status_code = response.status_code
            response.raise_for_status()
            rows = response.json()
        if not rows:
            raise SettingsStoreError("Supabase did not return the saved settings.")
        return UserSettings.model_validate(rows[0]).model_dump()
    except (httpx.HTTPError, ValueError, KeyError, IndexError) as error:
        response = getattr(error, "response", None)
        if response is not None and response.status_code == 404:
            try:
                details = response.json()
            except ValueError:
                details = {}
            if details.get("code") == "PGRST205":
                raise SettingsStoreError(
                    "Supabase cannot find public.user_settings in its Data API schema cache. "
                    "Apply backend/db/003_user_settings.sql and refresh the Supabase schema cache."
                ) from error
        raise SettingsStoreError(
            "Could not read or save user settings. Confirm the user_settings SQL migration is applied."
        ) from error


def read_user_settings(access_token: str) -> dict[str, Any]:
    return _request_settings(access_token, "GET")


def save_user_settings(access_token: str, payload: ProfileUpdate) -> dict[str, Any]:
    return _request_settings(access_token, "UPSERT", payload.model_dump())
