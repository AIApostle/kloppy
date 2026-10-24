"""Agent conversation transport routes."""

import asyncio
import logging
import time
import uuid

from fastapi import APIRouter, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..observability import request_id_context
from ..schemas.assistant import ChatRequest, ChatResponse
from ..services.agent import AgentConfigurationError, AgentProviderError, StrandsAgentService
from ..services.brand_knowledge import context_sources
from ..services.user_settings import SettingsAuthenticationError, SettingsStoreError, read_user_settings

router = APIRouter(prefix="/assistant", tags=["assistant"])
agent_service = StrandsAgentService()
logger = logging.getLogger("kloppy.api.websocket")


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    authorization: str | None = Header(default=None),
) -> ChatResponse:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        user_settings = read_user_settings(authorization[7:].strip())
        return agent_service.respond(payload, user_settings, access_token=authorization[7:].strip(), brand_sources=context_sources(authorization[7:].strip()))
    except SettingsAuthenticationError as error:
        raise HTTPException(status_code=401, detail="Settings or authentication could not be verified.") from error
    except SettingsStoreError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except AgentConfigurationError as error:
        raise HTTPException(status_code=503, detail="The agent is not configured.") from error
    except AgentProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.websocket("/ws")
async def chat_socket(websocket: WebSocket) -> None:
    """Process chat turns without placing the bearer token in the WebSocket URL."""
    request_id = uuid.uuid4().hex
    context_token = request_id_context.set(request_id)
    logger.info(
        "websocket_connection_started request_id=%s route=/api/assistant/ws",
        request_id,
    )
    try:
        await _serve_chat_socket(websocket, request_id)
    except WebSocketDisconnect:
        logger.info("websocket_connection_closed request_id=%s", request_id)
    except Exception as error:
        logger.error(
            "websocket_connection_failed request_id=%s error_type=%s",
            request_id,
            type(error).__name__,
        )
        raise
    finally:
        request_id_context.reset(context_token)


async def _serve_chat_socket(websocket: WebSocket, request_id: str) -> None:
    await websocket.accept()
    try:
        auth_message = await asyncio.wait_for(websocket.receive_json(), timeout=10)
    except (TimeoutError, ValueError, WebSocketDisconnect):
        logger.warning("websocket_auth_failed request_id=%s reason=missing_or_invalid_message", request_id)
        await websocket.close(code=1008, reason="Authentication required")
        return
    token = (
        auth_message.get("access_token")
        if isinstance(auth_message, dict) and auth_message.get("type") == "auth"
        else None
    )
    if not isinstance(token, str) or not token.strip():
        logger.warning("websocket_auth_failed request_id=%s reason=missing_token", request_id)
        await websocket.close(code=1008, reason="Authentication required")
        return
    try:
        user_settings = read_user_settings(token)
    except SettingsAuthenticationError:
        logger.warning("websocket_auth_failed request_id=%s reason=invalid_session", request_id)
        await websocket.close(code=1008, reason="Settings or authentication could not be verified")
        return
    except SettingsStoreError as error:
        logger.error(
            "websocket_setup_failed request_id=%s error_type=%s",
            request_id,
            type(error).__name__,
        )
        await websocket.send_json({"type": "response", "error": str(error), "error_code": "settings_unavailable"})
        await websocket.close(code=1011, reason="Settings storage unavailable")
        return
    logger.info("websocket_authenticated request_id=%s", request_id)
    try:
        while True:
            try:
                raw_payload = await websocket.receive_json()
            except ValueError:
                logger.warning("websocket_request_rejected request_id=%s reason=invalid_json", request_id)
                await websocket.send_json(
                    {
                        "type": "response",
                        "error": "The message format is invalid.",
                        "error_code": "invalid_request",
                    }
                )
                continue
            try:
                payload = ChatRequest.model_validate(raw_payload)
            except ValidationError:
                logger.warning("websocket_request_rejected request_id=%s reason=invalid_payload", request_id)
                await websocket.send_json(
                    {
                        "type": "response",
                        "error": "The message or conversation context is too large or invalid. Please shorten it and try again.",
                        "error_code": "invalid_request",
                    }
                )
                continue
            try:
                # A websocket can outlive a settings change in another tab.
                # Re-read the saved policy before every agent turn.
                user_settings = read_user_settings(token)
                turn_started_at = time.perf_counter()
                logger.info("websocket_turn_started request_id=%s", request_id)
                await websocket.send_json(
                    {"type": "activity", "status": "working", "label": "Connecting campaign context and available tools"}
                )
                loop = asyncio.get_running_loop()
                activity_queue: asyncio.Queue[dict[str, str]] = asyncio.Queue()

                def forward_activity(event: dict[str, str]) -> None:
                    loop.call_soon_threadsafe(activity_queue.put_nowait, event)

                response_task = asyncio.create_task(
                    asyncio.to_thread(
                        agent_service.respond,
                        payload,
                        user_settings,
                        forward_activity,
                        token,
                        context_sources(token),
                    )
                )
                while not response_task.done():
                    try:
                        event = await asyncio.wait_for(activity_queue.get(), timeout=0.25)
                        await websocket.send_json({"type": "activity", **event})
                    except TimeoutError:
                        continue
                while not activity_queue.empty():
                    await websocket.send_json({"type": "activity", **activity_queue.get_nowait()})
                response = await response_task
            except SettingsAuthenticationError as error:
                logger.warning("websocket_turn_failed request_id=%s error_type=%s", request_id, type(error).__name__)
                await websocket.send_json({"type": "response", "error": str(error), "error_code": "authentication_required"})
                await websocket.close(code=1008, reason="Authentication could not be verified")
                return
            except SettingsStoreError as error:
                logger.error("websocket_turn_failed request_id=%s error_type=%s", request_id, type(error).__name__)
                await websocket.send_json({"type": "response", "error": str(error), "error_code": "settings_unavailable"})
                continue
            except (AgentConfigurationError, AgentProviderError) as error:
                logger.error("websocket_turn_failed request_id=%s error_type=%s", request_id, type(error).__name__)
                await websocket.send_json({"type": "response", "error": str(error)})
                continue
            await websocket.send_json({"type": "response", **response.model_dump()})
            logger.info(
                "websocket_turn_completed request_id=%s duration_ms=%.1f",
                request_id,
                (time.perf_counter() - turn_started_at) * 1000,
            )
    except WebSocketDisconnect:
        logger.info("websocket_connection_closed request_id=%s", request_id)
        return
