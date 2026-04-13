from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Optional

from pydantic import BaseModel

# ContextVar for correlation ID propagation (async-safe)
_correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class RequestContext(BaseModel):
    """Structured context for a single request lifecycle."""

    request_id: str
    method: str
    path: str
    user_id: Optional[str] = None
    started_at: float = 0.0
    extra: dict = {}


def correlation_id() -> str:
    """Return the current correlation ID, generating one if none is set."""
    cid = _correlation_id_var.get(None)
    if cid is None:
        cid = uuid.uuid4().hex[:12]
        _correlation_id_var.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    """Store a correlation ID in the current async context."""
    _correlation_id_var.set(cid)


def clear_context() -> None:
    """Reset the correlation ID so the next call generates a fresh one."""
    _correlation_id_var.set(None)
