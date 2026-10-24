"""Tests for privacy-safe API and external-operation logging."""

import unittest

from fastapi.testclient import TestClient

from app.application import create_app
from app.observability import log_external_call


class ObservabilityTests(unittest.TestCase):
    def test_http_request_logs_method_route_status_and_request_id_without_query(self) -> None:
        client = TestClient(create_app())
        secret = "sensitive-query-value"

        with self.assertLogs("kloppy.api", level="INFO") as captured:
            response = client.get(f"/health?access_token={secret}")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get("X-Request-ID"))
        logs = "\n".join(captured.output)
        self.assertIn("method=GET", logs)
        self.assertIn("route=/health", logs)
        self.assertIn("status_code=200", logs)
        self.assertNotIn(secret, logs)

    def test_external_success_logs_provider_operation_and_status_only(self) -> None:
        secret = "private-provider-payload"
        with self.assertLogs("kloppy.observability", level="INFO") as captured:
            with log_external_call("tavily", "search") as call:
                call.status_code = 200

        logs = "\n".join(captured.output)
        self.assertIn("provider=tavily", logs)
        self.assertIn("operation=search", logs)
        self.assertIn("status_code=200", logs)
        self.assertNotIn(secret, logs)

    def test_external_failure_does_not_log_exception_message(self) -> None:
        secret = "sensitive-provider-response"
        with self.assertLogs("kloppy.observability", level="WARNING") as captured:
            with self.assertRaisesRegex(RuntimeError, secret):
                with log_external_call("openrouter", "agent.completion"):
                    raise RuntimeError(secret)

        logs = "\n".join(captured.output)
        self.assertIn("provider=openrouter", logs)
        self.assertIn("error_type=RuntimeError", logs)
        self.assertNotIn(secret, logs)


if __name__ == "__main__":
    unittest.main()
