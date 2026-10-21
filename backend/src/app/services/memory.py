"""User-scoped long-term memory backed by the Walrus Memory Python SDK."""

import hashlib
import logging
from dataclasses import dataclass
from typing import Literal

import httpx
from memwal import MemWalError, MemWalSync, RecallParams

from ..config import settings
from .user_settings import SettingsStoreError, _user_id

logger = logging.getLogger(__name__)
MAX_MEMORIES_PER_SCOPE = 5
MAX_MEMORY_TEXT_LENGTH = 1200


@dataclass(frozen=True)
class AgentMemoryContext:
    """Memory results and availability to ground one agent turn."""

    status: Literal["available", "not_configured", "unavailable"]
    memories: tuple[dict[str, str], ...] = ()


def _is_configured() -> bool:
    return bool(settings.memwal_private_key and settings.memwal_account_id)


def _namespace(user_id: str, campaign_id: str | None = None) -> str:
    """Derive a stable, non-identifying Walrus namespace per user and scope."""
    scope = f"campaign:{campaign_id}" if campaign_id else "workspace"
    digest = hashlib.sha256(f"{user_id}\0{scope}".encode()).hexdigest()[:32]
    return f"kloppy-{digest}"


def _create_client() -> MemWalSync:
    return MemWalSync.create(
        key=settings.memwal_private_key or "",
        account_id=settings.memwal_account_id or "",
        server_url=settings.memwal_server_url,
        namespace="kloppy",
    )


def capture_turn_memory(
    access_token: str | None,
    user_message: str,
    campaign_id: str | None = None,
) -> AgentMemoryContext:
    """Recall relevant private memories and queue facts from the user's message."""
    if not _is_configured():
        return AgentMemoryContext(status="not_configured")
    if not access_token:
        return AgentMemoryContext(status="unavailable")

    client: MemWalSync | None = None
    memories: list[dict[str, str]] = []
    failed = False
    try:
        user_id = _user_id(access_token)
        client = _create_client()
        scopes = [("workspace", _namespace(user_id))]
        if campaign_id:
            scopes.append(("campaign", _namespace(user_id, campaign_id)))

        seen: set[str] = set()
        for scope, namespace in scopes:
            recalled = client.recall(
                RecallParams(
                    query=user_message[:2000],
                    limit=MAX_MEMORIES_PER_SCOPE,
                    namespace=namespace,
                    max_distance=0.8,
                )
            )
            for result in recalled.results:
                text = result.text.strip()[:MAX_MEMORY_TEXT_LENGTH]
                if text and text not in seen:
                    seen.add(text)
                    memories.append({"scope": scope, "text": text})

        if len(user_message.split()) >= 3:
            accepted = client.analyze(
                user_message[:2000],
                namespace=_namespace(user_id, campaign_id),
            )
            logger.info("Walrus accepted %s memory fact jobs", len(accepted.job_ids))
    except (MemWalError, httpx.HTTPError, SettingsStoreError, TypeError, ValueError) as error:
        failed = True
        logger.warning("Walrus memory operation failed: %s", type(error).__name__)
    finally:
        if client is not None:
            try:
                client.close()
            except (MemWalError, httpx.HTTPError, RuntimeError) as error:
                failed = True
                logger.warning("Walrus memory client close failed: %s", type(error).__name__)

    return AgentMemoryContext(
        status="unavailable" if failed and not memories else "available",
        memories=tuple(memories),
    )
