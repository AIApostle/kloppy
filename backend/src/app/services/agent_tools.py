"""Trusted read and draft tools exposed to Kloppy's Strands agent."""

import json
import logging
import re
from contextlib import ExitStack
from typing import Any
from urllib.parse import urlparse

import httpx
from strands import ToolContext, tool
from strands.tools.mcp import MCPClient

from ..config import settings

logger = logging.getLogger(__name__)


@tool
def qloo_search_entities(query: str, entity_type: str = "urn:entity:brand") -> dict[str, Any]:
    """Find Qloo entities by name to ground an audience insight in real cultural entities."""
    if not settings.qloo_api_key:
        return {"available": False, "message": "Qloo is not configured."}
    try:
        response = httpx.get(
            f"{settings.qloo_base_url.rstrip('/')}/search",
            params={"query": query[:160], "types": entity_type, "take": 8},
            headers={"X-Api-Key": settings.qloo_api_key, "Accept": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", {})
        entities = results.get("entities", []) if isinstance(results, dict) else []
        return {
            "source": "Qloo API entity search",
            "entities": [
                {
                    "name": item.get("name"),
                    "entity_id": item.get("entity_id") or item.get("id"),
                    "type": item.get("type"),
                    "short_description": item.get("short_description"),
                }
                for item in entities[:8]
                if isinstance(item, dict)
            ],
        }
    except (httpx.HTTPError, ValueError) as error:
        logger.warning("Qloo entity search failed: %s", type(error).__name__)
        return {"source": "Qloo API entity search", "error": "Qloo search is temporarily unavailable."}


@tool
def qloo_cultural_affinities(
    entity_ids: list[str],
    result_type: str = "urn:entity:brand",
    location_query: str = "",
    take: int = 10,
) -> dict[str, Any]:
    """Get Qloo cultural affinity recommendations from selected entities and an optional location."""
    if not settings.qloo_api_key:
        return {"available": False, "message": "Qloo is not configured."}
    safe_ids = [value[:160] for value in entity_ids[:8] if isinstance(value, str) and value.strip()]
    if not safe_ids:
        return {"error": "Provide one or more Qloo entity IDs from entity search."}
    params: dict[str, str | int] = {
        "filter.type": result_type,
        "signal.interests.entities": ",".join(safe_ids),
        "take": max(1, min(take, 20)),
    }
    if location_query.strip():
        params["signal.location.query"] = location_query.strip()[:120]
    try:
        response = httpx.get(
            f"{settings.qloo_base_url.rstrip('/')}/v2/insights",
            params=params,
            headers={"X-Api-Key": settings.qloo_api_key, "Accept": "application/json"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", {})
        entities = results.get("entities", []) if isinstance(results, dict) else []
        return {
            "source": "Qloo API cultural affinity insights",
            "interpretation": "Directional cultural affinity only; not proof of purchase intent or an individual's identity.",
            "entities": [
                {
                    "name": item.get("name"),
                    "entity_id": item.get("entity_id") or item.get("id"),
                    "type": item.get("type"),
                    "affinity": item.get("affinity") or item.get("score"),
                    "tags": item.get("tags", [])[:8] if isinstance(item.get("tags"), list) else [],
                }
                for item in entities[:20]
                if isinstance(item, dict)
            ],
        }
    except (httpx.HTTPError, ValueError) as error:
        logger.warning("Qloo affinity request failed: %s", type(error).__name__)
        return {"source": "Qloo API cultural affinity insights", "error": "Qloo insights are temporarily unavailable."}


@tool(context=True)
def draft_document(
    title: str,
    content: str,
    tool_context: ToolContext,
) -> dict[str, str]:
    """Create a reviewable Markdown document draft in the Kloppy conversation."""
    safe_title = " ".join(title.split())[:140] or "Kloppy draft"
    safe_content = content.strip()[:50000]
    filename = re.sub(r"[^a-z0-9]+", "-", safe_title.lower()).strip("-")[:90] or "kloppy-draft"
    artifact = {
        "title": safe_title,
        "content": safe_content,
        "format": "markdown",
        "filename": f"{filename}.md",
    }
    state = tool_context.invocation_state
    state.setdefault("artifacts", []).append(artifact)
    return {"status": "drafted", "title": safe_title, "format": "Markdown"}


def _load_mcp_config() -> dict[str, Any]:
    if not settings.mcp_servers_json:
        return {"mcpServers": {}}
    try:
        raw = json.loads(settings.mcp_servers_json)
    except json.JSONDecodeError as error:
        logger.error("MCP_SERVERS_JSON is invalid JSON at character %s", error.pos)
        return {"mcpServers": {}}
    servers = raw.get("mcpServers", raw) if isinstance(raw, dict) else {}
    if not isinstance(servers, dict):
        logger.error("MCP_SERVERS_JSON must contain an mcpServers object")
        return {"mcpServers": {}}
    safe_servers: dict[str, Any] = {}
    for name, original in servers.items():
        if not isinstance(original, dict):
            continue
        server = dict(original)
        server_url = server.get("url")
        parsed_url = urlparse(server_url) if isinstance(server_url, str) else None
        local_http = bool(parsed_url and parsed_url.scheme == "http" and parsed_url.hostname in {"localhost", "127.0.0.1", "::1"})
        if "command" in server or not parsed_url or (parsed_url.scheme != "https" and not local_http):
            logger.warning("MCP server %s skipped: configure a remote HTTPS or local loopback URL", name)
            continue
        allowed = server.pop("allowed_tools", [])
        if not isinstance(allowed, list) or not allowed:
            logger.info("MCP server %s skipped because allowed_tools is empty", name)
            continue
        prefix = re.sub(r"[^A-Za-z0-9_-]", "_", str(name))
        server["prefix"] = prefix
        server["tool_filters"] = {"allowed": [f"{prefix}_{item}" for item in allowed]}
        server["continue_on_error"] = True
        safe_servers[str(name)] = server
    return {"mcpServers": safe_servers}


def connected_mcp_clients() -> list[MCPClient]:
    """Create clients only for explicitly configured, allowlisted MCP tools."""
    config = _load_mcp_config()
    if not config["mcpServers"]:
        return []
    try:
        return MCPClient.load_servers(config, continue_on_error=True, prefix_with_server_name=True)
    except (ValueError, TypeError) as error:
        logger.error("MCP server configuration could not be loaded: %s", type(error).__name__)
        return []


def agent_tool_session() -> tuple[ExitStack, list[Any]]:
    """Open configured read-only MCP tools and Qloo for an agent turn."""
    stack = ExitStack()
    tools: list[Any] = [draft_document]
    if settings.qloo_api_key:
        tools.extend([qloo_search_entities, qloo_cultural_affinities])
    clients = connected_mcp_clients()
    for client in clients:
        try:
            stack.enter_context(client)
            for server_tool in client.list_tools_sync():
                annotations = getattr(server_tool.mcp_tool, "annotations", None)
                if annotations and getattr(
                    annotations,
                    "read_only_hint",
                    getattr(annotations, "readOnlyHint", False),
                ):
                    tools.append(server_tool)
        except Exception as error:  # Keep healthy providers available when one MCP is offline.
            logger.warning("MCP connection unavailable: %s", type(error).__name__)
    return stack, tools
