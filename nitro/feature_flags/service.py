"""
FeatureFlags service — the main entry point for feature flag management.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from .models import Flag, FlagRule
from .store import FlagStore, MemoryFlagStore


class FlagDisabledError(Exception):
    """Raised by :meth:`FeatureFlags.require` when a flag is not active.

    Args:
        flag_name: Name of the disabled flag.
        context: The evaluation context passed to ``require()``.
    """

    def __init__(self, flag_name: str, context: dict[str, Any] | None = None) -> None:
        self.flag_name = flag_name
        self.context = context
        super().__init__(
            f"Feature flag '{flag_name}' is not enabled"
            + (f" for context {context}" if context else "")
        )


class FeatureFlags:
    """Main service class for managing and evaluating feature flags.

    Args:
        store: Storage backend.  Defaults to a new :class:`MemoryFlagStore`.

    Example::

        flags = FeatureFlags()

        flags.create("dark_mode", enabled=True)
        flags.create(
            "new_checkout",
            rollout_percentage=20,
            rules=[FlagRule(attribute="plan", operator="eq", value="pro")],
        )

        if flags.is_enabled("dark_mode"):
            ...

        if flags.is_enabled("new_checkout", context={"user_id": "u42", "plan": "pro"}):
            ...
    """

    def __init__(self, store: FlagStore | None = None) -> None:
        self._store: FlagStore = store if store is not None else MemoryFlagStore()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        enabled: bool = False,
        description: str = "",
        rollout_percentage: int = 100,
        rules: list[FlagRule] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Flag:
        """Create a new feature flag.

        Args:
            name: Unique flag identifier.
            enabled: Whether the flag is globally on.
            description: Human-readable description.
            rollout_percentage: Percentage of users who see the flag (0–100).
            rules: Optional list of conditional rules.
            metadata: Arbitrary extra data.

        Returns:
            The newly created :class:`Flag`.

        Raises:
            ValueError: If a flag with *name* already exists.
        """
        if self._store.get(name) is not None:
            raise ValueError(f"Feature flag '{name}' already exists")

        flag = Flag(
            name=name,
            enabled=enabled,
            description=description,
            rollout_percentage=rollout_percentage,
            rules=rules or [],
            metadata=metadata or {},
        )
        self._store.set(flag)
        return flag

    def get(self, name: str) -> Flag | None:
        """Return the :class:`Flag` with *name*, or ``None``."""
        return self._store.get(name)

    def update(self, name: str, **kwargs: Any) -> Flag:
        """Update one or more fields on an existing flag.

        Automatically updates ``updated_at``.

        Args:
            name: Flag identifier.
            **kwargs: Field values to update.

        Returns:
            The updated :class:`Flag`.

        Raises:
            KeyError: If no flag with *name* exists.
        """
        flag = self._store.get(name)
        if flag is None:
            raise KeyError(f"Feature flag '{name}' not found")

        for field, value in kwargs.items():
            setattr(flag, field, value)
        flag.updated_at = datetime.now(timezone.utc)
        self._store.set(flag)
        return flag

    def delete(self, name: str) -> bool:
        """Delete a flag.

        Returns:
            ``True`` if the flag existed and was deleted.
        """
        return self._store.delete(name)

    def list_flags(self) -> list[Flag]:
        """Return all flags."""
        return self._store.list_all()

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def is_enabled(self, name: str, context: dict[str, Any] | None = None) -> bool:
        """Return whether the flag is active for *context*.

        Returns ``False`` (rather than raising) if the flag does not exist.

        Args:
            name: Flag identifier.
            context: Evaluation context (e.g. ``{"user_id": "u1", "role": "admin"}``).
        """
        flag = self._store.get(name)
        if flag is None:
            return False
        return flag.is_active_for(context)

    def require(self, name: str, context: dict[str, Any] | None = None) -> bool:
        """Assert that *name* is enabled for *context*.

        Returns ``True`` when the flag is active.

        Raises:
            FlagDisabledError: If the flag is not active or does not exist.
        """
        if not self.is_enabled(name, context):
            raise FlagDisabledError(name, context)
        return True

    def toggle(self, name: str) -> Flag:
        """Flip the ``enabled`` state of a flag.

        Args:
            name: Flag identifier.

        Returns:
            The updated :class:`Flag`.

        Raises:
            KeyError: If no flag with *name* exists.
        """
        flag = self._store.get(name)
        if flag is None:
            raise KeyError(f"Feature flag '{name}' not found")
        return self.update(name, enabled=not flag.enabled)

    # ------------------------------------------------------------------
    # Middleware helper
    # ------------------------------------------------------------------

    def flag_middleware(self, context_extractor: Callable[..., dict[str, Any]]) -> Callable:
        """Return a middleware function that evaluates flags per-request.

        ``context_extractor`` is a callable that receives the incoming
        request object and returns a dict suitable for passing to
        :meth:`is_enabled`.

        The returned middleware attaches a ``feature_flags`` helper to the
        request so handlers can call ``request.feature_flags("my_flag")``.

        This is framework-agnostic — wire it into your framework's
        middleware stack as appropriate.

        Args:
            context_extractor: ``(request) -> dict`` callable.

        Returns:
            An async middleware coroutine.
        """
        flags_service = self

        async def middleware(request: Any, handler: Callable) -> Any:
            ctx = context_extractor(request)

            def check_flag(flag_name: str) -> bool:
                return flags_service.is_enabled(flag_name, ctx)

            request.feature_flags = check_flag  # type: ignore[attr-defined]
            return await handler(request)

        return middleware


# ------------------------------------------------------------------
# feature_flag decorator
# ------------------------------------------------------------------


def feature_flag(
    flags: FeatureFlags,
    flag_name: str,
    fallback: Callable | None = None,
    context_extractor: Callable | None = None,
) -> Callable:
    """Decorator that gates a function behind a feature flag.

    When the flag is disabled the *fallback* callable is invoked instead
    (with the same arguments).  If no fallback is provided and the flag is
    disabled, :class:`FlagDisabledError` is raised.

    Args:
        flags: :class:`FeatureFlags` instance to evaluate against.
        flag_name: Name of the flag to check.
        fallback: Optional replacement callable when flag is disabled.
        context_extractor: Optional ``(*args, **kwargs) -> dict`` callable.
            If provided, its return value is passed as ``context`` to
            :meth:`FeatureFlags.is_enabled`.  Defaults to ``None`` (no context).

    Example::

        @feature_flag(flags, "new_checkout", fallback=old_checkout)
        async def new_checkout_handler(request):
            ...
    """
    import functools

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = context_extractor(*args, **kwargs) if context_extractor else None
            if flags.is_enabled(flag_name, ctx):
                return await func(*args, **kwargs)
            if fallback is not None:
                import asyncio

                if asyncio.iscoroutinefunction(fallback):
                    return await fallback(*args, **kwargs)
                return fallback(*args, **kwargs)
            raise FlagDisabledError(flag_name, ctx)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = context_extractor(*args, **kwargs) if context_extractor else None
            if flags.is_enabled(flag_name, ctx):
                return func(*args, **kwargs)
            if fallback is not None:
                return fallback(*args, **kwargs)
            raise FlagDisabledError(flag_name, ctx)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
