"""
Abstract FlagStore interface and MemoryFlagStore implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Flag


class FlagStore(ABC):
    """Abstract base class for feature flag storage backends.

    All backends must implement the four primitive operations below.
    ``MemoryFlagStore`` is the default; swap in a database-backed store
    for persistence across restarts.
    """

    @abstractmethod
    def get(self, name: str) -> Flag | None:
        """Return the :class:`Flag` with *name*, or ``None`` if not found."""

    @abstractmethod
    def set(self, flag: Flag) -> None:
        """Persist (create or overwrite) *flag*."""

    @abstractmethod
    def delete(self, name: str) -> bool:
        """Delete the flag with *name*.

        Returns:
            ``True`` if the flag existed and was deleted, ``False`` otherwise.
        """

    @abstractmethod
    def list_all(self) -> list[Flag]:
        """Return all stored flags (order is implementation-defined)."""


class MemoryFlagStore(FlagStore):
    """In-process dictionary-backed flag store.

    Suitable for development, testing, or single-process deployments that
    do not require flag persistence across restarts.

    Thread-safety: basic dict operations are effectively atomic in CPython,
    but this store does **not** guarantee strict atomicity for concurrent
    read-modify-write sequences.
    """

    def __init__(self) -> None:
        self._store: dict[str, Flag] = {}

    def get(self, name: str) -> Flag | None:
        """Return the flag with *name*, or ``None``."""
        return self._store.get(name)

    def set(self, flag: Flag) -> None:
        """Store *flag* under its name."""
        self._store[flag.name] = flag

    def delete(self, name: str) -> bool:
        """Remove the flag with *name*.

        Returns:
            ``True`` if the flag existed, ``False`` otherwise.
        """
        if name in self._store:
            del self._store[name]
            return True
        return False

    def list_all(self) -> list[Flag]:
        """Return all flags in insertion order."""
        return list(self._store.values())
