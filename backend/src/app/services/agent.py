"""Strands-backed agent orchestration boundary."""

from typing import Protocol

from strands import Agent

from ..schemas.assistant import ChatRequest, ChatResponse
from ..config import settings


class AgentConfigurationError(RuntimeError):
    """Raised when agent provider configuration is incomplete."""


class AgentProviderError(RuntimeError):
    """Raised when the configured agent provider cannot complete a turn."""


class AgentService(Protocol):
    def respond(self, payload: ChatRequest) -> ChatResponse:
        """Run one agent turn and return the structured API response."""


class StrandsAgentService:
    """Builds a request-scoped Strands agent from the selected model."""

    def respond(self, payload: ChatRequest) -> ChatResponse:
        if not settings.strands_model_id and payload.model == "kloppy-balanced":
            raise AgentConfigurationError("Agent model configuration is missing.")

        prompt = self._prompt_for(payload)
        try:
            agent = Agent(
                model=(
                    payload.model
                    if payload.model != "kloppy-balanced"
                    else settings.strands_model_id
                ),
                name="kloppy",
                description="Kloppy marketing operating system agent",
            )
            result = agent(prompt)
        except Exception as error:
            raise AgentProviderError("The agent could not complete this request.") from error

        reply = self._extract_text(result)
        if not reply:
            raise AgentProviderError("The agent returned an empty response.")
        return ChatResponse(reply=reply, next_actions=[], artifact=None)

    @staticmethod
    def _prompt_for(payload: ChatRequest) -> str:
        return (
            f"Mode: {payload.mode}\n"
            f"Permission policy: {payload.permission}\n"
            f"Attachments: {', '.join(payload.attachments) or 'none'}\n"
            f"Explicit context: {', '.join(payload.context_items) or 'none'}\n\n"
            f"User request:\n{payload.message}"
        )

    @staticmethod
    def _extract_text(result: object) -> str:
        message = getattr(result, "message", {})
        content = message.get("content", []) if isinstance(message, dict) else []
        return "\n".join(
            block["text"]
            for block in content
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        ).strip()
