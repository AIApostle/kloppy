"""Agent conversation contracts."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    mode: str = Field(default="plan", pattern="^(research|plan|execute)$")
    model: str = Field(default="kloppy-balanced", max_length=80)
    permission: str = Field(default="ask", pattern="^(ask|auto)$")
    attachments: list[str] = Field(default_factory=list, max_length=12)
    context_items: list[str] = Field(default_factory=list, max_length=12)


class ChatResponse(BaseModel):
    reply: str
    next_actions: list[str]
    artifact: dict[str, str] | None = None
