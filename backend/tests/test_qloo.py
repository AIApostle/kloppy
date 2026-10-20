"""Tests for Qloo response normalization and capability-specific requests."""

import unittest
from unittest.mock import patch

from app.schemas.qloo import QlooCapabilityRequest
from app.services import qloo


class QlooCapabilityTests(unittest.TestCase):
    def test_entity_search_response_is_normalized_and_sensitive_attributes_are_excluded(self) -> None:
        with patch.object(
            qloo,
            "_request",
            return_value={
                "results": [
                    {
                        "name": "Example",
                        "entity_id": "entity-1",
                        "types": ["urn:entity:brand"],
                        "properties": {
                            "description": "A fashion brand.",
                            "keywords": ["footwear"],
                            "gender": "not exposed",
                        },
                    }
                ]
            },
        ) as request:
            results = qloo.search_entities("Example", "brand")

        self.assertEqual(results[0]["entity_id"], "entity-1")
        self.assertEqual(results[0]["properties"], {"description": "A fashion brand.", "keywords": ["footwear"]})
        request.assert_called_once_with("/search", {"query": "Example", "take": 8, "types": "urn:entity:brand"})

    def test_enrichment_resolves_then_fetches_full_entity_by_id(self) -> None:
        with patch.object(
            qloo,
            "_request",
            side_effect=[
                {"results": [{"name": "Example", "entity_id": "entity-1"}]},
                {"results": [{"name": "Example", "entity_id": "entity-1", "properties": {"description": "Verified."}}]},
            ],
        ) as request:
            result = qloo.run_capability(
                QlooCapabilityRequest(capability="enrichment", query="Example")
            )

        self.assertEqual(result["results"][0]["description"], "Verified.")
        self.assertEqual(request.call_args_list[1].args, ("/entities", {"entity_ids": "entity-1"}))

    def test_taste_analysis_requests_tag_insights(self) -> None:
        with patch.object(
            qloo,
            "_request",
            side_effect=[
                {"results": [{"name": "Example", "entity_id": "entity-1"}]},
                {
                    "results": {
                        "tags": [
                            {
                                "name": "Modern fashion",
                                "tag_id": "urn:tag:style:modern",
                                "subtype": "urn:tag:style",
                            }
                        ]
                    }
                },
            ],
        ) as request:
            result = qloo.run_capability(
                QlooCapabilityRequest(capability="taste", query="Example")
            )

        self.assertEqual(result["results"][0]["entity_id"], "urn:tag:style:modern")
        insight_params = request.call_args_list[1].args[1]
        self.assertEqual(insight_params["filter.type"], "urn:tag")
        self.assertEqual(insight_params["signal.interests.entities"], "entity-1")

    def test_recommendations_use_selected_result_category_and_provider_affinity(self) -> None:
        with patch.object(
            qloo,
            "_request",
            side_effect=[
                {"results": [{"name": "Example", "entity_id": "entity-1"}]},
                {
                    "results": {
                        "entities": [
                            {
                                "name": "Recommended",
                                "entity_id": "entity-2",
                                "query": {"affinity": 0.82, "affinity_rank": 0.73},
                            }
                        ]
                    }
                },
            ],
        ) as request:
            result = qloo.run_capability(
                QlooCapabilityRequest(
                    capability="recommendations",
                    query="Example",
                    result_category="artist",
                )
            )

        self.assertEqual(result["results"][0]["name"], "Recommended")
        self.assertEqual(result["results"][0]["affinity"], 0.82)
        self.assertEqual(result["results"][0]["affinity_rank"], 0.73)
        self.assertEqual(request.call_args_list[1].args[1]["filter.type"], "urn:entity:artist")

    def test_locality_uses_location_insights_and_heatmap_filter(self) -> None:
        with patch.object(
            qloo,
            "_request",
            side_effect=[
                {"results": [{"name": "Example", "entity_id": "entity-1"}]},
                {"results": {"entities": [{"name": "Nearby", "entity_id": "nearby-1"}]}},
                {
                    "results": {
                        "heatmap": [
                            {
                                "location": {"latitude": 40.7, "longitude": -73.9},
                                "query": {"affinity": 0.8, "affinity_rank": 0.7},
                            }
                        ]
                    }
                },
            ],
        ) as request:
            result = qloo.run_capability(
                QlooCapabilityRequest(
                    capability="locality",
                    query="Example",
                    location="New York",
                    result_category="place",
                )
            )

        self.assertEqual(result["results"][0]["name"], "Nearby")
        self.assertEqual(result["heatmap"][0]["affinity_rank"], 0.7)
        self.assertEqual(request.call_args_list[1].args[1]["signal.location.query"], "New York")
        self.assertEqual(request.call_args_list[2].args[1]["filter.type"], "urn:heatmap")
        self.assertEqual(request.call_args_list[2].args[1]["filter.location.query"], "New York")

    def test_grounding_includes_explainability_and_snapshot_is_versioned(self) -> None:
        for capability in ("grounding", "on_device"):
            with self.subTest(capability=capability), patch.object(
                qloo,
                "_request",
                side_effect=[
                    {"results": [{"name": "Example", "entity_id": "entity-1"}]},
                    {
                        "results": {
                            "entities": [
                                {
                                    "name": "Recommended",
                                    "entity_id": "entity-2",
                                    "query": {"affinity": 0.9, "explainability": {"signal": 0.8}},
                                }
                            ]
                        }
                    },
                ],
            ) as request:
                result = qloo.run_capability(
                    QlooCapabilityRequest(capability=capability, query="Example")
                )

            if capability == "grounding":
                self.assertEqual(result["grounded_options"][0]["entity"]["explainability"], {"signal": 0.8})
                self.assertTrue(request.call_args_list[1].args[1]["feature.explainability"])
            else:
                self.assertEqual(result["snapshot"]["schema_version"], 1)
                self.assertEqual(result["snapshot"]["items"][0]["name"], "Recommended")


if __name__ == "__main__":
    unittest.main()
