"""Agent conversation contracts."""

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)

    @field_validator("content")
    @classmethod
    def validate_content_length(cls, content: str, info: ValidationInfo) -> str:
        max_length = 2000 if info.data.get("role") == "user" else 12000
        if len(content) > max_length:
            raise ValueError(f"Conversation {info.data.get('role')} content is too long.")
        return content


class CampaignSectionContext(BaseModel):
    overview: str | None = Field(default=None, max_length=12000)
    audience: str | None = Field(default=None, max_length=12000)
    strategy: str | None = Field(default=None, max_length=12000)
    launch: str | None = Field(default=None, max_length=12000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    campaign_id: str | None = Field(default=None, max_length=100)
    campaign_name: str | None = Field(default=None, max_length=200)
    campaign_sections: CampaignSectionContext = Field(default_factory=CampaignSectionContext)
    attachments: list[str] = Field(default_factory=list, max_length=12)
    context_items: list[str] = Field(default_factory=list, max_length=12)
    conversation_history: list[ConversationTurn] = Field(default_factory=list, max_length=16)


class ChatResponse(BaseModel):
    reply: str
    next_actions: list[str]
    artifact: dict[str, Any] | None = None
    visual_results: list[dict[str, str]] = Field(default_factory=list)
    activities: list[dict[str, str]] = Field(default_factory=list)
