"""
Nitro Permissions — Framework-agnostic permission decorators.

These decorators extend the auth module's ``@require_auth`` / ``@require_role``
pattern with fine-grained resource:action permission checking.

Usage pattern::

    svc = PermissionService()
    auth = AuthService(secret="...")

    @require_auth(auth)
    @require_permission("post", "create", service=svc)
    async def create_post(request, current_user):
        ...

    @require_auth(auth)
    @require_any_permission(("post", "create"), ("post", "edit"), service=svc)
    async def write_post(request, current_user):
        ...

    @require_auth(auth)
    @require_all_permissions(("post", "create"), ("post", "publish"), service=svc)
    async def publish_post(request, current_user):
        ...

Notes:
    - All decorators must be placed *after* ``@require_auth`` (i.e. closer to
      the function body) so that ``current_user`` is already in kwargs.
    - They are framework-agnostic — no framework imports are used.
    - If no ``service`` is provided a default ``PermissionService()`` instance
      is created (stateless, safe to create per-call).
"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Optional, Tuple

from .service import PermissionService


class PermissionError(Exception):
    """Raised when a permission check fails.

    Attributes:
        message: Human-readable error description.
        status_code: Suggested HTTP status code (403 for authorisation
            failures, 401 when ``current_user`` is missing).
    """

    def __init__(
        self,
        message: str = "Permission denied",
        status_code: int = 403,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def require_permission(
    resource: str,
    action: str,
    service: Optional[PermissionService] = None,
) -> Callable:
    """Decorator that requires the current user to hold a specific permission.

    Must be applied *after* ``@require_auth`` so that ``current_user`` is
    already injected into kwargs.

    Args:
        resource: The resource to check (e.g. ``"post"``).
        action: The action to check (e.g. ``"create"``).
        service: Optional ``PermissionService`` instance. A default (stateless)
            instance is used when not provided.

    Raises:
        PermissionError(401): If ``current_user`` is not in kwargs.
        PermissionError(403): If the user lacks the required permission.

    Example::

        @require_auth(auth)
        @require_permission("post", "delete")
        async def delete_post(request, current_user):
            ...
    """
    _service = service or PermissionService()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise PermissionError("Authentication required", 401)
            if not _service.user_has_permission(current_user, resource, action):
                raise PermissionError(
                    f"Requires permission: {resource}:{action}", 403
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(
    *perms: Tuple[str, str],
    service: Optional[PermissionService] = None,
) -> Callable:
    """Decorator that passes if the user holds *at least one* of the given permissions.

    Must be applied *after* ``@require_auth``.

    Args:
        *perms: One or more ``(resource, action)`` tuples. The user needs to
            match at least one.
        service: Optional ``PermissionService`` instance.

    Raises:
        PermissionError(401): If ``current_user`` is not in kwargs.
        PermissionError(403): If the user lacks all of the required permissions.

    Example::

        @require_auth(auth)
        @require_any_permission(("post", "create"), ("post", "edit"))
        async def write_post(request, current_user):
            ...
    """
    _service = service or PermissionService()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise PermissionError("Authentication required", 401)
            for resource, action in perms:
                if _service.user_has_permission(current_user, resource, action):
                    return await func(*args, **kwargs)
            perm_str = ", ".join(f"{r}:{a}" for r, a in perms)
            raise PermissionError(
                f"Requires at least one of: {perm_str}", 403
            )

        return wrapper

    return decorator


def require_all_permissions(
    *perms: Tuple[str, str],
    service: Optional[PermissionService] = None,
) -> Callable:
    """Decorator that passes only if the user holds *all* of the given permissions.

    Must be applied *after* ``@require_auth``.

    Args:
        *perms: One or more ``(resource, action)`` tuples. The user must
            match every one.
        service: Optional ``PermissionService`` instance.

    Raises:
        PermissionError(401): If ``current_user`` is not in kwargs.
        PermissionError(403): If the user lacks any of the required permissions.

    Example::

        @require_auth(auth)
        @require_all_permissions(("post", "create"), ("post", "publish"))
        async def publish_post(request, current_user):
            ...
    """
    _service = service or PermissionService()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise PermissionError("Authentication required", 401)
            missing = [
                f"{r}:{a}"
                for r, a in perms
                if not _service.user_has_permission(current_user, resource=r, action=a)
            ]
            if missing:
                raise PermissionError(
                    f"Missing required permissions: {', '.join(missing)}", 403
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
