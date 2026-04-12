"""
Nitro Auth — Server-side session store.

Uses Nitro's MemoryRepository for storage with TTL support.
Framework-agnostic: no HTTP primitives here.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Optional

from nitro.domain.repository.memory import MemoryRepository


class Session:
    """A lightweight, in-memory session object.

    Not an Entity — stored directly in MemoryRepository using its
    plain-object (non-SQLModel) storage path.
    """

    def __init__(self, session_id: str, user_id: str, data: dict | None = None):
        self.id = session_id
        self.user_id = user_id
        self.data: dict[str, Any] = data or {}
        self.created_at = datetime.now(timezone.utc)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def delete(self, key: str) -> None:
        self.data.pop(key, None)

    def __repr__(self) -> str:
        return f"<Session id={self.id!r} user_id={self.user_id!r}>"


class SessionStore:
    """In-memory session store with TTL support. Framework-agnostic.

    Uses Nitro's MemoryRepository singleton under the hood.

    Args:
        ttl_seconds: How long each session lives before expiry (default: 1 hour).
    """

    def __init__(self, ttl_seconds: int = 3600):
        self._repo = MemoryRepository()
        self._ttl = ttl_seconds

    def create(self, user_id: str, data: dict | None = None) -> Session:
        """Create a new session for the given user and persist it.

        Returns the new Session with a freshly generated session_id.
        """
        session_id = secrets.token_urlsafe(32)
        session = Session(session_id, user_id, data)
        self._repo.save(session, ttl=self._ttl)
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID. Returns None if missing or expired."""
        return self._repo.get(Session, session_id)

    def destroy(self, session_id: str) -> None:
        """Delete a session. No-op if the session does not exist."""
        session = self.get(session_id)
        if session is not None:
            self._repo.delete(session)

    def refresh(self, session_id: str) -> Optional[Session]:
        """Reset the TTL on an existing session.

        Returns the refreshed Session, or None if it no longer exists.
        """
        session = self.get(session_id)
        if session is not None:
            self._repo.save(session, ttl=self._ttl)
        return session
