"""
audit_context — context manager for propagating actor/metadata in a block.

Uses ``contextvars`` for thread-safe (and async-safe) propagation.  Nested
calls are supported — the inner context overrides the outer one for the
duration of the inner block, then the outer context is restored.
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from .trail import AuditTrail


# Context variables — set to None when no audit context is active.
_ctx_trail: contextvars.ContextVar[Optional[AuditTrail]] = contextvars.ContextVar(
    "_audit_trail", default=None
)
_ctx_actor: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "_audit_actor", default=None
)
_ctx_metadata: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "_audit_metadata", default=None
)


@contextmanager
def audit_context(
    trail: AuditTrail,
    actor: str = "system",
    metadata: Optional[Dict[str, Any]] = None,
) -> Generator[AuditTrail, None, None]:
    """Context manager that sets the current audit trail, actor, and metadata.

    Within the block, ``get_audit_trail()``, ``get_current_actor()``, and
    ``get_current_metadata()`` will return the configured values.  Nesting is
    supported — inner blocks temporarily override the outer values and restore
    them on exit.

    Args:
        trail: The ``AuditTrail`` to activate for this block.
        actor: Actor identifier to associate with all audit entries in
            this block.
        metadata: Additional metadata to merge into entries recorded
            inside this block.

    Yields:
        The *trail* argument, for convenient use in ``with`` statements::

            with audit_context(trail, actor="user:42") as t:
                t.record_create(...)

    Example::

        trail = AuditTrail()
        with audit_context(trail, actor="user:7", metadata={"ip": "1.2.3.4"}):
            # any code here can call get_current_actor() → "user:7"
            actor = get_current_actor()
    """
    token_trail = _ctx_trail.set(trail)
    token_actor = _ctx_actor.set(actor)
    token_metadata = _ctx_metadata.set(metadata or {})
    try:
        yield trail
    finally:
        _ctx_trail.reset(token_trail)
        _ctx_actor.reset(token_actor)
        _ctx_metadata.reset(token_metadata)


def get_audit_trail() -> Optional[AuditTrail]:
    """Return the currently active ``AuditTrail``, or ``None``.

    Returns ``None`` when called outside an ``audit_context`` block.
    """
    return _ctx_trail.get()


def get_current_actor() -> Optional[str]:
    """Return the actor set by the enclosing ``audit_context``, or ``None``."""
    return _ctx_actor.get()


def get_current_metadata() -> Optional[Dict[str, Any]]:
    """Return the metadata dict set by the enclosing ``audit_context``, or ``None``."""
    return _ctx_metadata.get()
