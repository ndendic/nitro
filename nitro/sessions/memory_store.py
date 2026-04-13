"""
In-memory session store with TTL support.

Suitable for development and single-process deployments.
Sessions are lost on process restart.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from .base import SessionInterface


class MemorySessionStore(SessionInterface):
    """In-process dict-based session store with TTL expiration.

    Args:
        ttl: Session time-to-live in seconds (default: 3600 = 1 hour).
             Set to 0 for sessions that never expire.

    Example::

        store = MemorySessionStore(ttl=1800)  # 30 minutes
    """

    def __init__(self, ttl: int = 3600):
        self._ttl = ttl
        # {session_id: (data_dict, expires_at_timestamp)}
        self._store: dict[str, tuple[dict[str, Any], float]] = {}

    async def load(self, session_id: str) -> Optional[dict[str, Any]]:
        entry = self._store.get(session_id)
        if entry is None:
            return None
        data, expires_at = entry
        if self._ttl > 0 and time.monotonic() > expires_at:
            del self._store[session_id]
            return None
        return dict(data)  # Return a copy

    async def save(self, session_id: str, data: dict[str, Any]) -> None:
        expires_at = time.monotonic() + self._ttl if self._ttl > 0 else float("inf")
        self._store[session_id] = (dict(data), expires_at)

    async def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    async def exists(self, session_id: str) -> bool:
        entry = self._store.get(session_id)
        if entry is None:
            return False
        _, expires_at = entry
        if self._ttl > 0 and time.monotonic() > expires_at:
            del self._store[session_id]
            return False
        return True

    async def clear_all(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns the number of sessions removed.

        Call this periodically (e.g., via nitro.scheduler) to prevent
        memory growth from abandoned sessions.
        """
        if self._ttl <= 0:
            return 0
        now = time.monotonic()
        expired = [sid for sid, (_, exp) in self._store.items() if now > exp]
        for sid in expired:
            del self._store[sid]
        return len(expired)

    @property
    def count(self) -> int:
        """Number of sessions currently stored (including potentially expired)."""
        return len(self._store)
