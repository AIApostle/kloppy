"""Agent conversation transport routes."""

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
                if payload.mode == "execute":
                    # Re-read the policy immediately before every Execute turn;
                    # a websocket may outlive a settings change in another tab.
                    user_settings = read_user_settings(token)
                response = agent_service.respond(payload, user_settings)
            except (AgentConfigurationError, AgentProviderError, SettingsStoreError) as error:
                await websocket.send_json({"error": str(error)})
                continue
            await websocket.send_json(response.model_dump())
    except WebSocketDisconnect:
        return
