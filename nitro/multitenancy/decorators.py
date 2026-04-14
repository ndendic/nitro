"""
nitro.multitenancy — Route protection decorators.

Provides framework-agnostic decorators that resolve the current tenant
from the request and optionally enforce tenant-scoped role requirements.

Resolution order for ``require_tenant``:
  1. ``request.ctx.tenant_id`` (set by upstream middleware)
  2. ``X-Tenant-ID`` request header
  3. First path segment that matches a tenant slug
     (e.g. ``/acme/dashboard`` → tries slug ``"acme"``)

Usage::

    svc = TenantService()

    @require_tenant(service=svc)
    async def dashboard(request, current_tenant):
        ...

    @require_tenant(service=svc)
    @require_tenant_role("admin", service=svc)
    async def admin_panel(request, current_tenant, current_user):
        ...
"""

from __future__ import annotations

import asyncio
import inspect
from functools import wraps
from typing import Callable, Optional

from .models import Tenant
from .service import TenantService


class TenantError(Exception):
    """Raised when tenant resolution or role enforcement fails.

    Attributes:
        message: Human-readable error description.
        status_code: Suggested HTTP status code (404 when the tenant is
            not found, 403 for inactive tenant or insufficient role,
            401 when ``current_user`` is missing for role checks).
    """

    def __init__(self, message: str = "Tenant not found", status_code: int = 404):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _resolve_tenant_from_request(
    request, service: TenantService
) -> Optional[Tenant]:
    """Try to resolve a Tenant from the request using the 3-step strategy.

    1. ``request.ctx.tenant_id`` attribute
    2. ``X-Tenant-ID`` header
    3. First path segment matched against known tenant slugs

    Returns the Tenant object if found, otherwise None.
    """
    # 1. Framework context attribute (set by middleware)
    tenant_id = getattr(getattr(request, "ctx", None), "tenant_id", None)
    if tenant_id:
        # Could be a full ID or a slug — try both
        tenant = Tenant.get(tenant_id)
        if not tenant:
            tenant = service.get_tenant(tenant_id)
        if tenant:
            return tenant

    # 2. X-Tenant-ID header (accept both header dict and attribute access)
    headers = getattr(request, "headers", {}) or {}
    if hasattr(headers, "get"):
        header_val = headers.get("X-Tenant-ID") or headers.get("x-tenant-id")
    else:
        header_val = None
    if header_val:
        tenant = Tenant.get(header_val)
        if not tenant:
            tenant = service.get_tenant(header_val)
        if tenant:
            return tenant

    # 3. First URL path segment as a potential slug
    path = getattr(request, "path", "") or ""
    segments = [s for s in path.strip("/").split("/") if s]
    if segments:
        tenant = service.get_tenant(segments[0])
        if tenant:
            return tenant

    return None


def require_tenant(
    fn: Optional[Callable] = None,
    *,
    service: Optional[TenantService] = None,
) -> Callable:
    """Decorator that resolves the current tenant and injects it as ``current_tenant``.

    Supports both sync and async handler functions.

    Args:
        fn: The handler function (when used without arguments: ``@require_tenant``).
        service: Optional ``TenantService`` instance. A default stateless
            instance is used when not provided.

    Raises:
        TenantError(404): If no tenant could be resolved from the request.
        TenantError(403): If the resolved tenant is inactive.

    Example::

        @require_tenant
        async def dashboard(request, current_tenant):
            return {"tenant": current_tenant.name}

        # or with an explicit service:
        svc = TenantService()

        @require_tenant(service=svc)
        async def dashboard(request, current_tenant):
            ...
    """
    _service = service or TenantService()

    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                request = args[0] if args else kwargs.get("request")
                tenant = _resolve_tenant_from_request(request, _service)
                if not tenant:
                    raise TenantError("Tenant not found", 404)
                if not tenant.is_active:
                    raise TenantError("Tenant is inactive", 403)
                kwargs["current_tenant"] = tenant
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                request = args[0] if args else kwargs.get("request")
                tenant = _resolve_tenant_from_request(request, _service)
                if not tenant:
                    raise TenantError("Tenant not found", 404)
                if not tenant.is_active:
                    raise TenantError("Tenant is inactive", 403)
                kwargs["current_tenant"] = tenant
                return func(*args, **kwargs)
            return sync_wrapper

    # Support bare @require_tenant (no parentheses)
    if fn is not None:
        return decorator(fn)
    return decorator


def require_tenant_role(
    *roles: str,
    service: Optional[TenantService] = None,
) -> Callable:
    """Decorator factory that enforces tenant-scoped role membership.

    Must be applied *after* ``@require_tenant`` (i.e. closer to the
    function body) so that ``current_tenant`` is already in kwargs.
    Also requires ``current_user`` in kwargs (from an auth decorator or
    set manually) with a ``id`` or ``user_id`` attribute.

    Args:
        *roles: One or more allowed role names within the tenant.
        service: Optional ``TenantService`` instance.

    Raises:
        TenantError(401): If ``current_user`` is not in kwargs.
        TenantError(403): If the current user's role is not in ``roles``.

    Example::

        @require_tenant
        @require_tenant_role("admin", "owner")
        async def admin_panel(request, current_tenant, current_user):
            ...
    """
    _service = service or TenantService()

    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                current_tenant = kwargs.get("current_tenant")
                current_user = kwargs.get("current_user")
                if current_user is None:
                    raise TenantError("Authentication required", 401)
                # Resolve user_id from common attribute names
                user_id = (
                    getattr(current_user, "id", None)
                    or getattr(current_user, "user_id", None)
                    or getattr(current_user, "sub", None)
                )
                if not user_id:
                    raise TenantError("Cannot determine user identity", 401)
                tenant_id = getattr(current_tenant, "id", None) if current_tenant else None
                if not tenant_id:
                    raise TenantError("Tenant not resolved", 404)
                member = _service.get_member(tenant_id, user_id)
                if not member or not member.is_active:
                    raise TenantError("User is not a member of this tenant", 403)
                if member.role not in roles:
                    raise TenantError(
                        f"Requires one of roles: {', '.join(roles)}", 403
                    )
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                current_tenant = kwargs.get("current_tenant")
                current_user = kwargs.get("current_user")
                if current_user is None:
                    raise TenantError("Authentication required", 401)
                user_id = (
                    getattr(current_user, "id", None)
                    or getattr(current_user, "user_id", None)
                    or getattr(current_user, "sub", None)
                )
                if not user_id:
                    raise TenantError("Cannot determine user identity", 401)
                tenant_id = getattr(current_tenant, "id", None) if current_tenant else None
                if not tenant_id:
                    raise TenantError("Tenant not resolved", 404)
                member = _service.get_member(tenant_id, user_id)
                if not member or not member.is_active:
                    raise TenantError("User is not a member of this tenant", 403)
                if member.role not in roles:
                    raise TenantError(
                        f"Requires one of roles: {', '.join(roles)}", 403
                    )
                return func(*args, **kwargs)
            return sync_wrapper

    return decorator
