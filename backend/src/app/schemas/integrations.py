"""Integration response and mutation contracts."""

from pydantic import BaseModel


class Integration(BaseModel):
    id: str
    name: str
    kind: str
    category: str
    description: str
    status: str
    connected: bool


class IntegrationUpdate(BaseModel):
    connected: bool
