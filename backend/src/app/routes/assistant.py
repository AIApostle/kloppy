"""Agent conversation transport routes."""

import asyncio

from fastapi import APIRouter, Header, HTTPException, WebSocket, WebSocketDisconnect

from ..schemas.assistant import ChatRequest, ChatResponse
from ..services.agent import AgentConfigurationError, AgentProviderError, StrandsAgentService
from ..services.user_settings import SettingsStoreError, read_user_settings

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
        return agent_service.respond(payload, user_settings)
    except SettingsStoreError as error:
        raise HTTPException(status_code=401, detail="Settings or authentication could not be verified.") from error
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
    except SettingsStoreError:
        await websocket.close(code=1008, reason="Settings or authentication could not be verified")
        return
    await websocket.accept()
    try:
        while True:
            payload = ChatRequest.model_validate(await websocket.receive_json())
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
            except (AgentConfigurationError, AgentProviderError, SettingsStoreError) as error:
                await websocket.send_json({"type": "response", "error": str(error)})
                continue
            await websocket.send_json({"type": "response", **response.model_dump()})
    except WebSocketDisconnect:
        return
