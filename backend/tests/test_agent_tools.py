"""Tests for agent document and research tools."""

import base64
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

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
        with (
            patch.object(agent_tools.settings, "tavily_api_key", "test-key"),
            patch.object(agent_tools, "TavilyClient") as tavily_client,
        ):
            tavily_client.return_value.search.return_value = {
                "results": [
                    {
                        "title": "Industry report",
                        "url": "https://example.com/report",
                        "content": "Evidence from a published report.",
                        "published_date": "2026-01-15",
                    }
                ]
            }
            result = agent_tools._run_web_search("  current campaign trends  ")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["query"], "current campaign trends")
        self.assertEqual(result["sources"][0]["url"], "https://example.com/report")
        self.assertEqual(result["sources"][0]["snippet"], "Evidence from a published report.")
        tavily_client.assert_called_once_with(api_key="test-key")
        tavily_client.return_value.search.assert_called_once_with(
            "current campaign trends",
            timeout=15,
            search_depth="basic",
            max_results=6,
            include_answer=False,
            include_raw_content=False,
            include_published_date=True,
        )

    def test_web_search_is_explicitly_unavailable_without_configuration(self) -> None:
        with patch.object(agent_tools.settings, "tavily_api_key", None):
            result = agent_tools._run_web_search("current campaign trends")

        self.assertEqual(result["status"], "unavailable")
        self.assertIn("not configured", result["message"])
        self.assertEqual(result["sources"] if "sources" in result else [], [])

    def test_web_image_search_returns_safe_images_with_source_links(self) -> None:
        with (
            patch.object(agent_tools.settings, "tavily_api_key", "test-key"),
            patch.object(agent_tools, "TavilyClient") as tavily_client,
        ):
            tavily_client.return_value.search.return_value = {
                "images": [
                    {
                        "url": "https://cdn.example.com/image.jpg",
                        "description": "A bright product display",
                    },
                    {"url": "javascript:alert(1)", "description": "Unsafe URL"},
                ],
                "results": [
                    {
                        "title": "Product display ideas",
                        "url": "https://example.com/ideas",
                        "images": [{"url": "https://cdn.example.com/image.jpg"}],
                    }
                ],
            }
            result = agent_tools._run_web_image_search("  product display examples  ")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["query"], "product display examples")
        self.assertEqual(
            result["images"],
            [
                {
                    "url": "https://cdn.example.com/image.jpg",
                    "description": "A bright product display",
                    "source_title": "Product display ideas",
                    "source_url": "https://example.com/ideas",
                }
            ],
        )
        tavily_client.assert_called_once_with(api_key="test-key")
        self.assertTrue(tavily_client.return_value.search.call_args.kwargs["include_images"])
        self.assertTrue(
            tavily_client.return_value.search.call_args.kwargs["include_image_descriptions"]
        )
        self.assertTrue(tavily_client.return_value.search.call_args.kwargs["safe_search"])

    def test_web_image_search_records_results_for_chat_response(self) -> None:
        tool_function = agent_tools.web_image_search.__wrapped__
        invocation_context = SimpleNamespace(invocation_state={})
        with patch.object(
            agent_tools,
            "_run_web_image_search",
            return_value={"status": "ok", "images": [{"url": "https://example.com/image.jpg"}]},
        ):
            result = tool_function("campaign examples", invocation_context)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            invocation_context.invocation_state["visual_results"],
            [{"url": "https://example.com/image.jpg"}],
        )

    def test_web_search_tool_is_always_exposed(self) -> None:
        with (
            patch.object(agent_tools.settings, "tavily_api_key", None),
            patch.object(agent_tools.settings, "qloo_api_key", None),
            patch.object(agent_tools, "connected_mcp_clients", return_value=[]),
        ):
            stack, tools = agent_tools.agent_tool_session()
            stack.close()

        self.assertIn(agent_tools.web_search, tools)
        self.assertIn(agent_tools.web_image_search, tools)
        self.assertIn(
            "only when current, external, or explicitly requested facts",
            agent_tools.web_search.__doc__,
        )

    def test_project_memory_tool_is_only_exposed_for_a_selected_project(self) -> None:
        with patch.object(agent_tools, "connected_mcp_clients", return_value=[]):
            stack, tools = agent_tools.agent_tool_session(memory_enabled=False)
            stack.close()
            self.assertNotIn(agent_tools.walrus_remember_project_fact, tools)

            stack, tools = agent_tools.agent_tool_session(memory_enabled=True)
            stack.close()
            self.assertIn(agent_tools.walrus_remember_project_fact, tools)

    def test_interactive_question_tool_is_only_exposed_when_transport_can_pause(self) -> None:
        with patch.object(agent_tools, "connected_mcp_clients", return_value=[]):
            stack, tools = agent_tools.agent_tool_session(interactive=False)
            stack.close()
            self.assertNotIn(agent_tools.ask_user, tools)

            stack, tools = agent_tools.agent_tool_session(interactive=True)
            stack.close()
            self.assertIn(agent_tools.ask_user, tools)

    def test_permission_question_has_fixed_allow_or_decline_options(self) -> None:
        tool_function = agent_tools.ask_user.__wrapped__
        invocation_context = SimpleNamespace(
            invocation_state={
                "request_user_input": lambda question: question,
            }
        )

        result = tool_function(
            "May I create this HubSpot contact?",
            "permission",
            ["custom model-proposed option"],
            invocation_context,
        )

        self.assertEqual(result["options"], ["Allow once", "Do not allow"])
        self.assertEqual(result["question_type"], "permission")

    def test_project_memory_tool_uses_server_supplied_namespace(self) -> None:
        tool_function = agent_tools.walrus_remember_project_fact.__wrapped__
        invocation_context = SimpleNamespace(
            invocation_state={"walrus_project_namespace": "kloppy-user-project-hash"}
        )
        with patch.object(
            agent_tools,
            "remember_project_fact",
            return_value={"status": "queued"},
        ) as remember:
            result = tool_function(
                "The launch is planned for September.",
                invocation_context,
            )

        self.assertEqual(result, {"status": "queued"})
        remember.assert_called_once_with(
            "kloppy-user-project-hash",
            "The launch is planned for September.",
        )
        self.assertEqual(
            agent_tools.walrus_remember_project_fact.tool_spec["inputSchema"]["json"][
                "properties"
            ].keys(),
            {"fact"},
        )


if __name__ == "__main__":
    unittest.main()
