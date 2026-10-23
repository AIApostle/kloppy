"""Agent conversation transport routes."""

import asyncio

from fastapi import APIRouter, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..schemas.assistant import ChatRequest, ChatResponse
from ..services.agent import AgentConfigurationError, AgentProviderError, StrandsAgentService
from ..services.brand_knowledge import context_sources
from ..services.user_settings import SettingsAuthenticationError, SettingsStoreError, read_user_settings

router = APIRouter(prefix="/assistant", tags=["assistant"])
agent_service = StrandsAgentService()


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
    """Process chat turns over a WebSocket with the frontend's Supabase token."""
    token = websocket.query_params.get("access_token")
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    try:
        user_settings = read_user_settings(token)
    except SettingsAuthenticationError:
        await websocket.close(code=1008, reason="Settings or authentication could not be verified")
        return
    except SettingsStoreError as error:
        await websocket.accept()
        await websocket.send_json({"type": "response", "error": str(error), "error_code": "settings_unavailable"})
        await websocket.close(code=1011, reason="Settings storage unavailable")
        return
    await websocket.accept()
    try:
        while True:
            raw_payload = await websocket.receive_json()
            try:
                payload = ChatRequest.model_validate(raw_payload)
            except ValidationError:
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
                await websocket.send_json({"type": "response", "error": str(error), "error_code": "authentication_required"})
                await websocket.close(code=1008, reason="Authentication could not be verified")
                return
            except SettingsStoreError as error:
                await websocket.send_json({"type": "response", "error": str(error), "error_code": "settings_unavailable"})
                continue
            except (AgentConfigurationError, AgentProviderError) as error:
                await websocket.send_json({"type": "response", "error": str(error)})
                continue
            await websocket.send_json({"type": "response", **response.model_dump()})
    except WebSocketDisconnect:
        return
