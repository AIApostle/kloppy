"""Third-party connection routes."""

import json
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException

from ..data import INTEGRATIONS
from ..config import settings
from ..schemas.integrations import Integration, IntegrationUpdate

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=list[Integration])
def list_integrations() -> list[Integration]:
    items = [dict(item) for item in INTEGRATIONS]
    configured_mcp: list[str] = []
    if settings.mcp_servers_json:
        try:
            raw = json.loads(settings.mcp_servers_json)
            servers = raw.get("mcpServers", raw) if isinstance(raw, dict) else {}
            configured_mcp = [
                str(name)
                for name, server in servers.items()
                for parsed in [urlparse(server.get("url", "")) if isinstance(server, dict) else None]
                if isinstance(server, dict)
                and server.get("allowed_tools")
                and parsed
                and (parsed.scheme == "https" or (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}))
            ]
        except (json.JSONDecodeError, AttributeError):
            configured_mcp = []
    for item in items:
        configured_names = {name.lower().replace("-", "_").replace(" ", "_") for name in configured_mcp}
        provider_aliases = {
            "meta_ads": "meta-ads",
            "google_ads": "google-ads",
            "google_drive": "google-drive",
            "google_analytics": "ga4",
        }
        configured_provider = item["id"] in configured_mcp or item["id"] in {
            provider_aliases.get(name, name.replace("_", "-")) for name in configured_names
        }
        if item["id"] == "qloo" and (settings.qloo_api_key or "qloo" in configured_names):
            item.update(status="Configured", connected=True)
        elif item["id"] not in {"mcp", "qloo"} and configured_provider:
            item.update(status="Configured", connected=True)
        elif item["id"] == "mcp" and configured_mcp:
            item.update(
                status="Configured",
                connected=True,
                description=f"Allowlisted read-only tools from {', '.join(configured_mcp)}.",
            )
    return [Integration(**item) for item in items]


@router.patch("/{integration_id}", response_model=Integration)
def update_integration(integration_id: str, payload: IntegrationUpdate) -> Integration:
    raise HTTPException(
        status_code=409,
        detail="Connection state reflects backend credentials and MCP configuration; use the backend environment to configure providers.",
    )
