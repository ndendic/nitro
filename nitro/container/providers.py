"""
Provider types for the Nitro dependency injection container.

Three lifecycle policies:
- Singleton  : One instance, created lazily on first resolve, reused forever.
- Factory    : New instance created on every resolve call.
- Scoped     : One instance per ``Container.scope()`` context, shared within it.
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class Singleton:
    """Lazy singleton — one instance for the lifetime of the container.

    The factory is called at most once (thread/async safe).  Subsequent
    ``resolve()`` calls return the cached instance.

    Args:
        factory: Sync or async callable that produces the service instance.
        on_init: Optional callback invoked right after the instance is created.
        on_destroy: Optional callback invoked when the container is reset or stopped.
    """

    factory: Callable
    on_init: Optional[Callable] = None
    on_destroy: Optional[Callable] = None
    _instance: Any = field(default=None, init=False, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    async def resolve(self) -> Any:
        """Return the singleton instance, creating it on first call."""
        if self._instance is not None:
            return self._instance
        async with self._lock:
            # Double-checked locking
            if self._instance is None:
                instance = self.factory()
                if inspect.isawaitable(instance):
                    instance = await instance
                if self.on_init:
                    result = self.on_init(instance)
                    if inspect.isawaitable(result):
                        await result
                self._instance = instance
        return self._instance

    async def destroy(self) -> None:
        """Invoke ``on_destroy`` and clear the cached instance."""
        if self._instance is not None and self.on_destroy:
            result = self.on_destroy(self._instance)
            if inspect.isawaitable(result):
                await result
        self._instance = None

    def reset(self) -> None:
        """Clear the cached instance without calling ``on_destroy``."""
        self._instance = None


@dataclass
class Factory:
    """Factory provider — new instance on every resolve.

    Args:
        factory: Sync or async callable that produces the service instance.
        on_init: Optional callback invoked right after each new instance is created.
    """

    factory: Callable
    on_init: Optional[Callable] = None

    async def resolve(self) -> Any:
        """Create and return a fresh instance."""
        instance = self.factory()
        if inspect.isawaitable(instance):
            instance = await instance
        if self.on_init:
            result = self.on_init(instance)
            if inspect.isawaitable(result):
                await result
        return instance


@dataclass
class Scoped:
    """Scoped provider — one instance per ``Container.scope()`` context.

    Within a single scope the same instance is reused; different scopes get
    different instances.  The instance is created on first resolve within a scope.

    Args:
        factory: Sync or async callable that produces the service instance.
        on_init: Optional callback invoked right after the instance is created.
        on_destroy: Optional callback invoked when the scope exits.
    """

    factory: Callable
    on_init: Optional[Callable] = None
    on_destroy: Optional[Callable] = None
