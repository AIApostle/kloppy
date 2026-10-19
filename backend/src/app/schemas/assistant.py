"""Agent conversation contracts."""

from typing import Literal

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    campaign_id: str | None = Field(default=None, max_length=100)
    campaign_name: str | None = Field(default=None, max_length=200)
    attachments: list[str] = Field(default_factory=list, max_length=12)
    context_items: list[str] = Field(default_factory=list, max_length=12)
    conversation_history: list[ConversationTurn] = Field(default_factory=list, max_length=16)


class ChatResponse(BaseModel):
    reply: str
    next_actions: list[str]
    artifact: dict[str, str] | None = None
    activities: list[dict[str, str]] = Field(default_factory=list)
