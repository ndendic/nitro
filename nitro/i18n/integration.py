"""Framework integration for nitro.i18n."""

from __future__ import annotations

import contextvars
from pathlib import Path
from typing import Any

from .translations import Translations

# Context var for per-request locale
_request_locale: contextvars.ContextVar[str] = contextvars.ContextVar(
    "nitro_i18n_locale", default=""
)


def get_locale() -> str:
    """Get the current request locale (from context var or global)."""
    loc = _request_locale.get("")
    if loc:
        return loc
    tr = Translations.get_current()
    return tr.locale if tr else "en"


def set_locale(locale: str) -> None:
    """Set the locale for the current request context."""
    _request_locale.set(locale)
    tr = Translations.get_current()
    if tr:
        tr.set_locale(locale)


def parse_accept_language(header: str) -> list[str]:
    """Parse Accept-Language header into ordered locale list.

    Example::

        parse_accept_language("sr-Latn,en;q=0.8,de;q=0.5")
        # ["sr-Latn", "en", "de"]
    """
    if not header:
        return []
    locales: list[tuple[float, str]] = []
    for part in header.split(","):
        part = part.strip()
        if ";q=" in part:
            lang, _, q = part.partition(";q=")
            try:
                quality = float(q)
            except ValueError:
                quality = 0.0
        else:
            lang = part
            quality = 1.0
        locales.append((quality, lang.strip()))
    locales.sort(key=lambda x: x[0], reverse=True)
    return [loc for _, loc in locales]


def negotiate_locale(
    preferred: list[str], available: list[str], default: str = "en"
) -> str:
    """Pick the best locale from available options.

    Tries exact match first, then base language match (e.g., "en-US" → "en").
    """
    available_set = set(available)
    for loc in preferred:
        if loc in available_set:
            return loc
        # Try base language
        base = loc.split("-")[0].split("_")[0]
        if base in available_set:
            return base
    return default


def configure_i18n(
    app: Any,
    locales_dir: str | Path,
    *,
    default_locale: str = "en",
    fallback_locale: str | None = None,
) -> Translations:
    """Configure i18n for a Sanic application.

    Loads translation files from ``locales_dir``, sets up locale negotiation
    middleware from Accept-Language headers, and attaches translations to
    ``app.ctx.translations``.

    Args:
        app: Sanic application instance.
        locales_dir: Directory containing locale JSON files.
        default_locale: Default locale if none negotiated.
        fallback_locale: Fallback for missing keys.

    Returns:
        The configured Translations instance.
    """
    tr = Translations(
        default_locale=default_locale,
        fallback_locale=fallback_locale,
    )
    tr.load_dir(locales_dir)

    # Attach to app
    if hasattr(app, "ctx"):
        app.ctx.translations = tr  # type: ignore[attr-defined]

    # Add middleware for locale negotiation
    if hasattr(app, "on_request"):
        # Sanic middleware
        @app.on_request  # type: ignore[attr-defined]
        async def i18n_middleware(request: Any) -> None:
            header = request.headers.get("accept-language", "")
            preferred = parse_accept_language(header)
            locale = negotiate_locale(
                preferred, tr.available_locales, default_locale
            )
            set_locale(locale)

    return tr
