"""nitro.i18n — Internationalization and localization support.

Provides translation catalogs, locale negotiation, message formatting,
and framework integration for multi-language Nitro applications.

Quick start::

    from nitro.i18n import Translations, t

    translations = Translations()
    translations.load_dict("en", {
        "hello": "Hello, {name}!",
        "items": "{count} item|{count} items",
    })
    translations.load_dict("sr", {
        "hello": "Zdravo, {name}!",
        "items": "{count} stavka|{count} stavke|{count} stavki",
    })
    translations.set_locale("sr")

    t("hello", name="Nikola")   # "Zdravo, Nikola!"
    t("items", count=5)         # "5 stavki"

File-based catalogs::

    # locales/en.json: {"hello": "Hello!", "nav.home": "Home"}
    translations.load_dir("locales/")
    translations.set_locale("en")
    t("nav.home")  # "Home"

Sanic integration::

    from sanic import Sanic
    from nitro.i18n import configure_i18n

    app = Sanic("MyApp")
    configure_i18n(app, "locales/", default_locale="en")
    # Locale auto-detected from Accept-Language header
"""

from .catalog import Catalog
from .formatting import pluralize, format_message
from .integration import configure_i18n, get_locale, set_locale
from .translations import Translations, t

__all__ = [
    # Core
    "Translations",
    "Catalog",
    "t",
    # Formatting
    "pluralize",
    "format_message",
    # Integration
    "configure_i18n",
    "get_locale",
    "set_locale",
]
