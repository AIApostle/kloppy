"""Contracts for Qloo cultural-intelligence operations."""

from typing import Literal

from pydantic import BaseModel, Field

QlooEntityCategory = Literal[
    "place",
    "artist",
    "brand",
    "book",
    "movie",
    "destination",
    "person",
    "podcast",
    "tv_show",
]

QlooCapability = Literal[
    "enrichment",
    "taste",
    "recommendations",
    "locality",
    "grounding",
    "on_device",
]


class QlooCapabilityRequest(BaseModel):
    capability: QlooCapability
    query: str | None = Field(default=None, max_length=160)
    entity_category: QlooEntityCategory = "brand"
    result_category: QlooEntityCategory = "brand"
    interests: list[str] = Field(default_factory=list, max_length=8)
    entity_ids: list[str] = Field(default_factory=list, max_length=8)
    location: str | None = Field(default=None, max_length=160)
    goal: str | None = Field(default=None, max_length=500)
    campaign_name: str | None = Field(default=None, max_length=200)
    take: int = Field(default=10, ge=1, le=20)
