"""Authenticated integration catalog and MCP connection routes."""

from fastapi import APIRouter, Header, HTTPException

from ..data import INTEGRATIONS
from ..schemas.integrations import Integration, MCPConnectionCreate, MCPDiscoveryRequest
from ..services.mcp_connections import (
    MCPConnectionError,
    delete_connection,
    discover_read_only_tools,
    list_connections,
    save_connection,
)
from ..services.user_settings import SettingsAuthenticationError, SettingsStoreError

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    return authorization[7:].strip()


def _raise(error: Exception) -> None:
    if isinstance(error, SettingsAuthenticationError):
        raise HTTPException(status_code=401, detail=str(error)) from error
    if isinstance(error, SettingsStoreError):
        raise HTTPException(status_code=503, detail=str(error)) from error
    if isinstance(error, MCPConnectionError):
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("", response_model=list[Integration])
def get_integrations(authorization: str | None = Header(default=None)) -> list[Integration]:
    try:
        connections = {item["provider"]: item for item in list_connections(_token(authorization))}
        catalog = [item for item in INTEGRATIONS if item["id"] not in {"qloo", "mcp"}]
        output: list[Integration] = []
        for item in catalog:
            connected = item["id"] in connections
            output.append(
                Integration(
                    **{
                        **item,
                        "status": "Connected" if connected else "Setup needed",
                        "connected": connected,
                        "description": (
                            f"Connected through an MCP server. Read-only tools: {', '.join(connections[item['id']]['allowed_tools'])}."
                            if connected
                            else item["description"]
                        ),
                        "server_url": connections[item["id"]]["server_url"] if connected else None,
                        "allowed_tools": connections[item["id"]]["allowed_tools"] if connected else [],
                    }
                )
            )
        for provider, connection in connections.items():
            if provider.startswith("custom-"):
                output.append(
                    Integration(
                        id=provider,
                        name=connection["display_name"],
                        kind="Resource",
                        category="Custom MCP",
                        description=f"Connected MCP server. Read-only tools: {', '.join(connection['allowed_tools'])}.",
                        status="Connected",
                        connected=True,
                        server_url=connection["server_url"],
                        allowed_tools=connection["allowed_tools"],
                    )
                )
        return output
    except (SettingsAuthenticationError, SettingsStoreError) as error:
        _raise(error)
        raise AssertionError("unreachable")


@router.post("/discover")
def discover_tools(payload: MCPDiscoveryRequest, authorization: str | None = Header(default=None)) -> dict[str, list[str]]:
    try:
        from ..services.user_settings import _user_id

        _user_id(_token(authorization))
        return {"read_only_tools": discover_read_only_tools(payload.server_url, payload.access_token)}
    except (SettingsAuthenticationError, SettingsStoreError, MCPConnectionError) as error:
        _raise(error)
        raise AssertionError("unreachable")


@router.post("/custom", response_model=Integration)
def add_custom_connection(
    payload: MCPConnectionCreate,
    authorization: str | None = Header(default=None),
) -> Integration:
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Give this custom connection a name.")
    try:
        provider = "custom-" + name.lower().replace(" ", "-")
        saved = save_connection(
            _token(authorization), provider, name, payload.server_url,
            payload.access_token, payload.allowed_tools,
        )
        return Integration(
            id=saved["provider"], name=saved["display_name"], kind="Resource",
            category="Custom MCP", description=f"Connected and verified read-only tools: {', '.join(saved['verified_tools'])}.",
            status="Connected", connected=True,
            server_url=saved["server_url"], allowed_tools=saved["allowed_tools"],
        )
    except (SettingsAuthenticationError, SettingsStoreError, MCPConnectionError) as error:
        _raise(error)
        raise AssertionError("unreachable")


@router.post("/{integration_id}/connect", response_model=Integration)
def connect_integration(
    integration_id: str,
    payload: MCPConnectionCreate,
    authorization: str | None = Header(default=None),
) -> Integration:
    item = next((entry for entry in INTEGRATIONS if entry["id"] == integration_id), None)
    if not item or integration_id in {"qloo", "mcp"}:
        raise HTTPException(status_code=404, detail="Choose a supported integration.")
    try:
        saved = save_connection(
            _token(authorization), integration_id, item["name"], payload.server_url,
            payload.access_token, payload.allowed_tools,
        )
        return Integration(
            **{
                **item,
                "status": "Connected",
                "connected": True,
                "description": f"Connected and verified read-only tools: {', '.join(saved['verified_tools'])}.",
                "server_url": saved["server_url"],
                "allowed_tools": saved["allowed_tools"],
            }
        )
    except (SettingsAuthenticationError, SettingsStoreError, MCPConnectionError) as error:
        _raise(error)
        raise AssertionError("unreachable")


@router.delete("/{integration_id}", status_code=204)
def disconnect_integration(integration_id: str, authorization: str | None = Header(default=None)) -> None:
    try:
        delete_connection(_token(authorization), integration_id)
    except (SettingsAuthenticationError, SettingsStoreError) as error:
        _raise(error)
