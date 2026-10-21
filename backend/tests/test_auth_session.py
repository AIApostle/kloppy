"""Tests for backend verification of browser sessions."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.application import create_app
from app.services.user_settings import SettingsAuthenticationError, SettingsStoreError


class AuthSessionEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_session_requires_bearer_token(self) -> None:
        response = self.client.get("/api/auth/session")

        self.assertEqual(response.status_code, 401)

    def test_session_returns_verified_user_id(self) -> None:
        with patch(
            "app.routes.auth.endpoints._user_id",
            return_value="user-123",
        ) as verify:
            response = self.client.get(
                "/api/auth/session",
                headers={"Authorization": "Bearer valid-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"user_id": "user-123"})
        verify.assert_called_once_with("valid-token")

    def test_loopback_frontend_origins_can_call_the_api(self) -> None:
        response = self.client.options(
            "/api/auth/session",
            headers={
                "Origin": "http://localhost:5174",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:5174")

    def test_invalid_session_is_rejected(self) -> None:
        with patch(
            "app.routes.auth.endpoints._user_id",
            side_effect=SettingsAuthenticationError("invalid token"),
        ):
            response = self.client.get(
                "/api/auth/session",
                headers={"Authorization": "Bearer expired-token"},
            )

        self.assertEqual(response.status_code, 401)

    def test_auth_provider_outage_is_not_misreported_as_invalid_session(self) -> None:
        with patch(
            "app.routes.auth.endpoints._user_id",
            side_effect=SettingsStoreError("provider unavailable"),
        ):
            response = self.client.get(
                "/api/auth/session",
                headers={"Authorization": "Bearer valid-token"},
            )

        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
