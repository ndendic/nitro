"""
nitro.permissions — Fine-grained RBAC permission system for Nitro.

Provides resource:action permissions, role management, and framework-agnostic
decorators that integrate seamlessly with the existing ``nitro.auth`` module.

Quick start::

    from nitro.permissions import (
        Permission, Role, PermissionService,
        require_permission, require_any_permission, require_all_permissions,
    )
    from nitro.auth import AuthService, require_auth

    auth = AuthService(secret="change-me")
    svc = PermissionService()

    # Create roles and permissions
    svc.create_permission("post", "create", "Create blog posts")
    svc.create_permission("post", "delete", "Delete blog posts")
    svc.create_role("editor", permissions=[("post", "create")])
    svc.create_role("admin", permissions=[("post", "create"), ("post", "delete")])

    # Assign role to user (auth.User)
    user.add_role("editor")
    user.save()

    # Protect a route
    @require_auth(auth)
    @require_permission("post", "create", service=svc)
    async def create_post(request, current_user):
        ...

    # Check programmatically
    if svc.user_has_permission(user, "post", "delete"):
        ...
"""

from .models import Permission, Role, RolePermission
from .service import PermissionService
from .decorators import (
    PermissionError,
    require_permission,
    require_any_permission,
    require_all_permissions,
)

__all__ = [
    "Permission",
    "Role",
    "RolePermission",
    "PermissionService",
    "PermissionError",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
]
