"""
Core dependency injection container for the Nitro framework.

Usage::

    from nitro.container import Container, Singleton, Factory, Scoped

    container = Container()
    container.register(DatabasePool, Singleton(lambda: DatabasePool("sqlite:///app.db")))
    container.register(RequestLogger, Factory(lambda: RequestLogger()))
    container.register(UnitOfWork, Scoped(lambda: UnitOfWork()))

    db = await container.resolve(DatabasePool)

    async with container.scope() as scoped:
        uow = await scoped.resolve(UnitOfWork)
"""

from __future__ import annotations

import asyncio
import inspect
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator, Optional, Type, TypeVar, Union

from .providers import Factory, Scoped, Singleton

T = TypeVar("T")

# Keys may be a type or a plain string name
_Key = Union[Type, str]
_Provider = Union[Singleton, Factory, Scoped]


def _key_name(key: _Key) -> str:
    """Human-readable name for a registration key (for error messages)."""
    if isinstance(key, str):
        return repr(key)
    return key.__name__


class ScopedContainer:
    """A short-lived container that inherits registrations from a parent.

    Scoped providers get their own instance storage here.  Singleton and
    Factory providers delegate to the parent container.

    Do not create directly — use ``Container.scope()``.
    """

    def __init__(self, parent: "Container", scope_id: str) -> None:
        self._parent = parent
        self._scope_id = scope_id
        self._instances: Dict[_Key, Any] = {}
        self._locks: Dict[_Key, asyncio.Lock] = {}

    @property
    def scope_id(self) -> str:
        """Unique identifier for this scope."""
        return self._scope_id

    async def resolve(self, key: _Key) -> Any:
        """Resolve *key* within this scope.

        Scoped providers store their instance here.
        Singleton / Factory providers delegate to the parent.
        """
        provider = self._parent._get_provider(key)

        if isinstance(provider, Scoped):
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            async with self._locks[key]:
                if key not in self._instances:
                    instance = provider.factory()
                    if inspect.isawaitable(instance):
                        instance = await instance
                    if provider.on_init:
                        result = provider.on_init(instance)
                        if inspect.isawaitable(result):
                            await result
                    self._instances[key] = instance
            return self._instances[key]

        # Singleton or Factory — delegate to parent
        return await self._parent.resolve(key)

    async def _cleanup(self) -> None:
        """Invoke ``on_destroy`` for all Scoped instances held in this scope."""
        for key, instance in list(self._instances.items()):
            provider = self._parent._providers.get(key)
            if isinstance(provider, Scoped) and provider.on_destroy:
                result = provider.on_destroy(instance)
                if inspect.isawaitable(result):
                    await result
        self._instances.clear()

    def __repr__(self) -> str:
        return f"ScopedContainer(scope_id={self._scope_id!r})"


class Container:
    """Lightweight async-ready dependency injection container.

    Supports three provider lifecycles:
    - :class:`~nitro.container.providers.Singleton` — created once, shared forever.
    - :class:`~nitro.container.providers.Factory` — new instance per resolve.
    - :class:`~nitro.container.providers.Scoped` — new instance per ``scope()``.

    Registration accepts both *type* objects and plain *string* names as keys.

    Thread / async safety:
    - Singleton creation is protected by an ``asyncio.Lock`` inside the provider.
    - Scoped instance creation is protected by per-key locks inside ``ScopedContainer``.

    Example::

        container = Container()
        container.register(MyService, Singleton(lambda: MyService()))
        svc = await container.resolve(MyService)
    """

    def __init__(self) -> None:
        self._providers: Dict[_Key, _Provider] = {}
        self._overrides: Dict[_Key, _Provider] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, key: _Key, provider: _Provider) -> None:
        """Register a provider for *key*.

        Args:
            key: A type or string name.
            provider: A :class:`Singleton`, :class:`Factory`, or :class:`Scoped`
                      instance.

        Raises:
            TypeError: If *provider* is not a recognised provider type.
        """
        if not isinstance(provider, (Singleton, Factory, Scoped)):
            raise TypeError(
                f"provider must be Singleton, Factory, or Scoped; "
                f"got {type(provider).__name__!r}"
            )
        self._providers[key] = provider

    def override(self, key: _Key, provider: _Provider) -> None:
        """Override a registration — useful in tests.

        Overrides take precedence over normal registrations.  Use
        :meth:`reset_override` to remove a specific override or
        :meth:`reset` to clear everything.

        Args:
            key: A type or string name.
            provider: Replacement provider.
        """
        if not isinstance(provider, (Singleton, Factory, Scoped)):
            raise TypeError(
                f"provider must be Singleton, Factory, or Scoped; "
                f"got {type(provider).__name__!r}"
            )
        self._overrides[key] = provider

    def reset_override(self, key: _Key) -> None:
        """Remove the override for *key* (if any)."""
        self._overrides.pop(key, None)

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def _get_provider(self, key: _Key) -> _Provider:
        """Return the active provider for *key*, checking overrides first."""
        if key in self._overrides:
            return self._overrides[key]
        if key in self._providers:
            return self._providers[key]
        raise LookupError(
            f"No provider registered for {_key_name(key)}. "
            f"Did you call container.register({_key_name(key)}, ...)?"
        )

    async def resolve(self, key: _Key) -> Any:
        """Resolve and return the service for *key*.

        Calling with a :class:`Scoped` provider outside a scope will raise
        a ``RuntimeError``; use :meth:`scope` to create a scoped context.

        Args:
            key: A registered type or string name.

        Returns:
            The resolved service instance.

        Raises:
            LookupError: If no provider is registered for *key*.
            RuntimeError: If a Scoped provider is resolved outside a scope.
        """
        provider = self._get_provider(key)
        if isinstance(provider, Scoped):
            raise RuntimeError(
                f"{_key_name(key)} is a Scoped provider. "
                f"Resolve it inside `async with container.scope() as scoped`."
            )
        return await provider.resolve()

    # ------------------------------------------------------------------
    # Scoped context
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def scope(self):
        """Async context manager that yields a :class:`ScopedContainer`.

        Scoped providers resolved within this context share the same instance.
        On exit, ``on_destroy`` callbacks are invoked for all scoped instances.

        Example::

            async with container.scope() as scoped:
                uow = await scoped.resolve(UnitOfWork)
        """
        scope_id = uuid.uuid4().hex
        scoped = ScopedContainer(self, scope_id)
        try:
            yield scoped
        finally:
            await scoped._cleanup()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def has(self, key: _Key) -> bool:
        """Return ``True`` if a provider (or override) is registered for *key*."""
        return key in self._overrides or key in self._providers

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def reset(self) -> None:
        """Destroy all singletons and clear all registrations and overrides.

        Useful in tests to obtain a clean slate between test cases.
        """
        for provider in list(self._providers.values()):
            if isinstance(provider, Singleton):
                await provider.destroy()
        for provider in list(self._overrides.values()):
            if isinstance(provider, Singleton):
                await provider.destroy()
        self._providers.clear()
        self._overrides.clear()

    async def destroy_singletons(self) -> None:
        """Call ``on_destroy`` on all registered Singleton providers.

        Does not clear registrations — the container can continue to be used.
        """
        for provider in self._providers.values():
            if isinstance(provider, Singleton):
                await provider.destroy()
        for provider in self._overrides.values():
            if isinstance(provider, Singleton):
                await provider.destroy()

    def __repr__(self) -> str:
        keys = [_key_name(k) for k in self._providers]
        return f"Container(registered=[{', '.join(keys)}])"
