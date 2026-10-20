"""Knowledge source API contracts."""

from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeSourceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=100_000)
    source_type: Literal["brand_text", "document"] = "brand_text"
    file_name: str | None = Field(default=None, max_length=255)


class KnowledgeSource(BaseModel):
    id: str
    title: str
    content: str
    source_type: Literal["brand_text", "document"]
    file_name: str | None = None
    created_at: str
