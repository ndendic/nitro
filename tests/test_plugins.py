"""
Tests for nitro.plugins — plugin/extension system.

Covers:
- Plugin base class: name requirement, lifecycle state, health check, repr
- PluginMeta: validation, defaults, serialization
- PluginRegistry: register, unregister, get, queries, len, contains
- Dependency resolution: topological ordering, missing deps, cycles
- Lifecycle: setup_all, teardown_all, error handling, state transitions
- Discovery: entry-point mocking
- Health: aggregate health check
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from nitro.plugins import (
    Plugin,
    PluginError,
    PluginMeta,
    PluginRegistry,
    PluginState,
)


# ---------------------------------------------------------------------------
# Test Plugin Subclasses
# ---------------------------------------------------------------------------


class AlphaPlugin(Plugin):
    name = "alpha"
    version = "1.0.0"
    description = "First plugin"
    author = "test"
    tags = ["core"]

    def __init__(self):
        super().__init__()
        self.setup_called = False
        self.teardown_called = False
        self.setup_config: Dict[str, Any] = {}

    async def setup(self, app, **config):
        self.setup_called = True
        self.setup_config = config

    async def teardown(self, app):
        self.teardown_called = True


class BetaPlugin(Plugin):
    name = "beta"
    version = "2.0.0"
    description = "Depends on alpha"
    dependencies = ["alpha"]

    def __init__(self):
        super().__init__()
        self.setup_called = False
        self.teardown_called = False

    async def setup(self, app, **config):
        self.setup_called = True

    async def teardown(self, app):
        self.teardown_called = True


class GammaPlugin(Plugin):
    name = "gamma"
    version = "0.1.0"
    dependencies = ["beta"]

    def __init__(self):
        super().__init__()
        self.setup_called = False

    async def setup(self, app, **config):
        self.setup_called = True


class FailingPlugin(Plugin):
    name = "failing"
    version = "0.0.1"

    async def setup(self, app, **config):
        raise RuntimeError("setup exploded")


class FailingTeardownPlugin(Plugin):
    name = "fail-teardown"
    version = "0.0.1"

    async def setup(self, app, **config):
        pass

    async def teardown(self, app):
        raise RuntimeError("teardown exploded")


class NoNamePlugin(Plugin):
    pass


class CycleAPlugin(Plugin):
    name = "cycle-a"
    dependencies = ["cycle-b"]


class CycleBPlugin(Plugin):
    name = "cycle-b"
    dependencies = ["cycle-a"]


# ---------------------------------------------------------------------------
# TestPlugin
# ---------------------------------------------------------------------------


class TestPlugin:
    def test_requires_name(self):
        with pytest.raises(ValueError, match="non-empty 'name'"):
            NoNamePlugin()

    def test_initial_state(self):
        p = AlphaPlugin()
        assert p.state == PluginState.REGISTERED
        assert p._error is None

    def test_health_check(self):
        p = AlphaPlugin()
        h = p.health_check()
        assert h["name"] == "alpha"
        assert h["version"] == "1.0.0"
        assert h["state"] == "registered"
        assert h["error"] is None

    def test_health_check_with_error(self):
        p = AlphaPlugin()
        p.state = PluginState.ERROR
        p._error = RuntimeError("boom")
        h = p.health_check()
        assert h["state"] == "error"
        assert "boom" in h["error"]

    def test_repr(self):
        p = AlphaPlugin()
        assert "alpha@1.0.0" in repr(p)
        assert "registered" in repr(p)

    def test_class_vars_defaults(self):
        p = BetaPlugin()
        assert p.dependencies == ["alpha"]
        assert p.tags == []
        assert p.config_schema is None


# ---------------------------------------------------------------------------
# TestPluginMeta
# ---------------------------------------------------------------------------


class TestPluginMeta:
    def test_required_fields(self):
        meta = PluginMeta(name="test", version="1.0.0")
        assert meta.name == "test"
        assert meta.version == "1.0.0"
        assert meta.description == ""
        assert meta.dependencies == []
        assert meta.tags == []
        assert meta.config_schema is None

    def test_full_fields(self):
        meta = PluginMeta(
            name="auth",
            version="2.1.0",
            description="Auth plugin",
            author="Alice",
            dependencies=["config"],
            tags=["security"],
            config_schema={"secret_key": {"type": "string"}},
        )
        assert meta.author == "Alice"
        assert meta.dependencies == ["config"]
        assert meta.config_schema is not None

    def test_serialization_roundtrip(self):
        meta = PluginMeta(name="x", version="0.1.0", tags=["a", "b"])
        data = meta.model_dump()
        restored = PluginMeta(**data)
        assert restored == meta


# ---------------------------------------------------------------------------
# TestPluginRegistry — Registration
# ---------------------------------------------------------------------------


class TestRegistryRegistration:
    def test_register(self):
        reg = PluginRegistry()
        reg.register(AlphaPlugin())
        assert "alpha" in reg
        assert len(reg) == 1

    def test_register_duplicate_raises(self):
        reg = PluginRegistry()
        reg.register(AlphaPlugin())
        with pytest.raises(PluginError, match="already registered"):
            reg.register(AlphaPlugin())

    def test_register_non_plugin_raises(self):
        reg = PluginRegistry()
        with pytest.raises(PluginError, match="Expected a Plugin instance"):
            reg.register("not a plugin")

    def test_unregister(self):
        reg = PluginRegistry()
        p = AlphaPlugin()
        reg.register(p)
        removed = reg.unregister("alpha")
        assert removed is p
        assert "alpha" not in reg

    def test_unregister_missing_raises(self):
        reg = PluginRegistry()
        with pytest.raises(PluginError, match="not registered"):
            reg.unregister("nope")

    def test_unregister_active_raises(self):
        reg = PluginRegistry()
        p = AlphaPlugin()
        reg.register(p)
        p.state = PluginState.ACTIVE
        with pytest.raises(PluginError, match="active"):
            reg.unregister("alpha")


# ---------------------------------------------------------------------------
# TestPluginRegistry — Queries
# ---------------------------------------------------------------------------


class TestRegistryQueries:
    def test_get_existing(self):
        reg = PluginRegistry()
        p = AlphaPlugin()
        reg.register(p)
        assert reg.get("alpha") is p

    def test_get_missing(self):
        reg = PluginRegistry()
        assert reg.get("missing") is None

    def test_plugins_list(self):
        reg = PluginRegistry()
        a = AlphaPlugin()
        b = BetaPlugin()
        reg.register(a)
        reg.register(b)
        assert reg.plugins == [a, b]

    def test_names_list(self):
        reg = PluginRegistry()
        reg.register(AlphaPlugin())
        reg.register(BetaPlugin())
        assert reg.names == ["alpha", "beta"]

    def test_metadata(self):
        reg = PluginRegistry()
        reg.register(AlphaPlugin())
        metas = reg.metadata()
        assert len(metas) == 1
        assert metas[0].name == "alpha"
        assert metas[0].version == "1.0.0"
        assert metas[0].author == "test"

    def test_contains(self):
        reg = PluginRegistry()
        reg.register(AlphaPlugin())
        assert "alpha" in reg
        assert "nope" not in reg

    def test_len(self):
        reg = PluginRegistry()
        assert len(reg) == 0
        reg.register(AlphaPlugin())
        assert len(reg) == 1

    def test_repr(self):
        reg = PluginRegistry()
        reg.register(AlphaPlugin())
        assert "1 plugins" in repr(reg)


# ---------------------------------------------------------------------------
# TestPluginRegistry — Dependency Resolution
# ---------------------------------------------------------------------------


class TestDependencyResolution:
    def test_no_deps(self):
        reg = PluginRegistry()
        reg.register(AlphaPlugin())
        order = reg._resolve_order()
        assert [p.name for p in order] == ["alpha"]

    def test_linear_chain(self):
        reg = PluginRegistry()
        reg.register(GammaPlugin())
        reg.register(AlphaPlugin())
        reg.register(BetaPlugin())
        order = reg._resolve_order()
        names = [p.name for p in order]
        assert names.index("alpha") < names.index("beta")
        assert names.index("beta") < names.index("gamma")

    def test_missing_dependency_raises(self):
        reg = PluginRegistry()
        reg.register(BetaPlugin())
        with pytest.raises(PluginError, match="not registered"):
            reg._resolve_order()

    def test_circular_dependency_raises(self):
        reg = PluginRegistry()
        reg.register(CycleAPlugin())
        reg.register(CycleBPlugin())
        with pytest.raises(PluginError, match="Circular dependency"):
            reg._resolve_order()


# ---------------------------------------------------------------------------
# TestPluginRegistry — Lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_setup_all(self):
        reg = PluginRegistry()
        a = AlphaPlugin()
        b = BetaPlugin()
        reg.register(a)
        reg.register(b)
        app = MagicMock()
        asyncio.run(reg.setup_all(app))
        assert a.setup_called
        assert b.setup_called
        assert a.state == PluginState.ACTIVE
        assert b.state == PluginState.ACTIVE

    def test_setup_passes_config(self):
        reg = PluginRegistry()
        a = AlphaPlugin()
        reg.register(a)
        app = MagicMock()
        config = {"alpha": {"url": "redis://localhost", "timeout": 30}}
        asyncio.run(reg.setup_all(app, config=config))
        assert a.setup_config == {"url": "redis://localhost", "timeout": 30}

    def test_setup_failure_sets_error_state(self):
        reg = PluginRegistry()
        reg.register(FailingPlugin())
        app = MagicMock()
        with pytest.raises(PluginError, match="setup exploded"):
            asyncio.run(reg.setup_all(app))
        p = reg.get("failing")
        assert p.state == PluginState.ERROR
        assert p._error is not None

    def test_teardown_all(self):
        async def _run():
            reg = PluginRegistry()
            a = AlphaPlugin()
            b = BetaPlugin()
            reg.register(a)
            reg.register(b)
            app = MagicMock()
            await reg.setup_all(app)
            await reg.teardown_all(app)
            assert a.teardown_called
            assert b.teardown_called
            assert a.state == PluginState.TORN_DOWN
            assert b.state == PluginState.TORN_DOWN
        asyncio.run(_run())

    def test_teardown_reverse_order(self):
        async def _run():
            reg = PluginRegistry()
            a = AlphaPlugin()
            b = BetaPlugin()
            reg.register(a)
            reg.register(b)
            app = MagicMock()
            teardown_order: List[str] = []
            original_a_teardown = a.teardown
            original_b_teardown = b.teardown

            async def track_a(app):
                teardown_order.append("alpha")
                await original_a_teardown(app)

            async def track_b(app):
                teardown_order.append("beta")
                await original_b_teardown(app)

            await reg.setup_all(app)
            a.teardown = track_a
            b.teardown = track_b
            await reg.teardown_all(app)
            assert teardown_order == ["beta", "alpha"]
        asyncio.run(_run())

    def test_teardown_skips_non_active(self):
        reg = PluginRegistry()
        a = AlphaPlugin()
        reg.register(a)
        app = MagicMock()
        asyncio.run(reg.teardown_all(app))
        assert not a.teardown_called

    def test_teardown_failure_reports_errors(self):
        async def _run():
            reg = PluginRegistry()
            p = FailingTeardownPlugin()
            reg.register(p)
            app = MagicMock()
            await reg.setup_all(app)
            with pytest.raises(PluginError, match="teardown exploded"):
                await reg.teardown_all(app)
            assert p.state == PluginState.ERROR
        asyncio.run(_run())

    def test_state_transitions(self):
        async def _run():
            reg = PluginRegistry()
            a = AlphaPlugin()
            reg.register(a)
            assert a.state == PluginState.REGISTERED
            app = MagicMock()
            await reg.setup_all(app)
            assert a.state == PluginState.ACTIVE
            await reg.teardown_all(app)
            assert a.state == PluginState.TORN_DOWN
        asyncio.run(_run())


# ---------------------------------------------------------------------------
# TestPluginRegistry — Health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_healthy_when_all_active(self):
        reg = PluginRegistry()
        a = AlphaPlugin()
        reg.register(a)
        app = MagicMock()
        asyncio.run(reg.setup_all(app))
        h = reg.health()
        assert h["healthy"] is True
        assert "alpha" in h["plugins"]

    def test_unhealthy_when_not_all_active(self):
        reg = PluginRegistry()
        a = AlphaPlugin()
        reg.register(a)
        h = reg.health()
        assert h["healthy"] is False

    def test_empty_registry_is_healthy(self):
        reg = PluginRegistry()
        h = reg.health()
        assert h["healthy"] is True
        assert h["plugins"] == {}


# ---------------------------------------------------------------------------
# TestPluginRegistry — Discovery
# ---------------------------------------------------------------------------


class TestDiscovery:
    def test_discover_from_entry_points(self):
        mock_ep = MagicMock()
        mock_ep.name = "alpha"
        mock_ep.load.return_value = AlphaPlugin

        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_ep]

        with patch("nitro.plugins.registry.importlib.metadata.entry_points", return_value=mock_eps):
            reg = PluginRegistry()
            discovered = reg.discover()
            assert discovered == ["alpha"]
            assert "alpha" in reg

    def test_discover_skips_non_plugin_class(self):
        mock_ep = MagicMock()
        mock_ep.name = "bad"
        mock_ep.load.return_value = str

        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_ep]

        with patch("nitro.plugins.registry.importlib.metadata.entry_points", return_value=mock_eps):
            reg = PluginRegistry()
            discovered = reg.discover()
            assert discovered == []

    def test_discover_skips_already_registered(self):
        mock_ep = MagicMock()
        mock_ep.name = "alpha"
        mock_ep.load.return_value = AlphaPlugin

        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_ep]

        with patch("nitro.plugins.registry.importlib.metadata.entry_points", return_value=mock_eps):
            reg = PluginRegistry()
            reg.register(AlphaPlugin())
            discovered = reg.discover()
            assert discovered == []

    def test_discover_handles_load_error(self):
        mock_ep = MagicMock()
        mock_ep.name = "broken"
        mock_ep.load.side_effect = ImportError("no module")

        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_ep]

        with patch("nitro.plugins.registry.importlib.metadata.entry_points", return_value=mock_eps):
            reg = PluginRegistry()
            discovered = reg.discover()
            assert discovered == []
