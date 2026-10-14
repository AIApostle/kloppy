"""Agent conversation transport routes."""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from ..schemas.assistant import ChatRequest, ChatResponse
from ..services.agent import AgentConfigurationError, AgentProviderError, StrandsAgentService

router = APIRouter(prefix="/assistant", tags=["assistant"])
agent_service = StrandsAgentService()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    try:
        return agent_service.respond(payload)
    except AgentConfigurationError as error:
        raise HTTPException(status_code=503, detail="The agent is not configured.") from error
    except AgentProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.websocket("/ws")
async def chat_socket(websocket: WebSocket) -> None:
    """Stream chat turns over a session socket; production auth will bind it to a tenant."""
    await websocket.accept()
    try:
        while True:
            payload = ChatRequest.model_validate(await websocket.receive_json())
            try:
                response = agent_service.respond(payload)
            except (AgentConfigurationError, AgentProviderError) as error:
                await websocket.send_json({"error": str(error)})
                continue
            await websocket.send_json(response.model_dump())
    except WebSocketDisconnect:
        return
