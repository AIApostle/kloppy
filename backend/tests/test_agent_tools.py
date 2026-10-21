"""Tests for agent document and research tools."""

import base64
import unittest
from io import BytesIO
from unittest.mock import patch

import httpx
from docx import Document

from app.services import agent_tools
from app.services.agent import _tool_activity_label


class AgentToolTests(unittest.TestCase):
    def test_document_tool_requires_all_campaign_sections(self) -> None:
        schema = agent_tools.draft_document.tool_spec["inputSchema"]["json"]

        self.assertEqual(
            schema["required"],
            ["title", "overview", "audience", "strategy", "launch"],
        )
        self.assertTrue(
            {"overview", "audience", "strategy", "launch"}.issubset(
                schema["properties"]
            )
        )

    def test_activity_labels_do_not_expose_internal_tool_names(self) -> None:
        for tool_name in (
            "qloo_search_entities",
            "qloo_cultural_affinities",
            "qloo_agent_grounding",
            "google_drive_search_files",
        ):
            with self.subTest(tool_name=tool_name):
                label = _tool_activity_label(tool_name)
                self.assertNotIn("qloo", label.lower())
                self.assertNotIn(tool_name, label)

    def test_campaign_document_is_a_word_file_with_all_four_sections(self) -> None:
        sections = {
            "overview": "A campaign overview.",
            "audience": "Two testable audience hypotheses.",
            "strategy": "Lead with the product promise.",
            "launch": "Confirm approval and measure response.",
        }

        artifact = agent_tools._build_docx_artifact("Spring launch", sections)
        binary = base64.b64decode(artifact["docx_base64"])
        document = Document(BytesIO(binary))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]

        self.assertEqual(artifact["format"], "docx")
        self.assertEqual(artifact["filename"], "spring-launch.docx")
        self.assertEqual(artifact["sections"], sections)
        self.assertIn("Overview", paragraphs)
        self.assertIn("Audience", paragraphs)
        self.assertIn("Strategy", paragraphs)
        self.assertIn("Launch & Learn", paragraphs)
        for content in sections.values():
            self.assertIn(content, paragraphs)

    def test_web_search_returns_bounded_source_metadata(self) -> None:
        response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Industry report",
                        "url": "https://example.com/report",
                        "content": "Evidence from a published report.",
                        "published_date": "2026-01-15",
                    }
                ]
            },
            request=httpx.Request("POST", "https://api.tavily.com/search"),
        )
        with (
            patch.object(agent_tools.settings, "tavily_api_key", "test-key"),
            patch.object(agent_tools.httpx, "post", return_value=response) as post,
        ):
            result = agent_tools._run_web_search("  current campaign trends  ")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["query"], "current campaign trends")
        self.assertEqual(result["sources"][0]["url"], "https://example.com/report")
        self.assertEqual(result["sources"][0]["snippet"], "Evidence from a published report.")
        self.assertEqual(post.call_args.kwargs["json"]["api_key"], "test-key")

    def test_web_search_is_explicitly_unavailable_without_configuration(self) -> None:
        with patch.object(agent_tools.settings, "tavily_api_key", None):
            result = agent_tools._run_web_search("current campaign trends")

        self.assertEqual(result["status"], "unavailable")
        self.assertIn("not configured", result["message"])
        self.assertEqual(result["sources"] if "sources" in result else [], [])

    def test_web_search_tool_is_only_exposed_when_configured(self) -> None:
        with (
            patch.object(agent_tools.settings, "tavily_api_key", None),
            patch.object(agent_tools.settings, "qloo_api_key", None),
            patch.object(agent_tools, "connected_mcp_clients", return_value=[]),
        ):
            stack, tools = agent_tools.agent_tool_session()
            stack.close()

        self.assertNotIn(agent_tools.web_search, tools)

        with (
            patch.object(agent_tools.settings, "tavily_api_key", "test-key"),
            patch.object(agent_tools.settings, "qloo_api_key", None),
            patch.object(agent_tools, "connected_mcp_clients", return_value=[]),
        ):
            stack, tools = agent_tools.agent_tool_session()
            stack.close()

        self.assertIn(agent_tools.web_search, tools)


if __name__ == "__main__":
    unittest.main()
