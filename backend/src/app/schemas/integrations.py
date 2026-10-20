"""Integration and MCP connection contracts."""

from pydantic import BaseModel, Field


class Integration(BaseModel):
    id: str
    name: str
    kind: str
    category: str
    description: str
    status: str
    connected: bool
    server_url: str | None = None
    allowed_tools: list[str] = Field(default_factory=list)


class MCPConnectionCreate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    server_url: str = Field(min_length=8, max_length=2048)
    access_token: str | None = Field(default=None, max_length=4096)
    allowed_tools: list[str] = Field(min_length=1, max_length=40)


class MCPDiscoveryRequest(BaseModel):
    server_url: str = Field(min_length=8, max_length=2048)
    access_token: str | None = Field(default=None, max_length=4096)
