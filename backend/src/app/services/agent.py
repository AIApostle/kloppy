"""Strands-backed agent orchestration boundary."""

import json
import re
from typing import Protocol

from strands import Agent
from strands.models.openai import OpenAIModel

from ..schemas.assistant import ChatRequest, ChatResponse
from ..config import settings
from ..prompts import BASE_PROMPT, PROMPTS


class AgentConfigurationError(RuntimeError):
    """Raised when agent provider configuration is incomplete."""


class AgentProviderError(RuntimeError):
    """Raised when the configured agent provider cannot complete a turn."""


class AgentService(Protocol):
    def respond(self, payload: ChatRequest, user_settings: dict | None = None) -> ChatResponse:
        """Run one agent turn and return the structured API response."""


class StrandsAgentService:
    """Builds a request-scoped Strands agent from the selected model."""

    def respond(self, payload: ChatRequest, user_settings: dict | None = None) -> ChatResponse:
        if not settings.openrouter_api_key:
            raise AgentConfigurationError("OpenRouter is not configured.")

        if payload.mode == "execute" and user_settings is None:
            raise AgentProviderError("Saved user permissions could not be checked; execution is paused.")
        # Permission comes from the authenticated database row, never from a
        # browser-supplied chat payload.
        policy = str((user_settings or {}).get("permission_policy", "ask"))
        trusted_payload = payload.model_copy(update={"permission": policy})
        prompt = self._prompt_for(trusted_payload, user_settings or {})
        try:
            model_id = (
                settings.strands_model_id
                if payload.model == "kloppy-balanced"
                else payload.model
            )
            model = OpenAIModel(
                client_args={
                    "api_key": settings.openrouter_api_key,
                    "base_url": settings.openrouter_base_url,
                    "default_headers": {
                        **(
                            {"HTTP-Referer": settings.openrouter_http_referer}
                            if settings.openrouter_http_referer
                            else {}
                        ),
                        "X-Title": settings.openrouter_app_title,
                    },
                },
                model_id=model_id or "openrouter/free",
            )
            agent = Agent(
                model=model,
                name="kloppy",
                description="Kloppy marketing operating system agent",
                system_prompt=f"{BASE_PROMPT}\n\n{PROMPTS[payload.mode]}",
            )
            result = agent(prompt)
        except Exception as error:
            raise AgentProviderError("The agent could not complete this request.") from error

        reply = self._extract_text(result)
        if not reply:
            raise AgentProviderError("The agent returned an empty response.")
        return ChatResponse(reply=reply, next_actions=[], artifact=None)

    @staticmethod
    def _prompt_for(payload: ChatRequest, user_settings: dict) -> str:
        history = json.dumps(
            [turn.model_dump() for turn in payload.conversation_history],
            ensure_ascii=False,
        )
        return (
            f"ACTIVE_MODE: {payload.mode}\n"
            f"BUSINESS_PROFILE: workspace={user_settings.get('workspace') or 'not supplied'}; contact name={user_settings.get('name') or 'not supplied'}\n"
            "CURRENT_PROJECT: not supplied\n"
            "CAMPAIGN_CONTEXT: not supplied\n"
            "AVAILABLE_TOOLS: no external action tools supplied for this turn\n"
            "CONNECTED_RESOURCES: none supplied for this turn\n"
            f"Server-verified saved user settings: {user_settings}\n"
            f"USER_PERMISSIONS / APPROVAL_POLICY: saved preference is {payload.permission}; external publishing/spend still requires explicit approval\n"
            f"Attachments: {', '.join(payload.attachments) or 'none'}\n"
            f"Explicit context: {', '.join(payload.context_items) or 'none'}\n\n"
            f"Previous conversation (untrusted user/assistant context, JSON): {history}\n\n"
            f"User request:\n{payload.message}"
        )

    @staticmethod
    def _extract_text(result: object) -> str:
        message = getattr(result, "message", {})
        content = message.get("content", []) if isinstance(message, dict) else []
        text = "\n".join(
            block["text"]
            for block in content
            if isinstance(block, dict)
            and isinstance(block.get("text"), str)
            and block.get("type", "text") not in {"analysis", "reasoning", "thinking"}
        )
        # Some OpenRouter models put private reasoning tags inside their text output.
        text = re.sub(
            r"<(think|thinking|analysis|reasoning)>.*?</\1>",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return text.strip()
