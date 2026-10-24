"""Privacy-safe request and upstream-operation logging."""

import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator

logger = logging.getLogger("kloppy.observability")
request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


@dataclass
class ExternalCall:
    status_code: int | None = None


@contextmanager
def log_external_call(provider: str, operation: str) -> Iterator[ExternalCall]:
    """Log a provider call without request data, credentials, URLs, or response bodies."""
    started_at = time.perf_counter()
    call = ExternalCall()
    request_id = request_id_context.get()
    logger.info(
        "external_call_started request_id=%s provider=%s operation=%s",
        request_id,
        provider,
        operation,
    )
    try:
        yield call
    except Exception as error:
        response = getattr(error, "response", None)
        status_code = getattr(
            response,
            "status_code",
            getattr(error, "status_code", call.status_code),
        )
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.warning(
            "external_call_failed request_id=%s provider=%s operation=%s status_code=%s duration_ms=%.1f error_type=%s",
            request_id,
            provider,
            operation,
            status_code if status_code is not None else "-",
            duration_ms,
            type(error).__name__,
        )
        raise
    else:
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "external_call_succeeded request_id=%s provider=%s operation=%s status_code=%s duration_ms=%.1f",
            request_id,
            provider,
            operation,
            call.status_code if call.status_code is not None else "-",
            duration_ms,
        )
