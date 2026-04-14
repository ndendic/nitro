"""
nitro.multitenancy — Async-safe tenant context management.

Uses ``contextvars.ContextVar`` so tenant context is correctly isolated in
async environments (e.g. asyncio, Sanic, FastAPI) where
``threading.local`` would share state across coroutines running in the
same thread.

Usage::

    # Set context for the current async task / thread
    TenantContext.set("tenant-uuid")

    # Read it later
    current_id = TenantContext.get()   # → "tenant-uuid"

    # Use as a context manager
    with TenantContext.scope("other-tenant"):
        ...  # context is "other-tenant" here
    # back to the previous value after the block
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Generator, Optional

_tenant_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "nitro_current_tenant", default=None
)


class TenantContext:
    """Thread-safe (and async-safe) current-tenant store.

    All methods are class-level — there is no state on the class itself;
    everything lives in the ``ContextVar``.
    """

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    @classmethod
    def set(cls, tenant_id: str) -> contextvars.Token:
        """Set the current tenant for the running async task / thread.

        Args:
            tenant_id: The tenant identifier to store.

        Returns:
            A ``contextvars.Token`` that can be used to restore the
            previous value via :pymeth:`contextvars.ContextVar.reset`.
        """
        return _tenant_var.set(tenant_id)

    @classmethod
    def get(cls) -> Optional[str]:
        """Return the current tenant ID, or ``None`` if not set."""
        return _tenant_var.get()

    @classmethod
    def clear(cls) -> None:
        """Clear the current tenant context (resets to ``None``)."""
        _tenant_var.set(None)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    @classmethod
    @contextmanager
    def scope(cls, tenant_id: str) -> Generator[None, None, None]:
        """Context manager that sets a tenant for the duration of the block.

        The previous value is restored when the block exits, even if an
        exception is raised.

        Args:
            tenant_id: The tenant to activate within the block.

        Example::

            with TenantContext.scope("acme"):
                # current tenant is "acme"
                ...
            # previous tenant is restored
        """
        token = _tenant_var.set(tenant_id)
        try:
            yield
        finally:
            _tenant_var.reset(token)
