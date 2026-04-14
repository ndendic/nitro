"""nitro.plugins — Plugin base class with lifecycle hooks."""

from __future__ import annotations

import enum
from typing import Any, ClassVar, Dict, List, Optional


class PluginState(enum.Enum):
    """Lifecycle state of a plugin instance."""

    REGISTERED = "registered"
    SETTING_UP = "setting_up"
    ACTIVE = "active"
    TEARING_DOWN = "tearing_down"
    TORN_DOWN = "torn_down"
    ERROR = "error"


class Plugin:
    """Base class for Nitro plugins.

    Subclass this and override ``setup`` / ``teardown`` to hook into the
    application lifecycle.  The ``name`` class variable is **required** and
    must be unique across the registry.

    Example::

        class CachePlugin(Plugin):
            name = "cache"
            version = "0.1.0"
            description = "Redis cache layer"
            dependencies = ["config"]

            async def setup(self, app, **config):
                import redis.asyncio as redis
                app.ctx.cache = redis.from_url(config.get("url", "redis://localhost"))

            async def teardown(self, app):
                await app.ctx.cache.close()
    """

    name: ClassVar[str] = ""
    version: ClassVar[str] = "0.0.0"
    description: ClassVar[str] = ""
    author: ClassVar[str] = ""
    dependencies: ClassVar[List[str]] = []
    tags: ClassVar[List[str]] = []
    config_schema: ClassVar[Optional[Dict[str, Any]]] = None

    def __init__(self) -> None:
        if not self.name:
            raise ValueError(
                f"{type(self).__name__} must define a non-empty 'name' class variable"
            )
        self.state: PluginState = PluginState.REGISTERED
        self._error: Optional[Exception] = None

    async def setup(self, app: Any, **config: Any) -> None:
        """Called when the application starts.

        Override to initialise services, add middleware, register routes, etc.

        Args:
            app: The web-framework application instance.
            **config: Plugin-specific configuration values.
        """

    async def teardown(self, app: Any) -> None:
        """Called when the application shuts down.

        Override to release resources, close connections, flush buffers.

        Args:
            app: The web-framework application instance.
        """

    def health_check(self) -> Dict[str, Any]:
        """Return a health-check dict for this plugin.

        Override to add richer diagnostics (connection status, queue depth, …).
        """
        return {
            "name": self.name,
            "version": self.version,
            "state": self.state.value,
            "error": str(self._error) if self._error else None,
        }

    def __repr__(self) -> str:
        return f"<Plugin {self.name}@{self.version} [{self.state.value}]>"
