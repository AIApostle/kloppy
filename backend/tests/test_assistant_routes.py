"""Tests for assistant chat transport validation."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from app.routes.assistant import chat_socket
from app.schemas.assistant import ChatRequest


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


if __name__ == "__main__":
    unittest.main()
