"""Strands-backed agent orchestration boundary."""

import json
import logging
import re
from collections.abc import Callable
from typing import Any, Protocol

from strands import Agent
from strands.models.openai import OpenAIModel

from ..schemas.assistant import ChatRequest, ChatResponse
from ..config import settings
from ..prompts import BASE_PROMPT
from .agent_tools import agent_tool_session

logger = logging.getLogger(__name__)


class AgentConfigurationError(RuntimeError):
    """Raised when agent provider configuration is incomplete."""


class AgentProviderError(RuntimeError):
    """Raised when the configured agent provider cannot complete a turn."""


class AgentService(Protocol):
    def respond(
        self,
        payload: ChatRequest,
        user_settings: dict | None = None,
        on_activity: Callable[[dict[str, str]], None] | None = None,
    ) -> ChatResponse:
        """Run one agent turn and return the structured API response."""


class StrandsAgentService:
    """Builds a request-scoped, intent-driven Kloppy agent."""

    def respond(
        self,
        payload: ChatRequest,
        user_settings: dict | None = None,
        on_activity: Callable[[dict[str, str]], None] | None = None,
    ) -> ChatResponse:
        if not settings.openrouter_api_key:
            raise AgentConfigurationError("OpenRouter is not configured.")

        if user_settings is None:
            raise AgentProviderError("Saved user permissions could not be checked; the agent is paused.")
        # Permission comes from the authenticated database row, never the browser.
        activities: list[dict[str, str]] = []

        def emit(label: str, status: str = "working", tool_name: str = "") -> None:
            event = {"label": label, "status": status}
            if tool_name:
                event["tool"] = tool_name
            activities.append(event)
            if on_activity:
                try:
                    on_activity(event)
                except Exception:
                    logger.debug("Could not forward agent activity", exc_info=True)

        active_tools: dict[str, str] = {}

        def callback_handler(**event: Any) -> None:
            current = event.get("current_tool_use")
            if isinstance(current, dict):
                name = current.get("name")
                tool_id = str(current.get("toolUseId") or name or "")
                if isinstance(name, str) and name and tool_id not in active_tools:
                    active_tools[tool_id] = name
                    emit(_tool_activity_label(name), tool_name=name)

        emit("Reviewing your brief and saved preferences")
        stack, tools = agent_tool_session()
        try:
            with stack:
                prompt = self._prompt_for(payload, user_settings, tools)
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
                    model_id=settings.strands_model_id or "openrouter/free",
                )
                agent = Agent(
                    model=model,
                    name="kloppy",
                    description="Kloppy marketing operating system agent",
                    system_prompt=BASE_PROMPT,
                    tools=tools,
                    callback_handler=callback_handler,
                )
                invocation_state: dict[str, Any] = {"artifacts": []}
                result = agent(prompt, invocation_state=invocation_state)
        except Exception as error:
            raise AgentProviderError("The agent could not complete this request.") from error

        reply = self._extract_text(result)
        if not reply:
            raise AgentProviderError("The agent returned an empty response.")
        for name in active_tools.values():
            emit(_tool_activity_label(name), status="done", tool_name=name)
        emit("Response ready", status="done")
        artifacts = invocation_state.get("artifacts", [])
        artifact = artifacts[-1] if artifacts else None
        return ChatResponse(reply=reply, next_actions=[], artifact=artifact, activities=activities)

    @staticmethod
    def _prompt_for(payload: ChatRequest, user_settings: dict, available_tools: list[Any]) -> str:
        history = json.dumps(
            [turn.model_dump() for turn in payload.conversation_history],
            ensure_ascii=False,
        )
        return (
            f"BUSINESS_PROFILE: workspace={user_settings.get('workspace') or 'not supplied'}; contact name={user_settings.get('name') or 'not supplied'}\n"
            f"CURRENT_PROJECT: campaign_id={payload.campaign_id or 'general workspace'}; name={payload.campaign_name or 'Kloppy workspace'}\n"
            f"CAMPAIGN_CONTEXT: Work only in the selected campaign `{payload.campaign_name}` (id: {payload.campaign_id}). Do not carry facts, decisions, drafts, or conversation context from another campaign. If no campaign is selected, treat this as general workspace chat.\n"
            f"AVAILABLE_TOOLS: {', '.join(_tool_name(item) for item in available_tools)}\n"
            "Use an available tool when it materially improves the work. Do not claim a tool ran unless its result confirms it.\n"
            "CONNECTED_RESOURCES: only the tools listed above are connected for this turn; other integrations are unavailable.\n"
            f"Server-verified saved user settings: {user_settings}\n"
            f"USER_PERMISSIONS / APPROVAL_POLICY: saved preference is {user_settings.get('permission_policy', 'ask')}; external publishing/spend still requires explicit approval\n"
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


def _tool_name(item: Any) -> str:
    return getattr(item, "tool_name", getattr(item, "__name__", type(item).__name__))


def _tool_activity_label(name: str) -> str:
    normalized = name.lower()
    if "qloo_search" in normalized:
        return "Searching Qloo for relevant cultural entities"
    if "qloo_cultural" in normalized:
        return "Reading Qloo cultural affinity signals"
    if "draft_document" in normalized:
        return "Preparing a document draft"
    return f"Using connected service tool: {name.replace('_', ' ')}"
