"""Trusted read and draft tools exposed to Kloppy's Strands agent."""

import json
import logging
import re
from base64 import b64encode
from contextlib import ExitStack
from io import BytesIO
from typing import Any
from urllib.parse import urlparse

import httpx
from docx import Document
from docx.document import Document as DocxDocument
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
CAMPAIGN_SECTIONS = (
    ("overview", "Overview"),
    ("audience", "Audience"),
    ("strategy", "Strategy"),
    ("launch", "Launch & Learn"),
)


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


def _add_docx_body(document: DocxDocument, content: str) -> None:
    for line in content.splitlines():
        text = line.strip()
        if not text:
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", text)
        if heading:
            document.add_heading(heading.group(2).strip(), level=min(len(heading.group(1)), 3))
            continue
        bullet = re.match(r"^(?:[-*+])\s+(.+)$", text)
        if bullet:
            document.add_paragraph(bullet.group(1), style="List Bullet")
            continue
        numbered = re.match(r"^\d+[.)]\s+(.+)$", text)
        if numbered:
            document.add_paragraph(numbered.group(1), style="List Number")
            continue
        document.add_paragraph(text)


def _build_docx_artifact(title: str, sections: dict[str, str]) -> dict[str, Any]:
    safe_title = " ".join(title.split())[:140] or "Kloppy draft"
    filename = re.sub(r"[^a-z0-9]+", "-", safe_title.lower()).strip("-")[:90] or "kloppy-draft"
    normalized_sections = {
        key: str(sections.get(key) or "").strip()[:12000]
        for key, _ in CAMPAIGN_SECTIONS
    }
    document = Document()
    document.add_heading(safe_title, level=0)
    for key, heading in CAMPAIGN_SECTIONS:
        document.add_heading(heading, level=1)
        _add_docx_body(document, normalized_sections[key] or "Not developed in this draft.")
    output = BytesIO()
    document.save(output)
    content = "\n\n".join(
        f"## {heading}\n\n{normalized_sections[key] or 'Not developed in this draft.'}"
        for key, heading in CAMPAIGN_SECTIONS
    )
    return {
        "title": safe_title,
        "content": content,
        "format": "docx",
        "filename": f"{filename}.docx",
        "docx_base64": b64encode(output.getvalue()).decode("ascii"),
        "sections": normalized_sections,
    }


@tool(context=True)
def draft_document(
    title: str,
    overview: str,
    audience: str,
    strategy: str,
    launch: str,
    tool_context: ToolContext,
) -> dict[str, str]:
    """Create a reviewable Word document containing Overview, Audience, Strategy, and Launch & Learn."""
    artifact = _build_docx_artifact(
        title,
        {
            "overview": overview,
            "audience": audience,
            "strategy": strategy,
            "launch": launch,
        },
    )
    normalized_sections = artifact["sections"]
    state = tool_context.invocation_state
    state.setdefault("artifacts", []).append(artifact)
    state.setdefault("campaign_sections", {}).update(normalized_sections)
    return {"status": "drafted", "title": artifact["title"], "format": "Word document"}


def _run_web_search(query: str) -> dict[str, Any]:
    safe_query = " ".join(query.split())[:500]
    if not safe_query:
        return {"status": "error", "message": "Enter a search query."}
    if not settings.tavily_api_key:
        return {"status": "unavailable", "message": "Web search is not configured."}
    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": safe_query,
                "search_depth": "basic",
                "max_results": 6,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        logger.warning("Web search request failed: %s", type(error).__name__)
        return {"status": "error", "message": "Web search is temporarily unavailable."}
    if not isinstance(payload, dict):
        logger.warning("Web search returned an invalid response shape")
        return {"status": "error", "message": "Web search returned an invalid response."}
    results = payload.get("results", [])
    if not isinstance(results, list):
        logger.warning("Web search returned an invalid results shape")
        return {"status": "error", "message": "Web search returned an invalid response."}
    sources = [
        {
            "title": str(item.get("title") or "Untitled source")[:300],
            "url": str(item.get("url") or "")[:2000],
            "snippet": str(item.get("content") or "")[:2500],
            "published_date": str(item.get("published_date") or "")[:80],
        }
        for item in results[:6]
        if isinstance(item, dict) and isinstance(item.get("url"), str)
    ]
    return {"status": "ok", "query": safe_query, "sources": sources}


@tool
def web_search(query: str) -> dict[str, Any]:
    """Search the public web for current, source-backed information relevant to a marketing request."""
    return _run_web_search(query)


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
    """Open configured research and read-only tools for an agent turn."""
    stack = ExitStack()
    tools: list[Any] = [draft_document]
    if settings.tavily_api_key:
        tools.append(web_search)
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
