"""Secure, user-scoped MCP connection storage and validation."""

import logging
import ipaddress
import re
import socket
from typing import Any
from urllib.parse import urlparse

import httpx
from cryptography.fernet import Fernet, InvalidToken
from strands.tools.mcp import MCPClient

from ..config import settings
from .user_settings import SettingsAuthenticationError, SettingsStoreError, _headers, _user_id

logger = logging.getLogger(__name__)
TABLE_URL = "/rest/v1/user_mcp_servers"


class MCPConnectionError(ValueError):
    """A provider endpoint or its exposed tools could not be safely connected."""


def list_connections(access_token: str) -> list[dict[str, Any]]:
    user_id = _user_id(access_token)
    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}{TABLE_URL}",
            headers=_headers(access_token),
            params={
                "user_id": f"eq.{user_id}",
                "select": "provider,display_name,server_url,allowed_tools,created_at,updated_at",
                "order": "display_name.asc",
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as error:
        _raise_store_error(error)
    except httpx.HTTPError as error:
        raise SettingsStoreError("Could not load connected MCP services.") from error


def save_connection(
    access_token: str,
    provider: str,
    display_name: str,
    server_url: str,
    bearer_token: str | None,
    allowed_tools: list[str],
) -> dict[str, Any]:
    user_id = _user_id(access_token)
    clean_provider = _slug(provider)
    clean_url = _validate_url(server_url)
    clean_tools = _validate_tool_names(allowed_tools)
    tested_tools = _test_connection(clean_provider, clean_url, bearer_token, clean_tools)
    cipher = _cipher()
    encrypted_token = cipher.encrypt(bearer_token.encode()).decode() if bearer_token else ""
    payload = {
        "user_id": user_id,
        "provider": clean_provider,
        "display_name": display_name.strip()[:100],
        "server_url": clean_url,
        "encrypted_token": encrypted_token,
        "allowed_tools": clean_tools,
    }
    try:
        response = httpx.post(
            f"{settings.supabase_url.rstrip('/')}{TABLE_URL}",
            headers={**_headers(access_token), "Prefer": "resolution=merge-duplicates,return=representation"},
            params={
                "on_conflict": "user_id,provider",
                "select": "provider,display_name,server_url,allowed_tools,created_at,updated_at",
            },
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            raise SettingsStoreError("Supabase did not return the saved MCP connection.")
        return {**rows[0], "verified_tools": tested_tools}
    except httpx.HTTPStatusError as error:
        _raise_store_error(error)
    except httpx.HTTPError as error:
        raise SettingsStoreError("Could not save this MCP connection.") from error


def discover_read_only_tools(server_url: str, bearer_token: str | None) -> list[str]:
    """Probe an MCP server and return only tools that explicitly advertise read-only behavior."""
    url = _validate_url(server_url)
    config: dict[str, Any] = {"url": url}
    if bearer_token:
        config["headers"] = {"Authorization": f"Bearer {bearer_token}"}
    try:
        client = MCPClient.load_servers({"mcpServers": {"kloppy_probe": config}})[0]
        with client:
            tools = client.list_tools_sync()
    except Exception as error:
        logger.warning("MCP discovery failed: %s", type(error).__name__)
        raise MCPConnectionError("Kloppy could not reach this MCP server. Check its URL and authentication.") from error
    readable: list[str] = []
    for item in tools:
        tool_name = str(getattr(item, "tool_name", ""))
        annotations = getattr(getattr(item, "mcp_tool", None), "annotations", None)
        if annotations and getattr(annotations, "read_only_hint", getattr(annotations, "readOnlyHint", False)):
            readable.append(tool_name.removeprefix("kloppy_probe_"))
    return sorted(set(readable))


def delete_connection(access_token: str, provider: str) -> None:
    user_id = _user_id(access_token)
    try:
        response = httpx.delete(
            f"{settings.supabase_url.rstrip('/')}{TABLE_URL}",
            headers=_headers(access_token),
            params={"provider": f"eq.{_slug(provider)}", "user_id": f"eq.{user_id}"},
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        _raise_store_error(error)
    except httpx.HTTPError as error:
        raise SettingsStoreError("Could not disconnect this MCP service.") from error


def user_server_config(access_token: str) -> dict[str, Any]:
    """Return decrypted MCP config for this verified user's agent turn."""
    if not access_token:
        return {"mcpServers": {}}
    user_id = _user_id(access_token)
    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}{TABLE_URL}",
            headers=_headers(access_token),
            params={
                "user_id": f"eq.{user_id}",
                "select": "provider,server_url,encrypted_token,allowed_tools",
            },
            timeout=15,
        )
        response.raise_for_status()
        rows = response.json()
    except httpx.HTTPStatusError as error:
        # An unapplied optional connector migration must not take down chat.
        if error.response.status_code == 404:
            logger.warning("MCP connection storage is unavailable; apply the integration migration")
            return {"mcpServers": {}}
        _raise_store_error(error)
    except httpx.HTTPError as error:
        logger.warning("MCP connection list unavailable: %s", type(error).__name__)
        return {"mcpServers": {}}
    servers: dict[str, Any] = {}
    try:
        cipher = _cipher()
    except MCPConnectionError:
        if rows:
            logger.error("MCP encryption key is missing; user connectors are disabled")
        return {"mcpServers": {}}
    for row in rows:
        try:
            provider = _slug(row["provider"])
            token = row.get("encrypted_token")
            auth_token = cipher.decrypt(token.encode()).decode() if token else ""
            config = {
                "url": _validate_url(row["server_url"]),
                "allowed_tools": _validate_tool_names(row["allowed_tools"]),
            }
            if auth_token:
                config["headers"] = {"Authorization": f"Bearer {auth_token}"}
            servers[provider] = config
        except (KeyError, TypeError, ValueError, InvalidToken):
            logger.error("Skipping invalid stored MCP connection")
    return {"mcpServers": servers}


def _test_connection(provider: str, url: str, token: str | None, allowed_tools: list[str]) -> list[str]:
    server: dict[str, Any] = {"url": url, "allowed_tools": allowed_tools}
    if token:
        server["headers"] = {"Authorization": f"Bearer {token}"}
    try:
        client = MCPClient.load_servers(
            {"mcpServers": {provider: server}},
            continue_on_error=False,
            prefix_with_server_name=True,
        )[0]
        with client:
            available = client.list_tools_sync()
    except Exception as error:
        logger.warning("MCP endpoint verification failed: %s", type(error).__name__)
        raise MCPConnectionError("Kloppy could not reach this MCP server with the supplied connection details.") from error

    verified: list[str] = []
    for requested in allowed_tools:
        matched = next(
            (item for item in available if _tool_matches(item, provider, requested)),
            None,
        )
        if matched is None:
            raise MCPConnectionError(f"The MCP server does not expose the selected tool '{requested}'.")
        annotations = getattr(getattr(matched, "mcp_tool", None), "annotations", None)
        read_only = bool(
            annotations
            and getattr(annotations, "read_only_hint", getattr(annotations, "readOnlyHint", False))
        )
        if not read_only:
            raise MCPConnectionError(f"The selected tool '{requested}' is not marked read-only; Kloppy will not enable it.")
        verified.append(requested)
    return verified


def _tool_matches(item: Any, provider: str, requested: str) -> bool:
    exposed = str(getattr(item, "tool_name", ""))
    return exposed in {requested, f"{provider}_{requested}"} or exposed.endswith(f"_{requested}")


def _validate_url(value: str) -> str:
    parsed = urlparse(value.strip())
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise MCPConnectionError("Enter a valid MCP server URL without embedded credentials, query parameters, or a fragment.")
    if parsed.scheme != "https" and not (settings.environment == "development" and parsed.scheme == "http" and local):
        raise MCPConnectionError("MCP servers must use HTTPS. Local HTTP is allowed only in development.")
    if settings.environment != "development" or not local:
        try:
            addresses = {ipaddress.ip_address(result[4][0]) for result in socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)}
        except (OSError, ValueError) as error:
            raise MCPConnectionError("Kloppy could not resolve this MCP server host.") from error
        if not addresses or any(not address.is_global for address in addresses):
            raise MCPConnectionError("MCP servers must resolve to public IP addresses.")
    return value.strip().rstrip("/")


