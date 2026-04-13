"""nitro.settings — Composable application configuration with profiles.

Provides environment-aware settings with layered overrides, modular sections,
secret masking, and validation hooks. Built on Pydantic for type safety.

Quick start::

    from nitro.settings import AppSettings, Section, Secret

    class DatabaseSection(Section):
        url: str = "sqlite:///app.db"
        password: Secret = Secret("")
        pool_size: int = 5

    class MySettings(AppSettings):
        db: DatabaseSection = DatabaseSection()
        debug: bool = False

    settings = MySettings()
    settings = MySettings(env="production")  # loads .env.production

    # Safe display (secrets masked)
    print(settings.dump_safe())

Profile-based loading::

    # .env.development
    MY_DEBUG=true
    MY_DB__URL=sqlite:///dev.db

    # .env.production
    MY_DEBUG=false
    MY_DB__URL=postgresql://prod-host/app
    MY_DB__POOL_SIZE=20

    settings = MySettings(env="production")

Settings registry (singleton access)::

    from nitro.settings import SettingsRegistry

    registry = SettingsRegistry()
    registry.register(MySettings())

    # Later, anywhere in the app:
    settings = registry.get(MySettings)

Sanic integration::

    from sanic import Sanic
    from nitro.settings import configure_settings

    app = Sanic("MyApp")
    settings = configure_settings(app, MySettings)
    # settings available via app.ctx.settings
"""

from .base import AppSettings, Secret, Section
from .integration import configure_settings
from .registry import SettingsRegistry
from .validators import cross_validate, validate_range, validate_url

__all__ = [
    # Core
    "AppSettings",
    "Section",
    "Secret",
    # Registry
    "SettingsRegistry",
    # Integration
    "configure_settings",
    # Validators
    "cross_validate",
    "validate_range",
    "validate_url",
]
