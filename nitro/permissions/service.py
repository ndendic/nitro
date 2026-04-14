"""
Nitro Permissions — PermissionService.

Stateless service for managing roles, permissions, and user authorization
checks. All data is persisted via Entity (SQLModel Active Record).

The ``user`` parameter in permission-checking methods accepts any object
with a ``role_list`` property that returns a list of role name strings —
making it compatible with ``nitro.auth.User`` out of the box.
"""

from __future__ import annotations

from typing import Any, List, Optional

from .models import Permission, Role, RolePermission


class PermissionService:
    """Manages roles, permissions, and user authorisation checks.

    This service is intentionally stateless — all data lives in the
    database via Entity persistence. Instantiate it once and share the
    instance, or create a new one per request; behaviour is identical.

    Example::

        svc = PermissionService()

        # Set up roles and permissions
        svc.create_permission("post", "create", "Create blog posts")
        editor = svc.create_role("editor", permissions=[("post", "create")])

        # Assign to user (auth.User with role_list property)
        user.add_role("editor")
        user.save()

        # Check at runtime
        if svc.user_has_permission(user, "post", "create"):
            ...
    """

    # ------------------------------------------------------------------
    # Role management
    # ------------------------------------------------------------------

    def create_role(
        self,
        name: str,
        description: str = "",
        permissions: Optional[List[tuple[str, str]]] = None,
    ) -> Role:
        """Create a new role, optionally with an initial set of permissions.

        If a role with ``name`` already exists it is returned unchanged
        (idempotent). Permissions are tuples of ``(resource, action)``
        and are created automatically if they don't exist.

        Args:
            name: Unique role name (e.g. ``"editor"``).
            description: Human-readable description.
            permissions: Optional list of ``(resource, action)`` tuples to
                assign immediately.

        Returns:
            The created or existing Role.
        """
        existing = Role.get_by_name(name)
        if existing:
            role = existing
        else:
            role = Role(name=name, description=description)
            role.save()

        for resource, action in (permissions or []):
            role.add_permission(resource, action)

        return role

    def create_permission(
        self,
        resource: str,
        action: str,
        description: str = "",
    ) -> Permission:
        """Create a new permission or return the existing one.

        Permissions are uniquely identified by their ``(resource, action)``
        pair. This method is idempotent — calling it twice with the same
        arguments returns the same permission.

        Args:
            resource: The resource being governed (e.g. ``"post"``).
            action: The action being allowed (e.g. ``"create"``).
            description: Optional human-readable description.

        Returns:
            The created or existing Permission.
        """
        return Permission.get_or_create(resource, action, description)

    def get_role(self, name: str) -> Optional[Role]:
        """Fetch a role by name.

        Args:
            name: The role name to look up.

        Returns:
            The Role if found, or None.
        """
        return Role.get_by_name(name)

    # ------------------------------------------------------------------
    # Permission assignment / revocation
    # ------------------------------------------------------------------

    def assign_permission_to_role(
        self, role_name: str, resource: str, action: str
    ) -> bool:
        """Grant a permission to a role.

        Creates the permission if it doesn't already exist.

        Args:
            role_name: The name of the role to update.
            resource: The resource being governed.
            action: The action being allowed.

        Returns:
            True if the assignment was added, False if it already existed or
            the role was not found.
        """
        role = Role.get_by_name(role_name)
        if not role:
            return False
        return role.add_permission(resource, action)

    def revoke_permission_from_role(
        self, role_name: str, resource: str, action: str
    ) -> bool:
        """Revoke a permission from a role.

        Args:
            role_name: The name of the role to update.
            resource: The resource being governed.
            action: The action being revoked.

        Returns:
            True if the permission was removed, False if the role or assignment
            was not found.
        """
        role = Role.get_by_name(role_name)
        if not role:
            return False
        return role.remove_permission(resource, action)

    # ------------------------------------------------------------------
    # User permission checks
    # ------------------------------------------------------------------

    def user_has_permission(
        self, user: Any, resource: str, action: str
    ) -> bool:
        """Check whether a user has a specific permission through any of their roles.

        If the user has ``is_superuser=True``, this always returns True.

        Args:
            user: Any object with a ``role_list`` property returning
                  a list of role name strings. Compatible with
                  ``nitro.auth.User`` and ``nitro.auth.TokenPayload``.
            resource: The resource to check.
            action: The action to check.

        Returns:
            True if any of the user's roles grants the permission, False
            otherwise.
        """
        # Superuser bypass
        if getattr(user, "is_superuser", False):
            return True

        role_names: List[str] = getattr(user, "role_list", []) or []
        if not role_names:
            return False

        perm = Permission.check(resource, action)
        if not perm:
            return False

        for role_name in role_names:
            role = Role.get_by_name(role_name)
            if role and role.has_permission(resource, action):
                return True
        return False

    def get_user_permissions(self, user: Any) -> List[Permission]:
        """Return all permissions a user holds through their combined roles.

        If the user has ``is_superuser=True``, all permissions in the system
        are returned.

        Args:
            user: Any object with a ``role_list`` property.

        Returns:
            Deduplicated list of Permission objects.
        """
        if getattr(user, "is_superuser", False):
            return Permission.all()

        role_names: List[str] = getattr(user, "role_list", []) or []
        seen_ids: set[str] = set()
        permissions: List[Permission] = []

        for role_name in role_names:
            role = Role.get_by_name(role_name)
            if not role:
                continue
            for perm in role.permission_list:
                if perm.id not in seen_ids:
                    seen_ids.add(perm.id)
                    permissions.append(perm)

        return permissions

    def get_role_permissions(self, role_name: str) -> List[Permission]:
        """Return all permissions assigned to a named role.

        Args:
            role_name: The name of the role to inspect.

        Returns:
            List of Permission objects, or empty list if role not found.
        """
        role = Role.get_by_name(role_name)
        if not role:
            return []
        return role.permission_list
