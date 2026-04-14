"""
nitro.plugins — Plugin/extension system for Nitro applications.

Provides:
- Plugin           : Base class for all Nitro plugins (lifecycle hooks)
- PluginMeta       : Pydantic model for plugin metadata
- PluginRegistry   : Singleton registry for discovering and managing plugins
- PluginError      : Exception for plugin-related failures
- PluginState      : Enum for plugin lifecycle state

Quick start::

    from nitro.plugins import Plugin, PluginRegistry

    class MyPlugin(Plugin):
        name = "my-plugin"
        version = "1.0.0"
        description = "Adds custom functionality"

        async def setup(self, app, **config):
            app.ctx.my_service = MyService(**config)

        async def teardown(self, app):
            await app.ctx.my_service.close()

    # Register and use
    registry = PluginRegistry()
    registry.register(MyPlugin())
    await registry.setup_all(app, config={"my-plugin": {"key": "value"}})

    # Auto-discover from entry points
    registry.discover()  # finds plugins registered as 'nitro.plugins' entry points

Dependency ordering::

    class AuthPlugin(Plugin):
        name = "auth"
        version = "1.0.0"

    class AdminPlugin(Plugin):
        name = "admin"
        version = "1.0.0"
        dependencies = ["auth"]  # auth is set up before admin

    registry = PluginRegistry()
    registry.register(AuthPlugin())
    registry.register(AdminPlugin())
    await registry.setup_all(app)  # auth → admin (topological order)
"""

from .base import Plugin, PluginState
from .meta import PluginMeta
from .registry import PluginError, PluginRegistry

__all__ = [
    "Plugin",
    "PluginMeta",
    "PluginRegistry",
    "PluginError",
    "PluginState",
]
