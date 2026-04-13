"""Translations — multi-locale translation manager with global shortcut."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import Catalog
from .formatting import format_message, pluralize


class Translations:
    """Multi-locale translation manager.

    Manages catalogs for multiple locales, handles fallback chains,
    and provides the ``t()`` shortcut for translating messages.

    Usage::

        tr = Translations(default_locale="en", fallback_locale="en")
        tr.load_dict("en", {"greeting": "Hello, {name}!"})
        tr.load_dict("sr", {"greeting": "Zdravo, {name}!"})

        tr.set_locale("sr")
        tr.translate("greeting", name="Nikola")  # "Zdravo, Nikola!"

    The module-level ``t()`` function delegates to the last created
    Translations instance, enabling concise usage::

        from nitro.i18n import Translations, t
        Translations().load_dict("en", {"hi": "Hi!"})
        t("hi")  # "Hi!"
    """

    _current: Translations | None = None

    def __init__(
        self,
        default_locale: str = "en",
        fallback_locale: str | None = None,
    ) -> None:
        self._catalogs: dict[str, Catalog] = {}
        self._locale = default_locale
        self._fallback = fallback_locale or default_locale
        Translations._current = self

    @property
    def locale(self) -> str:
        """The currently active locale."""
        return self._locale

    @property
    def fallback_locale(self) -> str:
        """The fallback locale used when a key is missing."""
        return self._fallback

    @property
    def available_locales(self) -> list[str]:
        """List of locales with loaded catalogs."""
        return list(self._catalogs.keys())

    def set_locale(self, locale: str) -> None:
        """Set the active locale."""
        self._locale = locale

    def load_dict(self, locale: str, messages: dict[str, Any]) -> None:
        """Load translations from a dictionary.

        Nested dicts are flattened with dot notation::

            load_dict("en", {"nav": {"home": "Home"}})
            # Key: "nav.home"
        """
        catalog = Catalog.from_dict(locale, messages)
        if locale in self._catalogs:
            self._catalogs[locale].merge(catalog)
        else:
            self._catalogs[locale] = catalog

    def load_json(self, locale: str, path: str | Path) -> None:
        """Load translations from a JSON file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.load_dict(locale, data)

    def load_dir(self, directory: str | Path) -> None:
        """Load all JSON translation files from a directory.

        File names become locale codes: ``en.json`` → locale ``"en"``,
        ``sr-Latn.json`` → locale ``"sr-Latn"``.
        """
        dir_path = Path(directory)
        for file in sorted(dir_path.glob("*.json")):
            locale = file.stem
            self.load_json(locale, file)

    def translate(
        self,
        key: str,
        *,
        locale: str | None = None,
        count: int | None = None,
        default: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Translate a key with optional pluralization and formatting.

        Lookup order:
        1. Active locale catalog
        2. Fallback locale catalog
        3. Default value
        4. The key itself (as last resort)

        Args:
            key: The translation key.
            locale: Override the active locale for this call.
            count: If provided, triggers pluralization.
            default: Fallback if the key is missing everywhere.
            **kwargs: Format arguments for the message template.
        """
        active = locale or self._locale
        message = self._lookup(key, active)

        if message is None and active != self._fallback:
            message = self._lookup(key, self._fallback)

        if message is None:
            return default if default is not None else key

        if count is not None:
            message = pluralize(message, count, locale=active)

        if kwargs:
            message = format_message(message, **kwargs)

        return message

    def has_key(self, key: str, locale: str | None = None) -> bool:
        """Check if a key exists in the given or active locale."""
        loc = locale or self._locale
        catalog = self._catalogs.get(loc)
        return catalog is not None and catalog.has(key)

    def _lookup(self, key: str, locale: str) -> str | None:
        catalog = self._catalogs.get(locale)
        if catalog is None:
            return None
        return catalog.get(key)

    @classmethod
    def get_current(cls) -> Translations | None:
        """Get the current global Translations instance."""
        return cls._current

    @classmethod
    def reset(cls) -> None:
        """Reset the global instance — for testing."""
        cls._current = None


def t(
    key: str,
    *,
    locale: str | None = None,
    count: int | None = None,
    default: str | None = None,
    **kwargs: Any,
) -> str:
    """Global translation shortcut.

    Delegates to the most recently created Translations instance.

    Raises RuntimeError if no Translations instance has been created.
    """
    current = Translations.get_current()
    if current is None:
        raise RuntimeError(
            "No Translations instance created. "
            "Call Translations() before using t()."
        )
    return current.translate(
        key, locale=locale, count=count, default=default, **kwargs
    )
