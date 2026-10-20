"""User-scoped brand knowledge stored through Supabase RLS."""

from typing import Any

import httpx
import logging

from ..config import settings
from .user_settings import SettingsAuthenticationError, SettingsStoreError, _headers, _user_id

logger = logging.getLogger(__name__)


def list_sources(access_token: str) -> list[dict[str, Any]]:
    user_id = _user_id(access_token)
    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/brand_sources",
            headers=_headers(access_token),
            params={
                "user_id": f"eq.{user_id}",
                "select": "id,title,content,source_type,file_name,created_at",
                "order": "created_at.desc",
                "limit": "100",
            },
            timeout=15,
        )
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list):
            raise SettingsStoreError("Supabase returned an invalid knowledge response.")
        return rows
    except httpx.HTTPStatusError as error:
        _raise_storage_error(error)
    except httpx.HTTPError as error:
        raise SettingsStoreError("Could not load saved brand sources.") from error


def create_source(access_token: str, source: dict[str, Any]) -> dict[str, Any]:
    user_id = _user_id(access_token)
    try:
        response = httpx.post(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/brand_sources",
            headers={**_headers(access_token), "Prefer": "return=representation"},
            params={"select": "id,title,content,source_type,file_name,created_at"},
            json={**source, "user_id": user_id},
            timeout=20,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            raise SettingsStoreError("Supabase did not return the saved source.")
        return rows[0]
    except httpx.HTTPStatusError as error:
        _raise_storage_error(error)
    except httpx.HTTPError as error:
        raise SettingsStoreError("Could not save this brand source.") from error


def delete_source(access_token: str, source_id: str) -> None:
    user_id = _user_id(access_token)
    try:
        response = httpx.delete(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/brand_sources",
            headers=_headers(access_token),
            params={"id": f"eq.{source_id}", "user_id": f"eq.{user_id}"},
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        _raise_storage_error(error)
    except httpx.HTTPError as error:
        raise SettingsStoreError("Could not remove this brand source.") from error


def context_sources(access_token: str) -> list[dict[str, Any]]:
    """Load brand context without taking down chat before the migration is applied."""
    try:
        return list_sources(access_token)
    except SettingsStoreError as error:
        logger.warning("Saved brand context is unavailable: %s", error)
        return []


def _raise_storage_error(error: httpx.HTTPStatusError) -> None:
    if error.response.status_code in {401, 403}:
        raise SettingsAuthenticationError("Authentication could not be verified.") from error
    if error.response.status_code == 404:
        try:
            details = error.response.json()
        except ValueError:
            details = {}
        if details.get("code") == "PGRST205":
            logger.error("Supabase brand_sources table is unavailable (PGRST205).")
            raise SettingsStoreError(
                "Saved brand sources are temporarily unavailable. Please try again later."
            ) from error
    raise SettingsStoreError("Supabase could not read or save this brand source.") from error
