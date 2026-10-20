"""Trusted read and draft tools exposed to Kloppy's Strands agent."""

import json
import logging
import re
from contextlib import ExitStack
from typing import Any
from urllib.parse import urlparse

from strands import ToolContext, tool
from strands.tools.mcp import MCPClient

from ..config import settings
from .mcp_connections import user_server_config
from .qloo import (
    ENTITY_TYPES,
    QlooConfigurationError,
    QlooProviderError,
    agent_grounding_options,
    run_capability,
    search_entities,
)
from ..schemas.qloo import QlooCapabilityRequest

logger = logging.getLogger(__name__)


@tool
def qloo_search_entities(query: str, entity_type: str = "urn:entity:brand") -> dict[str, Any]:
    """Find Qloo entities by name to ground an audience insight in real cultural entities."""
    if not settings.qloo_api_key:
        return {"available": False, "message": "Qloo is not configured."}
    try:
        return {
            "source": "Qloo API entity search",
            "entities": search_entities(
                query,
                next((name for name, urn in ENTITY_TYPES.items() if urn == entity_type), "brand"),
                take=8,
            ),
        }
    except (QlooProviderError, ValueError) as error:
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
    try:
        category = next(
            (name for name, urn in ENTITY_TYPES.items() if urn == result_type),
            "brand",
        )
        response = run_capability(
            QlooCapabilityRequest(
                capability="locality" if location_query.strip() else "recommendations",
                entity_ids=safe_ids,
                result_category=category,
                location=location_query[:160] if location_query.strip() else None,
                take=max(1, min(take, 20)),
            )
        )
        return {
            "source": response["source"],
            "interpretation": response["interpretation"],
            "entities": response["results"],
            **({"heatmap": response["heatmap"]} if "heatmap" in response else {}),
        }
    except (QlooConfigurationError, QlooProviderError, ValueError) as error:
        logger.warning("Qloo affinity request failed: %s", type(error).__name__)
        return {"source": "Qloo API cultural affinity insights", "error": "Qloo insights are temporarily unavailable."}


@tool
def qloo_agent_grounding(query: str, entity_category: str = "brand", take: int = 8) -> dict[str, Any]:
    """Return a short, Qloo-ranked list of factual cultural options for campaign research."""
    if not settings.qloo_api_key:
        return {"available": False, "message": "Qloo is not configured."}
    try:
        return agent_grounding_options(query, entity_category, take)
    except (QlooConfigurationError, QlooProviderError, ValueError) as error:
        logger.warning("Qloo agent grounding failed: %s", type(error).__name__)
        return {"source": "Qloo API", "error": "Qloo grounding is temporarily unavailable."}


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


def _load_mcp_config(access_token: str | None = None) -> dict[str, Any]:
    raw: Any = {}
    if settings.mcp_servers_json:
        try:
            raw = json.loads(settings.mcp_servers_json)
        except json.JSONDecodeError as error:
            logger.error("MCP_SERVERS_JSON is invalid JSON at character %s", error.pos)
    servers = raw.get("mcpServers", raw) if isinstance(raw, dict) else {}
    if not isinstance(servers, dict):
        logger.error("MCP_SERVERS_JSON must contain an mcpServers object")
        servers = {}
    if access_token:
        servers = {**servers, **user_server_config(access_token).get("mcpServers", {})}
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


def connected_mcp_clients(access_token: str | None = None) -> list[MCPClient]:
    """Create clients only for explicitly configured, allowlisted MCP tools."""
    config = _load_mcp_config(access_token)
    if not config["mcpServers"]:
        return []
    try:
        return MCPClient.load_servers(config, continue_on_error=True, prefix_with_server_name=True)
    except (ValueError, TypeError) as error:
        logger.error("MCP server configuration could not be loaded: %s", type(error).__name__)
        return []


def agent_tool_session(access_token: str | None = None) -> tuple[ExitStack, list[Any]]:
    """Open configured read-only MCP tools and Qloo for an agent turn."""
    stack = ExitStack()
    tools: list[Any] = [draft_document]
    if settings.qloo_api_key:
        tools.extend([qloo_search_entities, qloo_cultural_affinities, qloo_agent_grounding])
    clients = connected_mcp_clients(access_token)
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
