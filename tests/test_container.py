"""
Tests for nitro.container — Dependency Injection Container.

Covers:
- Singleton lifecycle (lazy creation, same instance, thread safety)
- Factory lifecycle (new instance each time)
- Scoped lifecycle (same within scope, different across scopes)
- Async factories
- @inject decorator (sync and async functions)
- Scope context manager (enter, resolve, exit/cleanup)
- Override support for testing
- Error cases (missing provider, scoped-outside-scope, bad provider type)
- Lifecycle hooks (on_init, on_destroy)
- Container reset and destroy_singletons
- Sanic integration (mocked)
- Type-based and string-based registration
- has() check
- Container repr
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nitro.container import Container, Factory, Scoped, Singleton, ScopedContainer, inject
from nitro.container.container import _key_name


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


class Counter:
    """Simple stateful service used in tests."""

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self.calls = 0

    def increment(self):
        self.calls += 1
        return self.calls


class DatabasePool:
    """Fake DB pool."""

    def __init__(self, url: str = "sqlite:///:memory:") -> None:
        self.url = url
        self.closed = False

    def close(self):
        self.closed = True


class RequestLogger:
    """Fake logger."""

    instances: list["RequestLogger"] = []

    def __init__(self) -> None:
        RequestLogger.instances.append(self)

    @classmethod
    def reset(cls):
        cls.instances.clear()


class UnitOfWork:
    """Fake unit of work (scoped)."""

    destroyed = False

    def destroy(self):
        UnitOfWork.destroyed = True


@pytest.fixture(autouse=True)
def reset_logger():
    RequestLogger.reset()
    UnitOfWork.destroyed = False
    yield
    RequestLogger.reset()
    UnitOfWork.destroyed = False


@pytest.fixture
def container():
    return Container()


# ===========================================================================
# 1. Singleton provider
# ===========================================================================


class TestSingleton:
    def test_lazy_creation(self):
        """Instance is not created until first resolve."""
        created = []

        def factory():
            created.append(1)
            return Counter()

        provider = Singleton(factory)
        assert provider._instance is None
        assert created == []

    @pytest.mark.asyncio
    async def test_same_instance(self):
        """Same instance returned on every resolve."""
        provider = Singleton(lambda: Counter())
        a = await provider.resolve()
        b = await provider.resolve()
        assert a is b

    @pytest.mark.asyncio
    async def test_container_singleton(self):
        """Container.resolve returns same instance for Singleton."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter("x")))
        a = await c.resolve(Counter)
        b = await c.resolve(Counter)
        assert a is b
        assert a.name == "x"

    @pytest.mark.asyncio
    async def test_singleton_on_init_called_once(self):
        """on_init callback fires exactly once."""
        calls = []
        provider = Singleton(lambda: Counter(), on_init=lambda inst: calls.append(inst))
        await provider.resolve()
        await provider.resolve()
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_singleton_on_destroy(self):
        """on_destroy callback fires when destroy() is called."""
        destroyed = []
        provider = Singleton(lambda: DatabasePool(), on_destroy=lambda db: destroyed.append(db))
        db = await provider.resolve()
        await provider.destroy()
        assert len(destroyed) == 1
        assert destroyed[0] is db
        assert provider._instance is None

    @pytest.mark.asyncio
    async def test_singleton_reset_no_callback(self):
        """reset() clears the instance without calling on_destroy."""
        destroyed = []
        provider = Singleton(lambda: Counter(), on_destroy=lambda _: destroyed.append(1))
        await provider.resolve()
        provider.reset()
        assert provider._instance is None
        assert destroyed == []

    @pytest.mark.asyncio
    async def test_singleton_recreated_after_reset(self):
        """After reset(), next resolve creates a fresh instance."""
        call_count = [0]

        def factory():
            call_count[0] += 1
            return Counter()

        provider = Singleton(factory)
        first = await provider.resolve()
        provider.reset()
        second = await provider.resolve()
        assert first is not second
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_singleton_async_factory(self):
        """Async factory functions are supported for Singleton."""

        async def async_factory():
            return Counter("async")

        provider = Singleton(async_factory)
        inst = await provider.resolve()
        assert inst.name == "async"
        inst2 = await provider.resolve()
        assert inst is inst2

    @pytest.mark.asyncio
    async def test_singleton_concurrent_creation(self):
        """Only one instance is created under concurrent resolution."""
        created = []

        async def slow_factory():
            await asyncio.sleep(0.01)
            created.append(1)
            return Counter()

        provider = Singleton(slow_factory)
        results = await asyncio.gather(*[provider.resolve() for _ in range(10)])
        assert len(created) == 1
        assert all(r is results[0] for r in results)


