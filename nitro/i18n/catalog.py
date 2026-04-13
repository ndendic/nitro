"""Translation catalog — stores messages for a single locale."""

from __future__ import annotations

from typing import Any


class Catalog:
    """A flat key-value store for translated messages in one locale.

    Keys can use dot notation for namespacing (e.g., "nav.home").
    Values are plain strings or plural forms separated by ``|``.

    Usage::

        catalog = Catalog("en")
        catalog.add("hello", "Hello!")
        catalog.add("nav.home", "Home")
        catalog.get("hello")     # "Hello!"
        catalog.get("missing")   # None
    """

    __slots__ = ("locale", "_messages")

    def __init__(self, locale: str) -> None:
        self.locale = locale
        self._messages: dict[str, str] = {}

    def add(self, key: str, value: str) -> None:
        """Add or overwrite a translation key."""
        self._messages[key] = value

    def add_many(self, messages: dict[str, str]) -> None:
        """Add multiple translations at once."""
        self._messages.update(messages)

    def get(self, key: str) -> str | None:
        """Look up a translation by key. Returns None if missing."""
        return self._messages.get(key)

    def has(self, key: str) -> bool:
        """Check whether a key exists in this catalog."""
        return key in self._messages

    def keys(self) -> list[str]:
        """Return all translation keys."""
        return list(self._messages.keys())

    def merge(self, other: Catalog) -> None:
        """Merge another catalog into this one. Other's values win on conflict."""
        self._messages.update(other._messages)

    def __len__(self) -> int:
        return len(self._messages)

    def __repr__(self) -> str:
        return f"Catalog({self.locale!r}, {len(self)} keys)"

    @classmethod
    def from_dict(cls, locale: str, data: dict[str, Any]) -> Catalog:
        """Create a catalog from a nested dict, flattening keys with dots.

        Example::

            Catalog.from_dict("en", {
                "nav": {"home": "Home", "about": "About"},
                "hello": "Hello!"
            })
            # Keys: "nav.home", "nav.about", "hello"
        """
        catalog = cls(locale)
        cls._flatten(data, "", catalog)
        return catalog

    @classmethod
    def _flatten(cls, data: dict[str, Any], prefix: str, catalog: Catalog) -> None:
        for key, value in data.items():
            full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
            if isinstance(value, dict):
                cls._flatten(value, full_key, catalog)
            else:
                catalog.add(full_key, str(value))
