"""Tests for assistant chat transport validation."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from app.routes.assistant import chat_socket
from app.schemas.assistant import ChatRequest, ChatResponse


class AssistantRequestValidationTests(unittest.TestCase):
    def test_assistant_history_allows_longer_agent_replies(self) -> None:
        request = ChatRequest.model_validate(
            {
                "message": "Continue.",
                "conversation_history": [
                    {"role": "assistant", "content": "A" * 2500},
                ],
            }
        )

        self.assertEqual(len(request.conversation_history[0].content), 2500)

    def test_user_history_keeps_the_user_message_limit(self) -> None:
        with self.assertRaises(ValidationError):
            ChatRequest.model_validate(
                {
                    "message": "Continue.",
                    "conversation_history": [
                        {"role": "user", "content": "A" * 2001},
                    ],
                }
            )


class AssistantWebSocketValidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_payload_returns_error_and_keeps_socket_alive(self) -> None:
        websocket = MagicMock()
        websocket.query_params = {}
        websocket.accept = AsyncMock()
        websocket.close = AsyncMock()
        websocket.send_json = AsyncMock()
        websocket.receive_json = AsyncMock(
            side_effect=[
                {"type": "auth", "access_token": "verified-token"},
                {
                    "message": "Continue.",
                    "conversation_history": [
                        {"role": "user", "content": "A" * 2001},
                    ],
                },
                WebSocketDisconnect(),
            ]
        )

        with patch(
            "app.routes.assistant.read_user_settings",
            return_value={"permission_policy": "ask"},
        ):
            await chat_socket(websocket)

        websocket.send_json.assert_awaited_once_with(
            {
                "type": "response",
                "error": "The message or conversation context is too large or invalid. Please shorten it and try again.",
                "error_code": "invalid_request",
            }
        )
        websocket.close.assert_not_awaited()

    async def test_websocket_does_not_accept_bearer_token_from_url(self) -> None:
        websocket = MagicMock()
        websocket.query_params = {"access_token": "must-not-use-url-token"}
        websocket.accept = AsyncMock()
        websocket.close = AsyncMock()
        websocket.receive_json = AsyncMock(return_value={"message": "not an auth frame"})

        with self.assertLogs("kloppy.api.websocket", level="INFO") as captured:
            await chat_socket(websocket)

        websocket.close.assert_awaited_once_with(
            code=1008,
            reason="Authentication required",
        )
        self.assertNotIn("must-not-use-url-token", "\n".join(captured.output))


class AssistantInteractiveQuestionTests(unittest.IsolatedAsyncioTestCase):
    async def test_turn_waits_for_popup_answer_before_sending_final_response(self) -> None:
        question_sent = asyncio.Event()
        response_sent = asyncio.Event()
        frames = [
            {"type": "auth", "access_token": "verified-token"},
            {"message": "Create a CRM contact."},
        ]
        sent: list[dict] = []
        websocket = MagicMock()
        websocket.query_params = {}
        websocket.accept = AsyncMock()
        websocket.close = AsyncMock()

        async def receive_json():
            if frames:
                return frames.pop(0)
            if not question_sent.is_set():
                await question_sent.wait()
                return {
                    "type": "answer",
                    "question_id": next(item["question_id"] for item in sent if item["type"] == "question"),
                    "approved": True,
                    "answer": "Allow once",
                }
            await response_sent.wait()
            raise WebSocketDisconnect()

        async def send_json(frame: dict) -> None:
            sent.append(frame)
            if frame.get("type") == "question":
                question_sent.set()
            elif frame.get("type") == "response":
                response_sent.set()

        websocket.receive_json = receive_json
        websocket.send_json = send_json

        def respond(*args, request_user_input, cancel_signal):
            answer = request_user_input(
                {
                    "question": "May I create this contact?",
                    "question_type": "permission",
                    "options": ["Allow once", "Do not allow"],
                }
            )
            return ChatResponse(reply=f"Approval: {answer['approved']}", next_actions=[])

        with (
            patch("app.routes.assistant.read_user_settings", return_value={"permission_policy": "ask"}),
            patch("app.routes.assistant.context_sources", return_value=[]),
            patch("app.routes.assistant.agent_service.respond", side_effect=respond),
        ):
            await chat_socket(websocket)

        question = next(item for item in sent if item.get("type") == "question")
        final_response = next(item for item in sent if item.get("type") == "response")
        self.assertEqual(question["question_type"], "permission")
        self.assertEqual(question["options"], ["Allow once", "Do not allow"])
        self.assertEqual(final_response["reply"], "Approval: True")
        self.assertLess(sent.index(question), sent.index(final_response))

    async def test_cancel_frame_signals_agent_and_reports_stopped(self) -> None:
        stopped_sent = asyncio.Event()
        frames = [
            {"type": "auth", "access_token": "verified-token"},
            {"message": "Prepare a campaign."},
            {"type": "cancel"},
        ]
        sent: list[dict] = []
        websocket = MagicMock()
        websocket.query_params = {}
        websocket.accept = AsyncMock()
        websocket.close = AsyncMock()

        async def receive_json():
            if frames:
                return frames.pop(0)
            await stopped_sent.wait()
            raise WebSocketDisconnect()

        async def send_json(frame: dict) -> None:
            sent.append(frame)
            if frame.get("type") == "stopped":
                stopped_sent.set()

        websocket.receive_json = receive_json
        websocket.send_json = send_json

        def respond(*args, cancel_signal, **kwargs):
            self.assertTrue(cancel_signal.wait(timeout=2))
            return ChatResponse(reply="This should not be sent.", next_actions=[])

        with (
            patch("app.routes.assistant.read_user_settings", return_value={"permission_policy": "ask"}),
            patch("app.routes.assistant.context_sources", return_value=[]),
            patch("app.routes.assistant.agent_service.respond", side_effect=respond),
        ):
            await chat_socket(websocket)

        self.assertIn({"type": "stopped"}, sent)
        self.assertFalse(any(item.get("reply") == "This should not be sent." for item in sent))


if __name__ == "__main__":
    unittest.main()