# ===========================================================================
# 2. Factory provider
# ===========================================================================


class TestFactory:
    @pytest.mark.asyncio
    async def test_new_instance_each_time(self):
        """Factory returns a distinct instance on every call."""
        provider = Factory(lambda: Counter())
        a = await provider.resolve()
        b = await provider.resolve()
        assert a is not b

    @pytest.mark.asyncio
    async def test_container_factory(self):
        """Container.resolve returns new instance each time for Factory."""
        c = Container()
        c.register(RequestLogger, Factory(lambda: RequestLogger()))
        a = await c.resolve(RequestLogger)
        b = await c.resolve(RequestLogger)
        assert a is not b
        assert len(RequestLogger.instances) == 2

    @pytest.mark.asyncio
    async def test_factory_on_init(self):
        """on_init is called for every new instance."""
        calls = []
        provider = Factory(lambda: Counter(), on_init=lambda inst: calls.append(inst))
        await provider.resolve()
        await provider.resolve()
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_factory_async_factory(self):
        """Async factory functions work for Factory."""

        async def async_factory():
            return Counter("async-factory")

        provider = Factory(async_factory)
        inst = await provider.resolve()
        assert inst.name == "async-factory"


# ===========================================================================
# 3. Scoped provider
# ===========================================================================


class TestScoped:
    @pytest.mark.asyncio
    async def test_same_within_scope(self):
        """Same instance returned within a single scope."""
        c = Container()
        c.register(UnitOfWork, Scoped(lambda: UnitOfWork()))
        async with c.scope() as scoped:
            a = await scoped.resolve(UnitOfWork)
            b = await scoped.resolve(UnitOfWork)
        assert a is b

    @pytest.mark.asyncio
    async def test_different_across_scopes(self):
        """Different instances across separate scopes."""
        c = Container()
        c.register(UnitOfWork, Scoped(lambda: UnitOfWork()))
        async with c.scope() as s1:
            a = await s1.resolve(UnitOfWork)
        async with c.scope() as s2:
            b = await s2.resolve(UnitOfWork)
        assert a is not b

    @pytest.mark.asyncio
    async def test_scoped_on_destroy_called(self):
        """on_destroy fires when the scope exits."""
        destroyed = []
        c = Container()
        c.register(
            UnitOfWork,
            Scoped(lambda: UnitOfWork(), on_destroy=lambda inst: destroyed.append(inst)),
        )
        async with c.scope() as scoped:
            inst = await scoped.resolve(UnitOfWork)
        assert len(destroyed) == 1
        assert destroyed[0] is inst

    @pytest.mark.asyncio
    async def test_scoped_on_destroy_not_called_if_never_resolved(self):
        """on_destroy is not called if the provider was never resolved in the scope."""
        destroyed = []
        c = Container()
        c.register(
            UnitOfWork,
            Scoped(lambda: UnitOfWork(), on_destroy=lambda _: destroyed.append(1)),
        )
        async with c.scope():
            pass  # Never resolved
        assert destroyed == []

    @pytest.mark.asyncio
    async def test_scoped_resolve_outside_scope_raises(self):
        """Resolving a Scoped provider directly on Container raises RuntimeError."""
        c = Container()
        c.register(UnitOfWork, Scoped(lambda: UnitOfWork()))
        with pytest.raises(RuntimeError, match="Scoped provider"):
            await c.resolve(UnitOfWork)

    @pytest.mark.asyncio
    async def test_scoped_async_factory(self):
        """Async factory functions work for Scoped providers."""

        async def async_factory():
            return UnitOfWork()

        c = Container()
        c.register(UnitOfWork, Scoped(async_factory))
        async with c.scope() as scoped:
            inst = await scoped.resolve(UnitOfWork)
            assert isinstance(inst, UnitOfWork)

    @pytest.mark.asyncio
    async def test_scoped_scope_id_is_unique(self):
        """Each scope gets a unique scope_id."""
        c = Container()
        ids = set()
        for _ in range(5):
            async with c.scope() as scoped:
                ids.add(scoped.scope_id)
        assert len(ids) == 5

    @pytest.mark.asyncio
    async def test_scoped_inherits_singleton(self):
        """ScopedContainer also resolves Singleton providers from parent."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter("shared")))
        async with c.scope() as scoped:
            inst = await scoped.resolve(Counter)
        assert inst.name == "shared"

    @pytest.mark.asyncio
    async def test_scoped_inherits_factory(self):
        """ScopedContainer also resolves Factory providers from parent."""
        c = Container()
        c.register(RequestLogger, Factory(lambda: RequestLogger()))
        async with c.scope() as scoped:
            inst = await scoped.resolve(RequestLogger)
        assert isinstance(inst, RequestLogger)


# ===========================================================================
# 4. @inject decorator
# ===========================================================================


class TestInject:
    @pytest.mark.asyncio
    async def test_inject_async_function(self):
        """@inject auto-wires async function parameters."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter("injected")))

        @inject(c)
        async def handler(counter: Counter):
            return counter.name

        result = await handler()
        assert result == "injected"

    @pytest.mark.asyncio
    async def test_inject_does_not_override_explicit_arg(self):
        """Explicitly passed kwargs are not overridden by injection."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter("from-container")))
        my_counter = Counter("explicit")

        @inject(c)
        async def handler(counter: Counter):
            return counter.name

        result = await handler(counter=my_counter)
        assert result == "explicit"

    @pytest.mark.asyncio
    async def test_inject_multiple_params(self):
        """@inject wires multiple parameters at once."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter("c")))
        c.register(DatabasePool, Singleton(lambda: DatabasePool("db")))

        @inject(c)
        async def handler(counter: Counter, db: DatabasePool):
            return counter.name, db.url

        name, url = await handler()
        assert name == "c"
        assert url == "db"

    @pytest.mark.asyncio
    async def test_inject_skips_non_registered_params(self):
        """Parameters whose type isn't registered are left for the caller."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter("c")))

        @inject(c)
        async def handler(counter: Counter, extra: str):
            return counter.name + extra

        result = await handler(extra="-ok")
        assert result == "c-ok"

    @pytest.mark.asyncio
    async def test_inject_skips_request_param(self):
        """The conventional 'request' parameter is never injected."""
        c = Container()

        # If request type were registered it should still not be injected by name
        class FakeRequest:
            pass

        c.register(FakeRequest, Singleton(lambda: FakeRequest()))
        fake_req = FakeRequest()

        @inject(c)
        async def handler(request: FakeRequest):
            return request

        result = await handler(fake_req)
        assert result is fake_req

    @pytest.mark.asyncio
    async def test_inject_scoped_raises(self):
        """Injecting a Scoped provider outside a scope raises RuntimeError."""
        c = Container()
        c.register(UnitOfWork, Scoped(lambda: UnitOfWork()))

        @inject(c)
        async def handler(uow: UnitOfWork):
            return uow

        with pytest.raises(RuntimeError, match="Scoped provider"):
            await handler()

    @pytest.mark.asyncio
    async def test_inject_factory_produces_new_instances(self):
        """@inject with Factory provider injects fresh instances each call."""
        c = Container()
        c.register(RequestLogger, Factory(lambda: RequestLogger()))

        @inject(c)
        async def handler(logger: RequestLogger):
            return logger

        a = await handler()
        b = await handler()
        assert a is not b


# ===========================================================================
# 5. Override support
# ===========================================================================


class TestOverride:
    @pytest.mark.asyncio
    async def test_override_replaces_provider(self):
        """override() makes the replacement provider take effect."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter("real")))
        c.override(Counter, Singleton(lambda: Counter("mock")))
        inst = await c.resolve(Counter)
        assert inst.name == "mock"

    @pytest.mark.asyncio
    async def test_reset_override_restores_original(self):
        """reset_override() removes the override, restoring original."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter("real")))
        c.override(Counter, Singleton(lambda: Counter("mock")))
        c.reset_override(Counter)
        inst = await c.resolve(Counter)
        assert inst.name == "real"

    @pytest.mark.asyncio
    async def test_override_without_original(self):
        """An override can be registered even without a base registration."""
        c = Container()
        c.override(Counter, Singleton(lambda: Counter("only-override")))
        inst = await c.resolve(Counter)
        assert inst.name == "only-override"

    def test_override_bad_provider_raises(self):
        """TypeError raised when override receives a non-provider object."""
        c = Container()
        with pytest.raises(TypeError, match="Singleton, Factory, or Scoped"):
            c.override(Counter, "not-a-provider")


# ===========================================================================
# 6. Error cases
# ===========================================================================


class TestErrors:
    @pytest.mark.asyncio
    async def test_resolve_missing_key_raises(self):
        """LookupError raised when no provider is registered."""
        c = Container()
        with pytest.raises(LookupError, match="No provider registered for Counter"):
            await c.resolve(Counter)

    def test_register_bad_provider_raises(self):
        """TypeError raised when register() receives a non-provider object."""
        c = Container()
        with pytest.raises(TypeError, match="Singleton, Factory, or Scoped"):
            c.register(Counter, 42)

    @pytest.mark.asyncio
    async def test_scoped_outside_scope_raises(self):
        """RuntimeError raised when a Scoped provider is resolved directly."""
        c = Container()
        c.register(UnitOfWork, Scoped(lambda: UnitOfWork()))
        with pytest.raises(RuntimeError, match="Scoped provider"):
            await c.resolve(UnitOfWork)

    @pytest.mark.asyncio
    async def test_resolve_missing_in_scope_raises(self):
        """LookupError raised inside a scope for unregistered key."""
        c = Container()
        with pytest.raises(LookupError, match="No provider registered"):
            async with c.scope() as scoped:
                await scoped.resolve(Counter)


# ===========================================================================
# 7. String-based registration
# ===========================================================================


class TestStringKeys:
    @pytest.mark.asyncio
    async def test_register_and_resolve_by_string(self):
        """Services can be registered and resolved using string names."""
        c = Container()
        c.register("db", Singleton(lambda: DatabasePool("sqlite:///:memory:")))
        db = await c.resolve("db")
        assert isinstance(db, DatabasePool)

    @pytest.mark.asyncio
    async def test_string_singleton_same_instance(self):
        """String-keyed Singleton returns same instance."""
        c = Container()
        c.register("counter", Singleton(lambda: Counter()))
        a = await c.resolve("counter")
        b = await c.resolve("counter")
        assert a is b

    def test_has_string_key(self):
        """has() works with string keys."""
        c = Container()
        c.register("my-service", Factory(lambda: Counter()))
        assert c.has("my-service")
        assert not c.has("other-service")

    @pytest.mark.asyncio
    async def test_string_keyed_override(self):
        """override() and reset_override() work with string keys."""
        c = Container()
        c.register("svc", Singleton(lambda: Counter("real")))
        c.override("svc", Singleton(lambda: Counter("mock")))
        inst = await c.resolve("svc")
        assert inst.name == "mock"
        c.reset_override("svc")
        inst2 = await c.resolve("svc")
        assert inst2.name == "real"


# ===========================================================================
# 8. has() check
# ===========================================================================


class TestHas:
    def test_has_registered(self):
        c = Container()
        c.register(Counter, Singleton(lambda: Counter()))
        assert c.has(Counter)

    def test_has_not_registered(self):
        c = Container()
        assert not c.has(Counter)

    def test_has_override(self):
        c = Container()
        c.override(Counter, Singleton(lambda: Counter()))
        assert c.has(Counter)

    @pytest.mark.asyncio
    async def test_has_after_reset(self):
        """has() returns False after container.reset()."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter()))
        await c.reset()
        assert not c.has(Counter)


