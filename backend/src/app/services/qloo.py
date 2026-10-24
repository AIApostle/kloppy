"""Server-side Qloo API integration and cultural-intelligence operations."""

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from ..config import settings
from ..observability import log_external_call
from ..schemas.qloo import QlooCapabilityRequest

logger = logging.getLogger(__name__)

ENTITY_TYPES = {
    "place": "urn:entity:place",
    "artist": "urn:entity:artist",
    "brand": "urn:entity:brand",
    "book": "urn:entity:book",
    "movie": "urn:entity:movie",
    "destination": "urn:entity:destination",
    "person": "urn:entity:person",
    "podcast": "urn:entity:podcast",
    "tv_show": "urn:entity:tv_show",
}
INSIGHT_ENTITY_TYPES = {**ENTITY_TYPES, "destination": "urn:entity:place"}

SAFE_PROPERTY_KEYS = {
    "description",
    "short_description",
    "tagline",
    "image",
    "keywords",
    "genres",
    "genre",
    "notable_work",
    "industries",
    "category",
    "categories",
    "price_level",
    "cuisine",
    "brand_type",
    "products",
    "official_site",
}

INTERPRETATION = (
    "Qloo results are directional cultural-affinity signals. They are not "
    "proof of purchase intent, an individual's identity, or guaranteed outcomes."
)


class QlooConfigurationError(RuntimeError):
    """Raised when Qloo credentials are unavailable."""


class QlooProviderError(RuntimeError):
    """Raised when Qloo cannot complete a request."""


def _request(path: str, params: dict[str, str | int]) -> dict[str, Any]:
    if not settings.qloo_api_key:
        raise QlooConfigurationError("Qloo is not configured on the backend.")

    try:
        with log_external_call("qloo", path) as call:
            response = httpx.get(
                f"{settings.qloo_base_url.rstrip('/')}/{path.lstrip('/')}",
                params=params,
                headers={
                    "X-Api-Key": settings.qloo_api_key,
                    "Accept": "application/json",
                },
                timeout=25,
            )
            call.status_code = response.status_code
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as error:
        logger.warning("Qloo returned HTTP %s for %s", error.response.status_code, path)
        raise QlooProviderError("Qloo could not complete this request.") from error
    except (httpx.HTTPError, ValueError) as error:
        logger.warning("Qloo request failed for %s: %s", path, type(error).__name__)
        raise QlooProviderError("Qloo is temporarily unavailable.") from error

    if not isinstance(payload, dict):
        logger.warning("Qloo returned an unexpected response for %s", path)
        raise QlooProviderError("Qloo returned an unsupported response.")
    return payload


