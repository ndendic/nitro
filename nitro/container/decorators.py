"""
``@inject`` decorator for automatic dependency wiring via type hints.

Usage::

    from nitro.container import Container, Singleton, inject

    container = Container()
    container.register(MyService, Singleton(lambda: MyService()))

    @inject(container)
    async def handle(svc: MyService):
        ...

    await handle()  # svc injected automatically
"""

from __future__ import annotations

import functools
import inspect
from typing import TYPE_CHECKING, Any, Callable, get_type_hints

if TYPE_CHECKING:
    from .container import Container


def inject(container: "Container"):
    """Decorator factory that auto-wires type-annotated parameters.

    Parameters whose names appear in the wrapped function's type hints AND
    whose annotated type is registered in *container* will be resolved and
    injected automatically.  Parameters that are not registered (or have no
    annotation) are left for the caller to supply.

    Works with both ``async def`` and plain ``def`` functions.  For plain
    functions the container is resolved synchronously by running the async
    ``resolve()`` calls in the current event loop; if no loop is running an
    ``asyncio.run()`` call is made transparently.

    Args:
        container: The :class:`~nitro.container.Container` to resolve from.

    Returns:
        A decorator that wraps the target function.

    Example::

        @inject(container)
        async def create_order(db: DatabasePool, logger: RequestLogger):
            ...

        await create_order()           # both injected
        await create_order(logger=my_logger)  # logger overridden, db injected
    """

    def decorator(func: Callable) -> Callable:
        # Resolve hints once at decoration time (avoids repeated calls).
        try:
            hints = get_type_hints(func)
        except Exception:
            hints = {}

        sig = inspect.signature(func)
        params = sig.parameters

        # Determine which parameters to inject:
        # - has a type annotation
        # - the annotated type is registered in the container
        # - not "request" (conventional Sanic/web framework request arg)
        injectable: list[str] = []
        for name, param in params.items():
            if name in ("self", "cls", "request"):
                continue
            hint = hints.get(name)
            if hint is not None and container.has(hint):
                injectable.append(name)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Resolve missing injectable parameters
            for name in injectable:
                if name not in kwargs:
                    hint = hints[name]
                    provider = container._get_provider(hint)
                    from .providers import Scoped
                    if isinstance(provider, Scoped):
                        raise RuntimeError(
                            f"Cannot inject Scoped provider {hint.__name__!r} via @inject "
                            f"outside a scope context.  Use `async with container.scope()` "
                            f"and resolve manually."
                        )
                    kwargs[name] = await container.resolve(hint)
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            import asyncio

            async def _resolve_all():
                for name in injectable:
                    if name not in kwargs:
                        hint = hints[name]
                        provider = container._get_provider(hint)
                        from .providers import Scoped
                        if isinstance(provider, Scoped):
                            raise RuntimeError(
                                f"Cannot inject Scoped provider {hint.__name__!r} via @inject "
                                f"outside a scope context."
                            )
                        kwargs[name] = await container.resolve(hint)

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Can't block — caller must be async; warn and call without injection.
                    raise RuntimeError(
                        "inject() used on a sync function called from within a running "
                        "event loop.  Convert the function to async or call it from "
                        "synchronous code."
                    )
                loop.run_until_complete(_resolve_all())
            except RuntimeError:
                asyncio.run(_resolve_all())

            return func(*args, **kwargs)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
