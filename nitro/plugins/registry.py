"""nitro.plugins — Plugin registry with dependency-aware setup."""

from __future__ import annotations

import importlib.metadata
import logging
from typing import Any, Dict, List, Optional, Sequence

from .base import Plugin, PluginState
from .meta import PluginMeta

logger = logging.getLogger("nitro.plugins")

ENTRY_POINT_GROUP = "nitro.plugins"


class PluginError(Exception):
    """Raised on plugin registration, dependency, or lifecycle failures."""


class PluginRegistry:
    """Central registry for Nitro plugins.

    Handles registration, dependency ordering, lifecycle management,
    and entry-point based auto-discovery.
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, plugin: Plugin) -> None:
        """Register a plugin instance.

        Raises ``PluginError`` if a plugin with the same name is already registered.
        """
        if not isinstance(plugin, Plugin):
            raise PluginError(
                f"Expected a Plugin instance, got {type(plugin).__name__}"
            )
        if plugin.name in self._plugins:
            raise PluginError(
                f"Plugin '{plugin.name}' is already registered"
            )
        self._plugins[plugin.name] = plugin
        logger.info("Registered plugin: %s@%s", plugin.name, plugin.version)

    def unregister(self, name: str) -> Plugin:
        """Remove and return a registered plugin by name.

        Raises ``PluginError`` if the plugin is not found or is currently active.
        """
        plugin = self._plugins.get(name)
        if plugin is None:
            raise PluginError(f"Plugin '{name}' is not registered")
        if plugin.state == PluginState.ACTIVE:
            raise PluginError(
                f"Plugin '{name}' is active — tear it down before unregistering"
            )
        del self._plugins[name]
        logger.info("Unregistered plugin: %s", name)
        return plugin

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self, group: str = ENTRY_POINT_GROUP) -> List[str]:
        """Auto-discover plugins from Python entry points.

        Each entry point should resolve to a ``Plugin`` subclass (the class
        itself, not an instance).  The registry instantiates it.

        Returns the names of newly registered plugins.
        """
        discovered: List[str] = []
        eps = importlib.metadata.entry_points()
        # Python 3.12+ returns a SelectableGroups; 3.9–3.11 returns a dict
        group_eps = eps.select(group=group) if hasattr(eps, "select") else eps.get(group, [])
        for ep in group_eps:
            try:
                plugin_cls = ep.load()
                if not (isinstance(plugin_cls, type) and issubclass(plugin_cls, Plugin)):
                    logger.warning(
                        "Entry point %s does not resolve to a Plugin subclass — skipped",
                        ep.name,
                    )
                    continue
                plugin = plugin_cls()
                if plugin.name not in self._plugins:
                    self.register(plugin)
                    discovered.append(plugin.name)
            except Exception as exc:
                logger.warning("Failed to load entry point %s: %s", ep.name, exc)
        return discovered

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, name: str) -> Optional[Plugin]:
        """Return a registered plugin by name, or ``None``."""
        return self._plugins.get(name)

    @property
    def plugins(self) -> List[Plugin]:
        """All registered plugins (insertion order)."""
        return list(self._plugins.values())

    @property
    def names(self) -> List[str]:
        """Names of all registered plugins."""
        return list(self._plugins.keys())

    def metadata(self) -> List[PluginMeta]:
        """Return ``PluginMeta`` for every registered plugin."""
        return [
            PluginMeta(
                name=p.name,
                version=p.version,
                description=p.description,
                author=p.author,
                dependencies=list(p.dependencies),
                tags=list(p.tags),
                config_schema=p.config_schema,
            )
            for p in self._plugins.values()
        ]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _resolve_order(self) -> List[Plugin]:
        """Topological sort of plugins by dependency graph.

        Raises ``PluginError`` on missing dependencies or cycles.
        """
        visited: Dict[str, int] = {}  # 0 = in-progress, 1 = done
        order: List[Plugin] = []

        def visit(name: str, path: Sequence[str] = ()) -> None:
            if name in visited:
                if visited[name] == 0:
                    cycle = " → ".join([*path, name])
                    raise PluginError(f"Circular dependency: {cycle}")
                return
            plugin = self._plugins.get(name)
            if plugin is None:
                raise PluginError(
                    f"Plugin '{path[-1]}' depends on '{name}', which is not registered"
                )
            visited[name] = 0
            for dep in plugin.dependencies:
                visit(dep, (*path, name))
            visited[name] = 1
            order.append(plugin)

        for name in self._plugins:
            if name not in visited:
                visit(name)

        return order

    async def setup_all(
        self,
        app: Any,
        config: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """Set up all registered plugins in dependency order.

        Args:
            app: The web-framework application instance.
            config: Per-plugin config dicts keyed by plugin name.
        """
        config = config or {}
        order = self._resolve_order()
        for plugin in order:
            plugin_config = config.get(plugin.name, {})
            plugin.state = PluginState.SETTING_UP
            try:
                await plugin.setup(app, **plugin_config)
                plugin.state = PluginState.ACTIVE
                logger.info("Plugin '%s' set up successfully", plugin.name)
            except Exception as exc:
                plugin.state = PluginState.ERROR
                plugin._error = exc
                logger.error("Plugin '%s' setup failed: %s", plugin.name, exc)
                raise PluginError(
                    f"Failed to set up plugin '{plugin.name}': {exc}"
                ) from exc

    async def teardown_all(self, app: Any) -> None:
        """Tear down all active plugins in reverse dependency order."""
        order = self._resolve_order()
        errors: List[str] = []
        for plugin in reversed(order):
            if plugin.state != PluginState.ACTIVE:
                continue
            plugin.state = PluginState.TEARING_DOWN
            try:
                await plugin.teardown(app)
                plugin.state = PluginState.TORN_DOWN
                logger.info("Plugin '%s' torn down", plugin.name)
            except Exception as exc:
                plugin.state = PluginState.ERROR
                plugin._error = exc
                errors.append(f"{plugin.name}: {exc}")
                logger.error("Plugin '%s' teardown failed: %s", plugin.name, exc)
        if errors:
            raise PluginError(
                f"Teardown errors: {'; '.join(errors)}"
            )

    def health(self) -> Dict[str, Any]:
        """Aggregate health-check across all plugins."""
        checks = {p.name: p.health_check() for p in self._plugins.values()}
        all_active = all(
            c["state"] == "active" for c in checks.values()
        )
        return {
            "healthy": all_active,
            "plugins": checks,
        }

    def __len__(self) -> int:
        return len(self._plugins)

    def __contains__(self, name: str) -> bool:
        return name in self._plugins

    def __repr__(self) -> str:
        return f"<PluginRegistry [{len(self._plugins)} plugins]>"
