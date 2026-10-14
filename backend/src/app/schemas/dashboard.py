"""Dashboard response contracts."""

from pydantic import BaseModel


class DashboardResponse(BaseModel):
    campaign: dict
    segments: list[dict]
    integration_count: int
