"""
Abstract base interface for session backends and the SessionData container.
"""

from __future__ import annotations

import secrets
from abc import ABC, abstractmethod
from typing import Any, Optional


class SessionData:
    """A mutable dict-like session object with flash message support.

    This is the object handlers interact with. It wraps a plain dict
    and adds convenience methods for flash messages.

    Attributes:
        session_id: Unique session identifier.
        is_new: True if this session was just created (no prior cookie).
        modified: True if session data was changed since loading.
    """

    def __init__(
        self,
        session_id: str,
        data: dict[str, Any] | None = None,
        *,
        is_new: bool = False,
    ):
        self.session_id = session_id
        self._data: dict[str, Any] = data or {}
        self.is_new = is_new
        self.modified = False
        self._invalidated = False

    # -- Dict-like interface --

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.modified = True

    def __delitem__(self, key: str) -> None:
        del self._data[key]
        self.modified = True

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return True  # Session always truthy even if empty

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def pop(self, key: str, *args: Any) -> Any:
        result = self._data.pop(key, *args)
        self.modified = True
        return result

    def setdefault(self, key: str, default: Any = None) -> Any:
        if key not in self._data:
            self._data[key] = default
            self.modified = True
        return self._data[key]

    def update(self, mapping: dict[str, Any]) -> None:
        self._data.update(mapping)
        self.modified = True

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def clear(self) -> None:
        self._data.clear()
        self.modified = True

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict copy of the session data."""
        return dict(self._data)

    # -- Flash messages --

    def flash(self, message: str, category: str = "info") -> None:
        """Add a one-time flash message.

        Flash messages are consumed on the next request via ``pop_flashes()``.

        Args:
            message: The flash message text.
            category: Message category (e.g. "success", "error", "info", "warning").
        """
        flashes = self._data.setdefault("_flashes", [])
        flashes.append({"message": message, "category": category})
        self.modified = True

    def pop_flashes(self, category: str | None = None) -> list[dict[str, str]]:
        """Consume and return flash messages, optionally filtered by category.

        Args:
            category: If provided, only return messages of this category.

        Returns:
            List of ``{"message": str, "category": str}`` dicts.
        """
        flashes: list[dict[str, str]] = self._data.pop("_flashes", [])
        if flashes:
            self.modified = True
        if category is not None:
            # Return matching; put non-matching back
            matching = [f for f in flashes if f["category"] == category]
            remaining = [f for f in flashes if f["category"] != category]
            if remaining:
                self._data["_flashes"] = remaining
            return matching
        return flashes

    def peek_flashes(self, category: str | None = None) -> list[dict[str, str]]:
        """View flash messages without consuming them.

        Args:
            category: If provided, only return messages of this category.

        Returns:
            List of ``{"message": str, "category": str}`` dicts.
        """
        flashes: list[dict[str, str]] = self._data.get("_flashes", [])
        if category is not None:
            return [f for f in flashes if f["category"] == category]
        return list(flashes)

    # -- Session lifecycle --

    def invalidate(self) -> None:
        """Mark session for destruction. It will be deleted on save."""
        self._invalidated = True
        self._data.clear()
        self.modified = True

    @property
    def is_invalidated(self) -> bool:
        return self._invalidated

    def __repr__(self) -> str:
        return f"<SessionData id={self.session_id!r} keys={list(self._data.keys())} new={self.is_new}>"


def generate_session_id() -> str:
    """Generate a cryptographically secure session ID."""
    return secrets.token_urlsafe(32)


class SessionInterface(ABC):
    """Abstract base for session storage backends.

    Implementations must provide load, save, and delete methods.
    All methods are async to support I/O-bound backends (Redis, DB).
    """

    @abstractmethod
    async def load(self, session_id: str) -> Optional[dict[str, Any]]:
        """Load session data by ID.

        Returns:
            The session data dict, or None if the session doesn't exist
            or has expired.
        """

    @abstractmethod
    async def save(self, session_id: str, data: dict[str, Any]) -> None:
        """Persist session data.

        Args:
            session_id: The session identifier.
            data: The session data dict to store.
        """

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete a session by ID. No-op if session doesn't exist."""

    async def exists(self, session_id: str) -> bool:
        """Check if a session exists. Default: try to load it."""
        return (await self.load(session_id)) is not None

    async def clear_all(self) -> int:
        """Delete all sessions. Returns the count of deleted sessions.

        Optional — backends may override for efficiency. Default raises
        NotImplementedError.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support clear_all()"
        )
