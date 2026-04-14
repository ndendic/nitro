"""
nitro.multitenancy — TenantService.

Stateless service for managing tenants, members, and invitations.
All data is persisted via Entity (SQLModel Active Record).

The service intentionally holds no state — create one instance and share
it, or instantiate per-request; behaviour is identical.
"""

from __future__ import annotations

import secrets
from typing import List, Optional

from .models import Tenant, TenantInvitation, TenantMember


class TenantService:
    """Manages tenants, memberships, and invitation flows.

    Example::

        svc = TenantService()

        # Create a tenant
        tenant = svc.create_tenant("Acme Corp", slug="acme")

        # Add a member
        member = svc.add_member(tenant.id, user_id="user-1", role="admin")

        # Invite someone
        invitation = svc.create_invitation(tenant.id, "bob@example.com")

        # Accept the invitation (when the user follows the invite link)
        member = svc.accept_invitation(invitation.token, user_id="user-2")
    """

    # ------------------------------------------------------------------
    # Tenant management
    # ------------------------------------------------------------------

    def create_tenant(
        self,
        name: str,
        slug: str,
        plan: str = "free",
        max_members: int = 10,
    ) -> Tenant:
        """Create and persist a new tenant.

        Args:
            name: Human-readable display name.
            slug: URL-safe unique identifier.
            plan: Subscription plan (default ``"free"``).
            max_members: Maximum number of active members allowed.

        Returns:
            The newly created Tenant.

        Raises:
            ValueError: If a tenant with the given slug already exists.
        """
        existing = Tenant.get_by_slug(slug)
        if existing:
            raise ValueError(f"Tenant with slug {slug!r} already exists")
        tenant = Tenant(name=name, slug=slug, plan=plan, max_members=max_members)
        tenant.save()
        return tenant

    def get_tenant(self, slug: str) -> Optional[Tenant]:
        """Fetch a tenant by slug.

        Args:
            slug: The URL-safe tenant identifier.

        Returns:
            The matching Tenant, or None.
        """
        return Tenant.get_by_slug(slug)

    def deactivate_tenant(self, slug: str) -> bool:
        """Deactivate a tenant by slug.

        Args:
            slug: The tenant slug.

        Returns:
            True if the tenant was found and deactivated, False otherwise.
        """
        tenant = Tenant.get_by_slug(slug)
        if not tenant:
            return False
        tenant.deactivate()
        return True

    # ------------------------------------------------------------------
    # Member management
    # ------------------------------------------------------------------

    def add_member(
        self, tenant_id: str, user_id: str, role: str = "member"
    ) -> TenantMember:
        """Add a user to a tenant.

        Args:
            tenant_id: The ID of the target tenant.
            user_id: The user's identifier.
            role: Role within the tenant (default ``"member"``).

        Returns:
            The newly created TenantMember.

        Raises:
            ValueError: If the tenant does not exist, is inactive, or is full.
            ValueError: If the user is already an active member.
        """
        tenant = Tenant.get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id!r} not found")
        if not tenant.is_active:
            raise ValueError(f"Tenant {tenant_id!r} is not active")
        if tenant.is_full:
            raise ValueError(
                f"Tenant {tenant_id!r} has reached its member limit ({tenant.max_members})"
            )

        existing = TenantMember.get_by_user_and_tenant(user_id, tenant_id)
        if existing and existing.is_active:
            raise ValueError(
                f"User {user_id!r} is already a member of tenant {tenant_id!r}"
            )

        member = TenantMember(tenant_id=tenant_id, user_id=user_id, role=role)
        member.save()
        return member

    def remove_member(self, tenant_id: str, user_id: str) -> bool:
        """Remove a user from a tenant (soft-delete: marks membership inactive).

        Args:
            tenant_id: The tenant's ID.
            user_id: The user's identifier.

        Returns:
            True if the membership was found and deactivated, False otherwise.
        """
        member = TenantMember.get_by_user_and_tenant(user_id, tenant_id)
        if not member:
            return False
        member.is_active = False
        member.save()
        return True

    def get_member(self, tenant_id: str, user_id: str) -> Optional[TenantMember]:
        """Fetch the membership record for a user+tenant combination.

        Args:
            tenant_id: The tenant's ID.
            user_id: The user's identifier.

        Returns:
            The TenantMember if found, or None.
        """
        return TenantMember.get_by_user_and_tenant(user_id, tenant_id)

    def get_user_tenants(self, user_id: str) -> List[Tenant]:
        """Return all tenants that a user actively belongs to.

        Args:
            user_id: The user's identifier.

        Returns:
            List of Tenant objects (active memberships only).
        """
        memberships = TenantMember.where(
            TenantMember.user_id == user_id,
            TenantMember.is_active == True,  # noqa: E712
        ) or []
        tenants = []
        for membership in memberships:
            tenant = Tenant.get(membership.tenant_id)
            if tenant:
                tenants.append(tenant)
        return tenants

    def set_member_role(self, tenant_id: str, user_id: str, role: str) -> bool:
        """Change a member's role within a tenant.

        Args:
            tenant_id: The tenant's ID.
            user_id: The user's identifier.
            role: The new role to assign.

        Returns:
            True if the membership was found and updated, False otherwise.
        """
        member = TenantMember.get_by_user_and_tenant(user_id, tenant_id)
        if not member:
            return False
        member.role = role
        member.save()
        return True

    def get_tenant_members(self, tenant_id: str) -> List[TenantMember]:
        """Return all active members of a tenant.

        Args:
            tenant_id: The tenant's ID.

        Returns:
            List of TenantMember records.
        """
        return TenantMember.where(
            TenantMember.tenant_id == tenant_id,
            TenantMember.is_active == True,  # noqa: E712
        ) or []

    def is_tenant_admin(self, tenant_id: str, user_id: str) -> bool:
        """Check whether a user is an admin of a tenant.

        Args:
            tenant_id: The tenant's ID.
            user_id: The user's identifier.

        Returns:
            True if the user has the ``"admin"`` role in this tenant.
        """
        member = TenantMember.get_by_user_and_tenant(user_id, tenant_id)
        if not member or not member.is_active:
            return False
        return member.role == "admin"

    # ------------------------------------------------------------------
    # Invitation management
    # ------------------------------------------------------------------

    def create_invitation(
        self,
        tenant_id: str,
        email: str,
        role: str = "member",
        invited_by: str = "",
    ) -> TenantInvitation:
        """Create a new invitation for a user to join a tenant.

        Generates a cryptographically secure random token. If a pending
        invitation for the same email+tenant already exists it is expired
        and a new one is issued.

        Args:
            tenant_id: The tenant to invite the user to.
            email: Email address of the invitee.
            role: Role to assign when the invitation is accepted.
            invited_by: User ID of the inviter (optional).

        Returns:
            The newly created TenantInvitation.
        """
        # Expire any existing pending invitations for this email+tenant
        existing = TenantInvitation.where(
            TenantInvitation.tenant_id == tenant_id,
            TenantInvitation.email == email,
            TenantInvitation.status == "pending",
        ) or []
        for inv in existing:
            inv.expire()

        token = secrets.token_urlsafe(32)
        invitation = TenantInvitation(
            tenant_id=tenant_id,
            email=email,
            role=role,
            token=token,
            invited_by=invited_by,
        )
        invitation.save()
        return invitation

    def accept_invitation(
        self, token: str, user_id: str
    ) -> Optional[TenantMember]:
        """Accept a pending invitation and create a tenant membership.

        Validates that the invitation exists, is still pending, and that
        the target tenant has capacity. Marks the invitation as accepted.

        Args:
            token: The invitation token from the invite link.
            user_id: The user accepting the invitation.

        Returns:
            The newly created TenantMember, or None if the invitation
            was not found, is not pending, or the tenant is inactive / full.
        """
        invitation = TenantInvitation.get_by_token(token)
        if not invitation or invitation.status != "pending":
            return None

        tenant = Tenant.get(invitation.tenant_id)
        if not tenant or not tenant.is_active:
            return None

        if tenant.is_full:
            return None

        invitation.accept()
        member = TenantMember(
            tenant_id=invitation.tenant_id,
            user_id=user_id,
            role=invitation.role,
        )
        member.save()
        return member
