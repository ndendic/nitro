"""
Nitro Permissions — Permission and Role entities.

Provides a structured RBAC (Role-Based Access Control) layer on top of
Nitro's Entity base class. Permissions are resource+action pairs (e.g.
"post:create"), and Roles are named collections of permissions.

Design choices:
- Roles/Permissions persist via Entity (SQLModel-backed Active Record)
- Roles reference permissions via a RolePermission join table
- Role-to-User mapping stays in auth.User.roles (comma-separated role names)
  so no schema changes to the existing auth module are required
"""

from __future__ import annotations

from typing import List, Optional

from nitro.domain.entities.base_entity import Entity
from sqlmodel import Field


class Permission(Entity, table=True):
    """A single permission defined by a resource and action pair.

    Example: resource="post", action="create" → "post:create"

    Attributes:
        resource: The resource this permission governs (e.g. "post", "user").
        action: The action allowed on that resource (e.g. "create", "delete").
        description: Human-readable description of what this permission allows.
    """

    __tablename__ = "perm_permissions"

    resource: str = Field(index=True)
    action: str = Field(index=True)
    description: str = ""

    @property
    def key(self) -> str:
        """Return the canonical permission key: ``resource:action``."""
        return f"{self.resource}:{self.action}"

    @classmethod
    def check(cls, resource: str, action: str) -> Optional["Permission"]:
        """Look up a Permission by resource and action.

        Args:
            resource: The resource to look up.
            action: The action to look up.

        Returns:
            The matching Permission, or None if not found.
        """
        results = cls.find_by(resource=resource, action=action)
        if not results:
            return None
        return results[0] if isinstance(results, list) else results

    @classmethod
    def get_or_create(cls, resource: str, action: str, description: str = "") -> "Permission":
        """Return an existing permission or create one if it doesn't exist.

        Args:
            resource: The resource name.
            action: The action name.
            description: Optional description (used only when creating).

        Returns:
            The existing or newly created Permission.
        """
        existing = cls.check(resource, action)
        if existing:
            return existing
        perm = cls(resource=resource, action=action, description=description)
        perm.save()
        return perm

    def __repr__(self) -> str:
        return f"<Permission {self.key}>"


class Role(Entity, table=True):
    """A named role that groups one or more permissions together.

    Attributes:
        name: Unique role name (e.g. "editor", "admin").
        description: Human-readable description of this role.
    """

    __tablename__ = "perm_roles"

    name: str = Field(unique=True, index=True)
    description: str = ""

    @property
    def permission_list(self) -> List[Permission]:
        """Return all permissions assigned to this role."""
        rp_entries = RolePermission.where(RolePermission.role_id == self.id)
        permissions = []
        for rp in rp_entries:
            perm = Permission.get(rp.permission_id)
            if perm:
                permissions.append(perm)
        return permissions

    def add_permission(self, resource: str, action: str) -> bool:
        """Assign a permission to this role.

        Creates the Permission if it doesn't exist yet. Does nothing if the
        assignment already exists.

        Args:
            resource: The permission resource.
            action: The permission action.

        Returns:
            True if a new assignment was created, False if it already existed.
        """
        perm = Permission.get_or_create(resource, action)
        existing = RolePermission.where(
            RolePermission.role_id == self.id,
            RolePermission.permission_id == perm.id,
        )
        if existing:
            return False
        rp = RolePermission(role_id=self.id, permission_id=perm.id)
        rp.save()
        return True

    def remove_permission(self, resource: str, action: str) -> bool:
        """Revoke a permission from this role.

        Args:
            resource: The permission resource.
            action: The permission action.

        Returns:
            True if the assignment was removed, False if it didn't exist.
        """
        perm = Permission.check(resource, action)
        if not perm:
            return False
        existing = RolePermission.where(
            RolePermission.role_id == self.id,
            RolePermission.permission_id == perm.id,
        )
        if not existing:
            return False
        for rp in existing:
            rp.delete()
        return True

    def has_permission(self, resource: str, action: str) -> bool:
        """Check whether this role grants a specific permission.

        Args:
            resource: The permission resource.
            action: The permission action.

        Returns:
            True if this role has the permission, False otherwise.
        """
        perm = Permission.check(resource, action)
        if not perm:
            return False
        result = RolePermission.where(
            RolePermission.role_id == self.id,
            RolePermission.permission_id == perm.id,
        )
        return bool(result)

    @classmethod
    def get_by_name(cls, name: str) -> Optional["Role"]:
        """Find a role by its unique name.

        Args:
            name: The role name to look up.

        Returns:
            The matching Role, or None.
        """
        results = cls.find_by(name=name)
        if not results:
            return None
        return results[0] if isinstance(results, list) else results

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class RolePermission(Entity, table=True):
    """Join table linking roles to permissions.

    Attributes:
        role_id: The ID of the Role.
        permission_id: The ID of the Permission.
    """

    __tablename__ = "perm_role_permissions"

    role_id: str = Field(index=True)
    permission_id: str = Field(index=True)

    def __repr__(self) -> str:
        return f"<RolePermission role={self.role_id} perm={self.permission_id}>"