def _entities(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results")
    if isinstance(results, list):
        return [item for item in results if isinstance(item, dict)]
    if isinstance(results, dict):
        entities = results.get("entities")
        if isinstance(entities, list):
            return [item for item in entities if isinstance(item, dict)]
    return []


def _insight_records(payload: dict[str, Any], *, taste_analysis: bool = False) -> list[dict[str, Any]]:
    results = payload.get("results")
    if isinstance(results, dict):
        records = results.get("tags" if taste_analysis else "entities")
        if isinstance(records, list):
            return [item for item in records if isinstance(item, dict)]
    return []


def _heatmap_points(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results")
    points = results.get("heatmap") if isinstance(results, dict) else None
    if not isinstance(points, list):
        return []
    normalized: list[dict[str, Any]] = []
    for rank, point in enumerate(points, start=1):
        if not isinstance(point, dict):
            continue
        location = point.get("location")
        metrics = point.get("query")
        if not isinstance(location, dict):
            location = {}
        if not isinstance(metrics, dict):
            metrics = {}
        normalized.append(
            {
                "rank": rank,
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "geohash": location.get("geohash"),
                "affinity": metrics.get("affinity"),
                "affinity_rank": metrics.get("affinity_rank"),
                "popularity": metrics.get("popularity"),
            }
        )
    return normalized


def _safe_entity(item: dict[str, Any], rank: int) -> dict[str, Any]:
    properties = item.get("properties")
    safe_properties: dict[str, Any] = {}
    if isinstance(properties, dict):
        for key, value in properties.items():
            if key not in SAFE_PROPERTY_KEYS or value is None:
                continue
            if isinstance(value, str):
                safe_properties[key] = value[:1200]
            elif isinstance(value, list):
                safe_properties[key] = [
                    item[:300] if isinstance(item, str) else item
                    for item in value[:12]
                    if isinstance(item, (str, int, float, bool))
                ]
            elif isinstance(value, dict) and key == "image" and isinstance(value.get("url"), str):
                safe_properties[key] = {"url": value["url"][:2048]}
            elif isinstance(value, (int, float, bool)):
                safe_properties[key] = value
    types = item.get("types")
    if not isinstance(types, list):
        types = [
            value
            for value in (item.get("type"), item.get("subtype"))
            if isinstance(value, str)
        ]
    query = item.get("query")
    if not isinstance(query, dict):
        query = {}
    description = (
        item.get("short_description")
        or safe_properties.get("short_description")
        or safe_properties.get("description")
    )
    if isinstance(description, list):
        description = next(
            (
                value.get("value")
                for value in description
                if isinstance(value, dict) and value.get("value")
            ),
            None,
        )
    if not isinstance(description, str):
        description = None
    entity_id = (
        item.get("entity_id")
        or item.get("tag_id")
        or item.get("tag_value")
        or item.get("id")
    )
    return {
        "name": item.get("name"),
        "entity_id": str(entity_id) if entity_id is not None else None,
        "types": types[:8],
        "rank": rank,
        "popularity": (
            item.get("popularity") if item.get("popularity") is not None else query.get("popularity")
        ),
        "affinity": (
            item.get("affinity")
            if item.get("affinity") is not None
            else item.get("score")
            if item.get("score") is not None
            else query.get("affinity")
        ),
        "affinity_rank": query.get("affinity_rank"),
        "description": description[:1200] if description else None,
        "properties": safe_properties,
        "tags": item.get("tags", [])[:12] if isinstance(item.get("tags"), list) else [],
        "explainability": query.get("explainability"),
    }


def search_entities(
    query: str,
    category: str = "brand",
    take: int = 8,
) -> list[dict[str, Any]]:
    """Resolve a name to Qloo entities, including selected cultural attributes."""
    safe_query = query.strip()[:160]
    if not safe_query:
        raise ValueError("Enter a name or interest to search.")
    params: dict[str, str | int] = {"query": safe_query, "take": max(1, min(take, 20))}
    entity_type = ENTITY_TYPES.get(category)
    if entity_type:
        params["types"] = entity_type
    payload = _request("/search", params)
    return [_safe_entity(item, index + 1) for index, item in enumerate(_entities(payload))]


def enrich_entities(entity_ids: list[str]) -> list[dict[str, Any]]:
    """Fetch full Qloo entity metadata for resolved entity IDs."""
    safe_ids = list(dict.fromkeys(value.strip()[:160] for value in entity_ids if value.strip()))[:8]
    if not safe_ids:
        raise ValueError("Provide at least one Qloo entity ID to enrich.")
    payload = _request("/entities", {"entity_ids": ",".join(safe_ids)})
    return [_safe_entity(item, index + 1) for index, item in enumerate(_entities(payload))]


def _resolve_seeds(payload: QlooCapabilityRequest) -> tuple[list[str], list[dict[str, Any]]]:
    entity_ids = [item.strip()[:160] for item in payload.entity_ids if item.strip()][:8]
    resolved: list[dict[str, Any]] = []
    if entity_ids:
        return entity_ids, resolved

    queries: list[str] = []
    if payload.query and payload.query.strip():
        queries.append(payload.query.strip())
    queries.extend(item.strip() for item in payload.interests if item.strip())
    unique_queries = list(dict.fromkeys(queries))[:8]
    for query in unique_queries:
        matches = search_entities(query, payload.entity_category, take=3)
        resolved.extend(matches[:3])
    resolved = resolved[:8]
    entity_ids = list(
        dict.fromkeys(
            str(item["entity_id"])
            for item in resolved
            if isinstance(item.get("entity_id"), str) and item["entity_id"]
        )
    )[:8]
    return entity_ids, resolved


def _insights(
    entity_ids: list[str],
    result_category: str,
    location: str | None,
    take: int,
    *,
    explainability: bool = False,
    taste_analysis: bool = False,
) -> list[dict[str, Any]]:
    params: dict[str, str | int] = {
        "filter.type": "urn:tag" if taste_analysis else INSIGHT_ENTITY_TYPES[result_category],
        "take": max(1, min(take, 20)),
    }
    if entity_ids:
        params["signal.interests.entities"] = ",".join(entity_ids)
    if location and location.strip():
        params["signal.location.query"] = location.strip()[:160]
    if explainability:
        params["feature.explainability"] = "true"
    response = _request("/v2/insights", params)
    return [
        _safe_entity(item, index + 1)
        for index, item in enumerate(_insight_records(response, taste_analysis=taste_analysis))
    ]


def _heatmap(
    entity_ids: list[str],
    location: str,
    take: int,
) -> list[dict[str, Any]]:
    params: dict[str, str | int] = {
        "filter.type": "urn:heatmap",
        "filter.location.query": location.strip()[:160],
    }
    if entity_ids:
        params["signal.interests.entities"] = ",".join(entity_ids)
    points = _heatmap_points(_request("/v2/insights", params))
    return points[: max(1, min(take, 100))]


def run_capability(payload: QlooCapabilityRequest) -> dict[str, Any]:
    """Run one of Kloppy's six Qloo-powered cultural-intelligence capabilities."""
    capability = payload.capability
    if capability == "enrichment":
        if not payload.query or not payload.query.strip():
            raise ValueError("Enter a record name to enrich.")
        matches = search_entities(payload.query, payload.entity_category, payload.take)
        ids = [str(item["entity_id"]) for item in matches if item.get("entity_id")]
        details = enrich_entities(ids) if ids else []
        results = details or matches
        return {
            "capability": capability,
            "source": "Qloo Search and Entities APIs",
            "query_context": payload.model_dump(exclude={"entity_ids"}),
            "resolved_entities": matches,
            "results": results,
            "interpretation": INTERPRETATION,
        }

    if capability == "locality" and not (payload.location and payload.location.strip()):
        raise ValueError("Enter a location to explore nearby cultural affinity.")

    entity_ids, resolved = _resolve_seeds(payload)
    if capability != "locality" and not entity_ids:
        raise ValueError("Enter a starting entity or at least one interest.")
    if capability == "locality" and not entity_ids:
        raise ValueError("Enter at least one interest or entity to map in this location.")

    if capability == "taste":
        results = _insights(
            entity_ids,
            payload.result_category,
            payload.location,
            payload.take,
            taste_analysis=True,
        )
        source = "Qloo Insights API taste analysis"
    else:
        results = _insights(
            entity_ids,
            payload.result_category,
            payload.location if capability == "locality" else None,
            payload.take,
            explainability=capability == "grounding",
        )
        source = "Qloo API cultural affinity insights"

    response: dict[str, Any] = {
        "capability": capability,
        "source": source,
        "query_context": payload.model_dump(exclude={"entity_ids"}),
        "resolved_entities": resolved,
        "results": results,
        "ranking_basis": (
            "Qloo provider ordering; a numeric affinity score is shown only when Qloo supplies one."
        ),
        "interpretation": INTERPRETATION,
    }
    if capability == "locality":
        response["heatmap"] = _heatmap(entity_ids, payload.location or "", payload.take)
    if capability == "grounding":
        response["grounded_options"] = [
            {"rank": item["rank"], "entity": item, "source": "Qloo API"}
            for item in results
        ]
    if capability == "on_device":
        response["snapshot"] = {
            "schema_version": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "source": source,
            "query_context": response["query_context"],
            "items": results,
            "interpretation": INTERPRETATION,
        }
    return response


def agent_grounding_options(query: str, category: str = "brand", take: int = 8) -> dict[str, Any]:
    """Return Qloo-ranked options for the agent with explicit evidence boundaries."""
    payload = QlooCapabilityRequest(
        capability="grounding",
        query=query,
        entity_category=category if category in ENTITY_TYPES else "brand",
        result_category=category if category in ENTITY_TYPES else "brand",
        take=max(1, min(take, 20)),
    )
    return run_capability(payload)
