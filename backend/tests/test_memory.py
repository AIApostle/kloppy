"""Tests for user-scoped Walrus Memory integration."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from memwal import MemWalError, RecallMemory, RecallResult

from app.schemas.assistant import ChatRequest
from app.services import memory
from app.services.agent import StrandsAgentService


class WalrusMemoryTests(unittest.TestCase):
    def test_namespace_is_stable_and_scoped_to_user_and_campaign(self) -> None:
        workspace = memory._namespace("user-1")
        same_workspace = memory._namespace("user-1")
        another_user = memory._namespace("user-2")
        campaign = memory._namespace("user-1", "campaign-1")
        another_campaign = memory._namespace("user-1", "campaign-2")

        self.assertEqual(workspace, same_workspace)
        self.assertNotEqual(workspace, another_user)
        self.assertNotEqual(workspace, campaign)
        self.assertNotEqual(campaign, another_campaign)
        self.assertLessEqual(len(campaign), 64)
        self.assertTrue(campaign.startswith("kloppy-"))

    def test_memory_is_disabled_without_account_credentials(self) -> None:
        with (
            patch.object(memory.settings, "memwal_private_key", None),
            patch.object(memory.settings, "memwal_account_id", None),
            patch.object(memory, "_user_id") as user_id,
            patch.object(memory.MemWalSync, "create") as create_client,
        ):
            context = memory.capture_turn_memory("token", "I prefer concise answers.")

        self.assertEqual(context.status, "not_configured")
        self.assertEqual(context.memories, ())
        user_id.assert_not_called()
        create_client.assert_not_called()

    def test_campaign_memory_is_recalled_and_user_message_is_analyzed(self) -> None:
        client = MagicMock()
        client.recall.side_effect = [
            RecallResult(
                results=[
                    RecallMemory(
                        blob_id="blob-1",
                        text="Workspace preference: concise answers.",
                        distance=0.2,
                    )
                ],
                total=1,
            ),
            RecallResult(
                results=[
                    RecallMemory(
                        blob_id="blob-2",
                        text="Campaign preference: practical examples.",
                        distance=0.3,
                    )
                ],
                total=1,
            ),
        ]
        client.analyze.return_value = SimpleNamespace(job_ids=["job-1"])
        with (
            patch.object(memory.settings, "memwal_private_key", "private-key"),
            patch.object(memory.settings, "memwal_account_id", "account-id"),
            patch.object(memory, "_user_id", return_value="verified-user-id"),
            patch.object(memory.MemWalSync, "create", return_value=client),
        ):
            context = memory.capture_turn_memory(
                "verified-token",
                "I prefer concise answers and practical examples.",
                "campaign-1",
            )

        self.assertEqual(context.status, "available")
        self.assertEqual(
            context.memories,
            (
                {"scope": "workspace", "text": "Workspace preference: concise answers."},
                {"scope": "campaign", "text": "Campaign preference: practical examples."},
            ),
        )
        self.assertEqual(client.recall.call_count, 2)
        self.assertEqual(
            client.analyze.call_args.kwargs["namespace"],
            memory._namespace("verified-user-id", "campaign-1"),
        )
        client.close.assert_called_once()

    def test_memory_provider_failure_is_degraded_without_throwing(self) -> None:
        client = MagicMock()
        client.recall.side_effect = MemWalError("relayer unavailable")
        with (
            patch.object(memory.settings, "memwal_private_key", "private-key"),
            patch.object(memory.settings, "memwal_account_id", "account-id"),
            patch.object(memory, "_user_id", return_value="verified-user-id"),
            patch.object(memory.MemWalSync, "create", return_value=client),
        ):
            context = memory.capture_turn_memory(
                "verified-token",
                "Please help me outline this launch.",
            )

        self.assertEqual(context.status, "unavailable")
        self.assertEqual(context.memories, ())
        client.analyze.assert_not_called()
        client.close.assert_called_once()

    def test_agent_prompt_labels_recalled_memory_as_untrusted_context(self) -> None:
        prompt = StrandsAgentService._prompt_for(
            ChatRequest(message="Help with the next campaign."),
            {"name": "A.", "workspace": "Studio", "permission_policy": "ask"},
            [],
            memory_context=memory.AgentMemoryContext(
                status="available",
                memories=({"scope": "workspace", "text": "The user prefers concise plans."},),
            ),
        )

        self.assertIn("WALRUS_MEMORY", prompt)
        self.assertIn('"status": "available"', prompt)
        self.assertIn("untrusted data", prompt)
        self.assertIn("The user prefers concise plans.", prompt)


if __name__ == "__main__":
    unittest.main()
