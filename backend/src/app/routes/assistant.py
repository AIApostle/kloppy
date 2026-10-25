"""Agent conversation transport routes."""

import asyncio
from concurrent.futures import Future, TimeoutError as FutureTimeoutError
import logging
import time
from threading import Event, Lock
import uuid
from typing import Any

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
QUESTION_TIMEOUT_SECONDS = 300


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
                response, stopped = await _run_agent_turn(
                    websocket,
                    payload,
                    user_settings,
                    token,
                )
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
            if stopped:
                await websocket.send_json({"type": "stopped"})
                logger.info("websocket_turn_stopped request_id=%s", request_id)
                continue
            if response is None:
                raise AgentProviderError("The agent ended without a response.")
            await websocket.send_json({"type": "response", **response.model_dump()})
            logger.info(
                "websocket_turn_completed request_id=%s duration_ms=%.1f",
                request_id,
                (time.perf_counter() - turn_started_at) * 1000,
            )
    except WebSocketDisconnect:
        logger.info("websocket_connection_closed request_id=%s", request_id)
        return


async def _run_agent_turn(
    websocket: WebSocket,
    payload: ChatRequest,
    user_settings: dict[str, Any],
    token: str,
) -> tuple[ChatResponse | None, bool]:
    loop = asyncio.get_running_loop()
    events: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    cancel_signal = Event()
    questions: dict[str, Future[dict[str, Any]]] = {}
    question_lock = Lock()

    def queue_event(event: dict[str, Any]) -> None:
        loop.call_soon_threadsafe(events.put_nowait, event)

    def forward_activity(event: dict[str, str]) -> None:
        queue_event({"type": "activity", **event})

    def request_user_input(question: dict[str, Any]) -> dict[str, Any]:
        question_id = uuid.uuid4().hex
        result: Future[dict[str, Any]] = Future()
        with question_lock:
            questions[question_id] = result
        queue_event({"type": "question", "question_id": question_id, **question, "_future": result})
        try:
            return result.result(timeout=QUESTION_TIMEOUT_SECONDS)
        except FutureTimeoutError:
            return {"status": "timed_out"}
        finally:
            with question_lock:
                questions.pop(question_id, None)

    response_task = asyncio.create_task(
        asyncio.to_thread(
            agent_service.respond,
            payload,
            user_settings,
            forward_activity,
            token,
            context_sources(token),
            request_user_input=request_user_input,
            cancel_signal=cancel_signal,
        )
    )
    receive_task = asyncio.create_task(websocket.receive_json())
    event_task = asyncio.create_task(events.get())
    stopped = False

    def resolve_open_questions(result: dict[str, Any]) -> None:
        with question_lock:
            pending = list(questions.values())
        for future in pending:
            if not future.done():
                future.set_result(result)

    try:
        while not response_task.done():
            done, _ = await asyncio.wait(
                {response_task, receive_task, event_task},
                timeout=0.25,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if receive_task in done:
                frame = receive_task.result()
                if isinstance(frame, dict) and frame.get("type") == "answer":
                    question_id = frame.get("question_id")
                    with question_lock:
                        result = questions.get(question_id) if isinstance(question_id, str) else None
                    if result and not result.done():
                        if frame.get("cancelled") is True:
                            result.set_result({"status": "cancelled"})
                        elif frame.get("approved") is not None:
                            if isinstance(frame.get("approved"), bool):
                                result.set_result(
                                    {
                                        "status": "answered",
                                        "approved": frame["approved"],
                                        "answer": "Allow once" if frame["approved"] else "Do not allow",
                                    }
                                )
                        else:
                            answer = frame.get("answer")
                            if isinstance(answer, str) and answer.strip() and len(answer) <= 2000:
                                result.set_result({"status": "answered", "answer": answer.strip()})
                elif isinstance(frame, dict) and frame.get("type") == "cancel":
                    stopped = True
                    cancel_signal.set()
                    resolve_open_questions({"status": "cancelled"})
                    await websocket.send_json(
                        {"type": "activity", "status": "waiting", "label": "Stopping your response"}
                    )
                receive_task = asyncio.create_task(websocket.receive_json())

            if event_task in done:
                event = event_task.result()
                future = event.pop("_future", None)
                if event.get("type") == "question":
                    question_id = event.get("question_id")
                    if isinstance(question_id, str) and isinstance(future, Future):
                        with question_lock:
                            questions[question_id] = future
                    if stopped:
                        if isinstance(future, Future) and not future.done():
                            future.set_result({"status": "cancelled"})
                        event_task = asyncio.create_task(events.get())
                        continue
                await websocket.send_json(event)
                event_task = asyncio.create_task(events.get())

        while not events.empty():
            event = events.get_nowait()
            event.pop("_future", None)
            await websocket.send_json(event)

        if stopped:
            return None, True
        return await response_task, False
    finally:
        if not response_task.done():
            cancel_signal.set()
            resolve_open_questions({"status": "cancelled"})
            try:
                await asyncio.wait_for(asyncio.shield(response_task), timeout=10)
            except TimeoutError:
                logger.warning("websocket_agent_shutdown_timeout")
            except Exception as error:
                logger.warning("websocket_agent_shutdown_failed error_type=%s", type(error).__name__)
        for task in (receive_task, event_task):
            task.cancel()