# ===========================================================================
# 9. Container lifecycle — reset and destroy_singletons
# ===========================================================================


class TestContainerLifecycle:
    @pytest.mark.asyncio
    async def test_reset_clears_registrations(self):
        """reset() removes all registrations."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter()))
        await c.reset()
        assert not c.has(Counter)

    @pytest.mark.asyncio
    async def test_reset_destroys_singleton(self):
        """reset() calls on_destroy on Singleton instances."""
        destroyed = []
        c = Container()
        c.register(
            Counter,
            Singleton(lambda: Counter(), on_destroy=lambda _: destroyed.append(1)),
        )
        await c.resolve(Counter)
        await c.reset()
        assert destroyed == [1]

    @pytest.mark.asyncio
    async def test_destroy_singletons_only(self):
        """destroy_singletons() calls on_destroy but keeps registrations."""
        destroyed = []
        c = Container()
        c.register(
            Counter,
            Singleton(lambda: Counter(), on_destroy=lambda _: destroyed.append(1)),
        )
        await c.resolve(Counter)
        await c.destroy_singletons()
        assert destroyed == [1]
        # Registrations still present
        assert c.has(Counter)

    @pytest.mark.asyncio
    async def test_reset_clears_overrides(self):
        """reset() also clears overrides."""
        c = Container()
        c.override(Counter, Singleton(lambda: Counter("mock")))
        await c.reset()
        assert not c.has(Counter)

    @pytest.mark.asyncio
    async def test_destroy_singletons_async_on_destroy(self):
        """Async on_destroy callbacks are awaited during destroy_singletons."""
        destroyed = []

        async def async_destroy(inst):
            destroyed.append(inst)

        c = Container()
        c.register(Counter, Singleton(lambda: Counter(), on_destroy=async_destroy))
        inst = await c.resolve(Counter)
        await c.destroy_singletons()
        assert inst in destroyed


# ===========================================================================
# 10. Lifecycle hooks — on_init and on_destroy (provider level)
# ===========================================================================


class TestLifecycleHooks:
    @pytest.mark.asyncio
    async def test_singleton_async_on_init(self):
        """Async on_init callback is awaited."""
        calls = []

        async def async_init(inst):
            calls.append(inst)

        provider = Singleton(lambda: Counter(), on_init=async_init)
        inst = await provider.resolve()
        assert inst in calls

    @pytest.mark.asyncio
    async def test_factory_async_on_init(self):
        """Async on_init callback is awaited for each Factory resolve."""
        calls = []

        async def async_init(inst):
            calls.append(inst)

        provider = Factory(lambda: Counter(), on_init=async_init)
        await provider.resolve()
        await provider.resolve()
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_scoped_async_on_destroy(self):
        """Async on_destroy callback is awaited on scope exit."""
        destroyed = []

        async def async_destroy(inst):
            destroyed.append(inst)

        c = Container()
        c.register(UnitOfWork, Scoped(lambda: UnitOfWork(), on_destroy=async_destroy))
        async with c.scope() as scoped:
            inst = await scoped.resolve(UnitOfWork)
        assert inst in destroyed


# ===========================================================================
# 11. ScopedContainer repr and parent access
# ===========================================================================


class TestScopedContainerDetails:
    @pytest.mark.asyncio
    async def test_scoped_repr(self):
        c = Container()
        async with c.scope() as scoped:
            r = repr(scoped)
        assert "ScopedContainer" in r
        assert "scope_id" in r

    @pytest.mark.asyncio
    async def test_container_repr(self):
        c = Container()
        c.register(Counter, Singleton(lambda: Counter()))
        r = repr(c)
        assert "Container" in r
        assert "Counter" in r

    @pytest.mark.asyncio
    async def test_scoped_concurrent_creation(self):
        """Only one instance is created per Scoped key under concurrent resolution."""
        created = []

        async def slow_factory():
            await asyncio.sleep(0.01)
            created.append(1)
            return UnitOfWork()

        c = Container()
        c.register(UnitOfWork, Scoped(slow_factory))
        async with c.scope() as scoped:
            results = await asyncio.gather(*[scoped.resolve(UnitOfWork) for _ in range(10)])
        assert len(created) == 1
        assert all(r is results[0] for r in results)


# ===========================================================================
# 12. Sanic integration
# ===========================================================================


class TestSanicIntegration:
    def _make_mock_app(self):
        """Return a minimal Sanic-like mock with lifecycle hook registration."""
        app = MagicMock()
        app.name = "TestApp"
        app._hooks = {"before_server_stop": [], "on_request": [], "on_response": []}

        def make_decorator(hook_name):
            def decorator(func):
                app._hooks[hook_name].append(func)
                return func

            return decorator

        app.before_server_stop = make_decorator("before_server_stop")
        app.on_request = make_decorator("on_request")
        app.on_response = make_decorator("on_response")
        return app

    @pytest.mark.asyncio
    async def test_sanic_container_registers_hooks(self):
        """sanic_container() registers three lifecycle hooks."""
        from nitro.container import sanic_container

        c = Container()
        app = self._make_mock_app()
        sanic_container(app, c)

        assert len(app._hooks["before_server_stop"]) == 1
        assert len(app._hooks["on_request"]) == 1
        assert len(app._hooks["on_response"]) == 1

    @pytest.mark.asyncio
    async def test_sanic_on_request_creates_scope(self):
        """on_request hook attaches a ScopedContainer to request.ctx."""
        from nitro.container import sanic_container

        c = Container()
        app = self._make_mock_app()
        sanic_container(app, c)

        request = MagicMock()
        request.ctx = MagicMock()
        on_request = app._hooks["on_request"][0]
        await on_request(request)

        assert isinstance(request.ctx.container, ScopedContainer)

    @pytest.mark.asyncio
    async def test_sanic_on_response_cleans_up(self):
        """on_response hook calls _cleanup on the scoped container."""
        from nitro.container import sanic_container

        destroyed = []
        c = Container()
        c.register(
            UnitOfWork,
            Scoped(lambda: UnitOfWork(), on_destroy=lambda _: destroyed.append(1)),
        )
        app = self._make_mock_app()
        sanic_container(app, c)

        # Simulate request lifecycle
        request = MagicMock()
        request.ctx = MagicMock()
        response = MagicMock()

        on_request = app._hooks["on_request"][0]
        on_response = app._hooks["on_response"][0]

        await on_request(request)
        # Resolve something in the scope
        await request.ctx.container.resolve(UnitOfWork)
        await on_response(request, response)

        assert destroyed == [1]

    @pytest.mark.asyncio
    async def test_sanic_on_stop_destroys_singletons(self):
        """before_server_stop hook destroys singleton instances."""
        destroyed = []
        c = Container()
        c.register(
            DatabasePool,
            Singleton(lambda: DatabasePool(), on_destroy=lambda db: destroyed.append(db)),
        )
        await c.resolve(DatabasePool)

        from nitro.container import sanic_container

        app = self._make_mock_app()
        sanic_container(app, c)

        stop_hook = app._hooks["before_server_stop"][0]
        await stop_hook(app, None)

        assert len(destroyed) == 1

    @pytest.mark.asyncio
    async def test_sanic_response_hook_no_error_without_container(self):
        """on_response does not fail if request.ctx.container is absent."""
        from nitro.container import sanic_container

        c = Container()
        app = self._make_mock_app()
        sanic_container(app, c)

        request = MagicMock()
        request.ctx = MagicMock(spec=[])  # no 'container' attribute
        response = MagicMock()

        on_response = app._hooks["on_response"][0]
        # Should not raise
        await on_response(request, response)


# ===========================================================================
# 13. _key_name helper
# ===========================================================================


class TestKeyName:
    def test_type_key(self):
        assert _key_name(Counter) == "Counter"

    def test_string_key(self):
        assert _key_name("my-svc") == "'my-svc'"


# ===========================================================================
# 14. Edge cases and integration
# ===========================================================================


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_container_is_not_singleton(self):
        """Each Container() call returns a distinct container."""
        c1 = Container()
        c2 = Container()
        c1.register(Counter, Singleton(lambda: Counter("c1")))
        c2.register(Counter, Singleton(lambda: Counter("c2")))
        a = await c1.resolve(Counter)
        b = await c2.resolve(Counter)
        assert a is not b
        assert a.name == "c1"
        assert b.name == "c2"

    @pytest.mark.asyncio
    async def test_multiple_provider_types_in_one_container(self):
        """Container handles Singleton, Factory, and Scoped simultaneously."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter("singleton")))
        c.register(RequestLogger, Factory(lambda: RequestLogger()))
        c.register(UnitOfWork, Scoped(lambda: UnitOfWork()))

        singleton = await c.resolve(Counter)
        singleton2 = await c.resolve(Counter)
        assert singleton is singleton2

        factory1 = await c.resolve(RequestLogger)
        factory2 = await c.resolve(RequestLogger)
        assert factory1 is not factory2

        async with c.scope() as scoped:
            scoped1 = await scoped.resolve(UnitOfWork)
            scoped2 = await scoped.resolve(UnitOfWork)
        assert scoped1 is scoped2

    @pytest.mark.asyncio
    async def test_inject_uses_same_singleton_across_calls(self):
        """@inject resolves the same Singleton instance on repeated calls."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter()))

        @inject(c)
        async def handler(counter: Counter):
            return counter

        a = await handler()
        b = await handler()
        assert a is b

    @pytest.mark.asyncio
    async def test_nested_scopes(self):
        """Nested scopes each get independent Scoped instances."""
        c = Container()
        c.register(UnitOfWork, Scoped(lambda: UnitOfWork()))

        async with c.scope() as outer:
            outer_inst = await outer.resolve(UnitOfWork)
            async with c.scope() as inner:
                inner_inst = await inner.resolve(UnitOfWork)
            assert outer_inst is not inner_inst

    @pytest.mark.asyncio
    async def test_override_shadows_scoped_in_scope(self):
        """An override (e.g. Factory) can replace a Scoped provider inside a scope."""
        c = Container()
        c.register(UnitOfWork, Scoped(lambda: UnitOfWork()))
        # Override with Factory
        c.override(UnitOfWork, Factory(lambda: UnitOfWork()))

        async with c.scope() as scoped:
            a = await scoped.resolve(UnitOfWork)
            b = await scoped.resolve(UnitOfWork)
        # Factory produces different instances; override wins
        assert a is not b

    @pytest.mark.asyncio
    async def test_register_overwrites_existing(self):
        """Calling register() twice for the same key replaces the provider."""
        c = Container()
        c.register(Counter, Singleton(lambda: Counter("first")))
        c.register(Counter, Singleton(lambda: Counter("second")))
        inst = await c.resolve(Counter)
        assert inst.name == "second"

    @pytest.mark.asyncio
    async def test_scope_cleanup_on_exception(self):
        """Scope cleanup (on_destroy) runs even if an exception is raised inside."""
        destroyed = []
        c = Container()
        c.register(
            UnitOfWork,
            Scoped(lambda: UnitOfWork(), on_destroy=lambda _: destroyed.append(1)),
        )
        with pytest.raises(ValueError):
            async with c.scope() as scoped:
                await scoped.resolve(UnitOfWork)
                raise ValueError("oops")

        assert destroyed == [1]
