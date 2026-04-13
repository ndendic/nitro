"""Framework integration helpers for nitro.settings."""

from __future__ import annotations

from typing import TypeVar

from .base import AppSettings
from .registry import SettingsRegistry

T = TypeVar("T", bound=AppSettings)


def configure_settings(app: object, settings_cls: type[T], **kwargs: object) -> T:
    """Configure settings for a web framework app.

    Creates the settings instance, registers it in the global registry,
    and attaches it to the app context.

    Supports Sanic (app.ctx.settings) and generic apps (app.state.settings).

    Usage::

        from sanic import Sanic
        from nitro.settings import configure_settings

        app = Sanic("MyApp")
        settings = configure_settings(app, MySettings, env="production")

        # Access later
        settings = app.ctx.settings

    Args:
        app: The web framework application instance.
        settings_cls: The AppSettings subclass to instantiate.
        **kwargs: Override values passed to the settings constructor.

    Returns:
        The configured settings instance.
    """
    settings = settings_cls(**kwargs)

    # Register in global registry
    registry = SettingsRegistry()
    registry.register(settings)

    # Attach to app context
    if hasattr(app, "ctx"):
        # Sanic
        app.ctx.settings = settings  # type: ignore[attr-defined]
    elif hasattr(app, "state"):
        # Starlette/FastAPI
        app.state.settings = settings  # type: ignore[attr-defined]
    else:
        # Generic fallback
        app.settings = settings  # type: ignore[attr-defined]

    return settings
