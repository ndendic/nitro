"""
nitro.multitenancy — Entity definitions for tenant isolation.

Provides three entities:
- Tenant          : An organisation / workspace in a multi-tenant SaaS system.
- TenantMember    : A user's membership in a tenant (with a role).
- TenantInvitation: A pending invitation to join a tenant.

All entities use the standard Nitro Active Record pattern (SQLModel-backed
Entity base class). Table names are prefixed with ``mt_`` to avoid collisions.
"""

from __future__ import annotations

import json
from typing import List, Optional

from nitro.domain.entities.base_entity import Entity
from sqlmodel import Field


class Tenant(Entity, table=True):
    """An organisation or workspace in a multi-tenant application.

    Attributes:
        name: Human-readable display name.
        slug: URL-safe unique identifier (e.g. ``"acme-corp"``).
        plan: Subscription plan (e.g. ``"free"``, ``"pro"``).
        is_active: Whether the tenant is currently active.
        max_members: Maximum number of members allowed.
        settings_json: JSON-encoded tenant-specific settings blob.
    """

    __tablename__ = "mt_tenants"

    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    plan: str = "free"
    is_active: bool = True
    max_members: int = 10
    settings_json: str = "{}"

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def settings(self) -> dict:
        """Return the tenant settings as a parsed dict."""
        try:
            return json.loads(self.settings_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def member_count(self) -> int:
        """Return the number of active members in this tenant."""
        members = TenantMember.where(
            TenantMember.tenant_id == self.id,
            TenantMember.is_active == True,  # noqa: E712
        )
        return len(members) if members else 0

    @property
    def is_full(self) -> bool:
        """Return True if the tenant has reached its member limit."""
        return self.member_count >= self.max_members

    # ------------------------------------------------------------------
    # Class methods
    # ------------------------------------------------------------------

    @classmethod
    def get_by_slug(cls, slug: str) -> Optional["Tenant"]:
        """Look up a Tenant by its URL-safe slug.

        Args:
            slug: The slug to search for.

        Returns:
            The matching Tenant, or None if not found.
        """
        results = cls.find_by(slug=slug)
        if not results:
            return None
        return results[0] if isinstance(results, list) else results

    # ------------------------------------------------------------------
    # Instance methods
    # ------------------------------------------------------------------

    def get_members(self) -> List["TenantMember"]:
        """Return all active member records for this tenant."""
        return TenantMember.where(
            TenantMember.tenant_id == self.id,
            TenantMember.is_active == True,  # noqa: E712
        ) or []

    def deactivate(self) -> None:
        """Mark the tenant as inactive and persist the change."""
        self.is_active = False
        self.save()

    def activate(self) -> None:
        """Mark the tenant as active and persist the change."""
        self.is_active = True
        self.save()

    def __repr__(self) -> str:
        return f"<Tenant {self.slug!r}>"


class TenantMember(Entity, table=True):
    """A user's membership within a specific tenant.

    Attributes:
        tenant_id: Foreign key to ``mt_tenants.id``.
        user_id: The user's identifier (from the application's user system).
        role: The user's role within this tenant (e.g. ``"admin"``, ``"member"``).
        is_active: Whether this membership is currently active.
    """

    __tablename__ = "mt_members"

    tenant_id: str = Field(index=True)
    user_id: str = Field(index=True)
    role: str = "member"
    is_active: bool = True

    # ------------------------------------------------------------------
    # Class methods
    # ------------------------------------------------------------------

    @classmethod
    def get_by_user_and_tenant(
        cls, user_id: str, tenant_id: str
    ) -> Optional["TenantMember"]:
        """Find a membership record for a specific user+tenant combination.

        Args:
            user_id: The user's identifier.
            tenant_id: The tenant's ID.

        Returns:
            The matching TenantMember, or None.
        """
        results = cls.where(
            cls.user_id == user_id,
            cls.tenant_id == tenant_id,
        )
        if not results:
            return None
        return results[0]

    def __repr__(self) -> str:
        return (
            f"<TenantMember tenant={self.tenant_id!r} user={self.user_id!r} "
            f"role={self.role!r}>"
        )


class TenantInvitation(Entity, table=True):
    """A pending invitation for a user to join a tenant.

    Attributes:
        tenant_id: The tenant the invitation is for.
        email: Email address of the invitee.
        role: Role that will be assigned when the invitation is accepted.
        token: Secure random token used to accept the invitation.
        status: Invitation status: ``"pending"``, ``"accepted"``, or ``"expired"``.
        invited_by: User ID of the person who sent the invitation.
    """

    __tablename__ = "mt_invitations"

    tenant_id: str = Field(index=True)
    email: str = Field(index=True)
    role: str = "member"
    token: str = Field(unique=True, index=True)
    status: str = "pending"
    invited_by: str = ""

    # ------------------------------------------------------------------
    # Class methods
    # ------------------------------------------------------------------

    @classmethod
    def get_by_token(cls, token: str) -> Optional["TenantInvitation"]:
        """Find an invitation by its unique token.

        Args:
            token: The invitation token to look up.

        Returns:
            The matching TenantInvitation, or None.
        """
        results = cls.find_by(token=token)
        if not results:
            return None
        return results[0] if isinstance(results, list) else results

    # ------------------------------------------------------------------
    # Instance methods
    # ------------------------------------------------------------------

    def accept(self) -> None:
        """Mark the invitation as accepted and persist the change."""
        self.status = "accepted"
        self.save()

    def expire(self) -> None:
        """Mark the invitation as expired and persist the change."""
        self.status = "expired"
        self.save()

    def __repr__(self) -> str:
        return (
            f"<TenantInvitation tenant={self.tenant_id!r} email={self.email!r} "
            f"status={self.status!r}>"
        )
