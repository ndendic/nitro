"""
@audited decorator — auto-records entity changes around method execution.

Wraps sync and async entity methods to capture the entity state before
and after execution, then records the appropriate AuditEntry.  Supports
extracting the actor from the request object via a dotted path string.
"""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable, Optional

from .trail import AuditTrail


def _extract_actor(obj: Any, path: str) -> str:
    """Walk a dotted attribute path on *obj* to extract the actor string.

    Example::

        _extract_actor(request, "user.id")     # request.user.id
        _extract_actor(request, "user_id")     # request.user_id

    Falls back to "system" if any attribute in the chain is missing or
    the final value is ``None``.

    Args:
        obj: Root object to start traversal from.
        path: Dot-separated attribute path.

    Returns:
        Actor string, or "system" on any failure.
    """
    try:
        parts = path.split(".")
        current = obj
        for part in parts:
            current = getattr(current, part)
        if current is None:
            return "system"
        return str(current)
    except AttributeError:
        return "system"


def audited(
    trail: AuditTrail,
    *,
    actor_from: Optional[str] = None,
    action: Optional[str] = None,
) -> Callable:
    """Decorator that auto-records entity changes around a method call.

    The decorated method must be a method on an object that exposes a
    ``to_dict()`` method (or ``model_dump()`` for Pydantic models) so the
    decorator can capture the entity snapshot before and after execution.

    Supports both sync and async methods.

    Args:
        trail: The ``AuditTrail`` to record into.
        actor_from: Dotted path to extract the actor from the first
            positional argument (typically the ``request`` object).
            For example ``"user_id"`` reads ``request.user_id``, while
            ``"user.id"`` reads ``request.user.id``.
            Falls back to "system" if the attribute does not exist.
        action: Override the action type ("create", "update", "delete").
            Defaults to "update".

    Returns:
        Decorator function.

    Example::

        @audited(trail, actor_from="user_id")
        def update_order(self, request, **kwargs):
            self.status = "active"
            self.save()
    """
    resolved_action = action or "update"

    def decorator(func: Callable) -> Callable:
        def _get_snapshot(instance: Any) -> dict:
            if hasattr(instance, "model_dump"):
                return instance.model_dump()
            if hasattr(instance, "to_dict"):
                return instance.to_dict()
            return {}

        def _get_entity_info(instance: Any) -> tuple[str, str]:
            entity_type = type(instance).__name__
            entity_id = str(getattr(instance, "id", "unknown"))
            return entity_type, entity_id

        def _resolve_actor(*args: Any) -> str:
            if actor_from and len(args) >= 2:
                # args[0] is self, args[1] is the first explicit arg (request)
                return _extract_actor(args[1], actor_from)
            return "system"

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            instance = args[0]
            entity_type, entity_id = _get_entity_info(instance)
            actor = _resolve_actor(*args)
            old_snapshot = _get_snapshot(instance)

            result = func(*args, **kwargs)

            new_snapshot = _get_snapshot(instance)

            if resolved_action == "create":
                trail.record_create(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    snapshot=new_snapshot,
                    actor=actor,
                )
            elif resolved_action == "delete":
                trail.record_delete(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    snapshot=old_snapshot,
                    actor=actor,
                )
            else:
                trail.record_update(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    old_state=old_snapshot,
                    new_state=new_snapshot,
                    actor=actor,
                )
            return result

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            instance = args[0]
            entity_type, entity_id = _get_entity_info(instance)
            actor = _resolve_actor(*args)
            old_snapshot = _get_snapshot(instance)

            result = await func(*args, **kwargs)

            new_snapshot = _get_snapshot(instance)

            if resolved_action == "create":
                trail.record_create(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    snapshot=new_snapshot,
                    actor=actor,
                )
            elif resolved_action == "delete":
                trail.record_delete(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    snapshot=old_snapshot,
                    actor=actor,
                )
            else:
                trail.record_update(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    old_state=old_snapshot,
                    new_state=new_snapshot,
                    actor=actor,
                )
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
