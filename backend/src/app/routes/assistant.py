"""Agent conversation routes."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

router = APIRouter(prefix="/assistant", tags=["assistant"])


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


def build_response(payload: ChatRequest) -> ChatResponse:
    """Return a deterministic response until the Strands runtime is connected."""
    text = payload.message.lower()
    if "audience" in text:
        reply = "I found three useful audience directions. I recommend starting with Culture-led early adopters because the evidence is strongest there."
        actions = ["Compare the three segments", "Draft audience messaging", "Show the evidence"]
    elif "creative" in text or "asset" in text:
        reply = "I can turn the approved strategy into a coordinated creative set: launch story, social variations, email copy, and a presentation outline."
        actions = ["Start the creative set", "Review the strategy", "Open the campaign map"]
    elif "campaign" in text or "launch" in text:
        reply = "Your Lagos product launch is in strategy review. Approve an audience first, then I can move the campaign into creative production."
        actions = ["Choose an audience", "Review the campaign brief", "Open integrations"]
    else:
        reply = "I’m ready to help shape the next marketing move. Ask me about your audience, strategy, creative, launch plan, or campaign evidence."
        actions = ["What should I do next?", "Find an audience", "Build the campaign plan"]
    artifact = None
    if payload.mode == "plan":
        artifact = {
            "title": "Campaign plan",
            "content": "Campaign plan\n\n1. Research the audience and market context.\n2. Review the evidence with the team.\n3. Approve the strategy before creative production.\n4. Prepare execution actions and request permission before publishing.",
        }
    if payload.mode == "research":
        reply = f"Research mode is active. I’ll search only and return sources, findings, and uncertainty before recommending a next step. {reply}"
        artifact = None
    if payload.mode == "execute":
        reply = f"Execute mode is active. I’ll research and plan first, then pause for permission unless your policy is auto-approve. {reply}"
    return ChatResponse(reply=reply, next_actions=actions, artifact=artifact)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return build_response(payload)


@router.websocket("/ws")
async def chat_socket(websocket: WebSocket) -> None:
    """Stream chat turns over a session socket; production auth will bind it to a tenant."""
    await websocket.accept()
    try:
        while True:
            payload = ChatRequest.model_validate(await websocket.receive_json())
            await websocket.send_json(build_response(payload).model_dump())
    except WebSocketDisconnect:
        return