def _validate_tool_names(values: list[str]) -> list[str]:
    if not isinstance(values, list) or not values or len(values) > 40:
        raise MCPConnectionError("Select at least one read-only tool exposed by this MCP server.")
    output = list(dict.fromkeys(item.strip() for item in values if isinstance(item, str)))
    if not output or any(not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", item) for item in output):
        raise MCPConnectionError("One or more MCP tool names are invalid.")
    return output


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-")[:64]
    if not slug:
        raise MCPConnectionError("A valid provider name is required.")
    return slug


def _cipher() -> Fernet:
    key = settings.integration_encryption_key
    if not key:
        raise MCPConnectionError("Set INTEGRATION_ENCRYPTION_KEY in the backend environment before connecting external services.")
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as error:
        raise MCPConnectionError("INTEGRATION_ENCRYPTION_KEY must be a valid Fernet key.") from error


def _raise_store_error(error: httpx.HTTPStatusError) -> None:
    if error.response.status_code in {401, 403}:
        raise SettingsAuthenticationError("Authentication could not be verified.") from error
    if error.response.status_code == 404:
        try:
            detail = error.response.json()
        except ValueError:
            detail = {}
        if detail.get("code") == "PGRST205":
            logger.error("Supabase user_mcp_servers table is unavailable (PGRST205).")
            raise SettingsStoreError(
                "Connected services are temporarily unavailable. Please try again later."
            ) from error
    raise SettingsStoreError("Supabase could not read or save this MCP connection.") from error
