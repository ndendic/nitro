"""
Tests for nitro.multitenancy — tenant isolation for SaaS applications.

Covers:
- Tenant, TenantMember, TenantInvitation entity CRUD and domain logic
- TenantContext: set/get/clear, context manager, async isolation
- TenantService: full API (create, members, invitations, limits, edge cases)
- require_tenant decorator: tenant resolution from ctx / header / path
- require_tenant_role decorator: role enforcement
- Edge cases: duplicate slugs, inactive tenants, expired invitations, full tenants
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from nitro.multitenancy import (
    Tenant,
    TenantContext,
    TenantError,
    TenantInvitation,
    TenantMember,
    TenantService,
    require_tenant,
    require_tenant_role,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    *,
    ctx_tenant_id: str = None,
    header_tenant_id: str = None,
    path: str = "/",
):
    """Build a lightweight mock request object."""
    req = MagicMock()
    req.path = path
    req.ctx = MagicMock()
    req.ctx.tenant_id = ctx_tenant_id
    if header_tenant_id:
        req.headers = {"X-Tenant-ID": header_tenant_id}
    else:
        req.headers = {}
    return req


def _make_user(user_id: str = "user-1"):
    user = MagicMock()
    user.id = user_id
    return user


# ---------------------------------------------------------------------------
# TestTenantModel
# ---------------------------------------------------------------------------


class TestTenantModel:
    def test_create_and_save(self, test_repository):
        tenant = Tenant(name="Acme Corp", slug="acme")
        tenant.save()
        loaded = Tenant.get(tenant.id)
        assert loaded is not None
        assert loaded.slug == "acme"
        assert loaded.name == "Acme Corp"

    def test_defaults(self, test_repository):
        tenant = Tenant(name="T", slug="t")
        assert tenant.plan == "free"
        assert tenant.is_active is True
        assert tenant.max_members == 10
        assert tenant.settings_json == "{}"

    def test_get_by_slug(self, test_repository):
        tenant = Tenant(name="Beta", slug="beta")
        tenant.save()
        found = Tenant.get_by_slug("beta")
        assert found is not None
        assert found.id == tenant.id

    def test_get_by_slug_not_found(self, test_repository):
        result = Tenant.get_by_slug("nonexistent-slug")
        assert result is None

    def test_settings_property_default(self, test_repository):
        tenant = Tenant(name="X", slug="x-1")
        assert tenant.settings == {}

    def test_settings_property_with_data(self, test_repository):
        import json
        tenant = Tenant(name="Y", slug="y-1", settings_json=json.dumps({"theme": "dark"}))
        tenant.save()
        loaded = Tenant.get(tenant.id)
        assert loaded.settings == {"theme": "dark"}

    def test_settings_property_invalid_json(self, test_repository):
        tenant = Tenant(name="Z", slug="z-1", settings_json="not-json")
        assert tenant.settings == {}

    def test_member_count_zero(self, test_repository):
        tenant = Tenant(name="Empty", slug="empty-mc")
        tenant.save()
        assert tenant.member_count == 0

    def test_member_count_with_members(self, test_repository):
        tenant = Tenant(name="Full", slug="full-mc")
        tenant.save()
        TenantMember(tenant_id=tenant.id, user_id="u1").save()
        TenantMember(tenant_id=tenant.id, user_id="u2").save()
        assert tenant.member_count == 2

    def test_member_count_excludes_inactive(self, test_repository):
        tenant = Tenant(name="Mixed", slug="mixed-mc")
        tenant.save()
        TenantMember(tenant_id=tenant.id, user_id="u1", is_active=True).save()
        TenantMember(tenant_id=tenant.id, user_id="u2", is_active=False).save()
        assert tenant.member_count == 1

    def test_is_full_false(self, test_repository):
        tenant = Tenant(name="NotFull", slug="notfull", max_members=5)
        tenant.save()
        assert not tenant.is_full

    def test_is_full_true(self, test_repository):
        tenant = Tenant(name="AtLimit", slug="atlimit", max_members=1)
        tenant.save()
        TenantMember(tenant_id=tenant.id, user_id="u1").save()
        assert tenant.is_full

    def test_deactivate(self, test_repository):
        tenant = Tenant(name="Deactivate", slug="deactivate-me")
        tenant.save()
        tenant.deactivate()
        loaded = Tenant.get(tenant.id)
        assert loaded.is_active is False

    def test_activate(self, test_repository):
        tenant = Tenant(name="Activate", slug="activate-me", is_active=False)
        tenant.save()
        tenant.activate()
        loaded = Tenant.get(tenant.id)
        assert loaded.is_active is True

    def test_get_members_returns_list(self, test_repository):
        tenant = Tenant(name="Members", slug="has-members")
        tenant.save()
        TenantMember(tenant_id=tenant.id, user_id="ua").save()
        TenantMember(tenant_id=tenant.id, user_id="ub").save()
        members = tenant.get_members()
        assert len(members) == 2

    def test_get_members_excludes_inactive(self, test_repository):
        tenant = Tenant(name="Inactive", slug="inactive-members")
        tenant.save()
        TenantMember(tenant_id=tenant.id, user_id="ua", is_active=True).save()
        TenantMember(tenant_id=tenant.id, user_id="ub", is_active=False).save()
        members = tenant.get_members()
        assert len(members) == 1
        assert members[0].user_id == "ua"

    def test_delete(self, test_repository):
        tenant = Tenant(name="ToDelete", slug="to-delete")
        tenant.save()
        tid = tenant.id
        tenant.delete()
        assert Tenant.get(tid) is None

    def test_repr(self, test_repository):
        tenant = Tenant(name="Repr", slug="repr-slug")
        assert "repr-slug" in repr(tenant)


# ---------------------------------------------------------------------------
# TestTenantMemberModel
# ---------------------------------------------------------------------------


class TestTenantMemberModel:
    def test_create_and_save(self, test_repository):
        tenant = Tenant(name="MT", slug="mt-member")
        tenant.save()
        member = TenantMember(tenant_id=tenant.id, user_id="u1")
        member.save()
        loaded = TenantMember.get(member.id)
        assert loaded is not None
        assert loaded.user_id == "u1"
        assert loaded.tenant_id == tenant.id

    def test_defaults(self, test_repository):
        member = TenantMember(tenant_id="t1", user_id="u1")
        assert member.role == "member"
        assert member.is_active is True

    def test_get_by_user_and_tenant_found(self, test_repository):
        tenant = Tenant(name="GT", slug="gt-find")
        tenant.save()
        member = TenantMember(tenant_id=tenant.id, user_id="u-find")
        member.save()
        found = TenantMember.get_by_user_and_tenant("u-find", tenant.id)
        assert found is not None
        assert found.id == member.id

    def test_get_by_user_and_tenant_not_found(self, test_repository):
        result = TenantMember.get_by_user_and_tenant("ghost", "ghost-tenant")
        assert result is None

    def test_role_can_be_admin(self, test_repository):
        member = TenantMember(tenant_id="t1", user_id="u2", role="admin")
        member.save()
        loaded = TenantMember.get(member.id)
        assert loaded.role == "admin"

    def test_delete(self, test_repository):
        member = TenantMember(tenant_id="t1", user_id="u3")
        member.save()
        mid = member.id
        member.delete()
        assert TenantMember.get(mid) is None

    def test_repr(self, test_repository):
        member = TenantMember(tenant_id="t1", user_id="u-repr", role="viewer")
        assert "t1" in repr(member)
        assert "u-repr" in repr(member)
        assert "viewer" in repr(member)


# ---------------------------------------------------------------------------
# TestTenantInvitationModel
# ---------------------------------------------------------------------------


class TestTenantInvitationModel:
    def test_create_and_save(self, test_repository):
        inv = TenantInvitation(
            tenant_id="t1", email="bob@example.com", token="tok-1"
        )
        inv.save()
        loaded = TenantInvitation.get(inv.id)
        assert loaded is not None
        assert loaded.email == "bob@example.com"
        assert loaded.token == "tok-1"

    def test_defaults(self, test_repository):
        inv = TenantInvitation(tenant_id="t1", email="x@x.com", token="t2")
        assert inv.role == "member"
        assert inv.status == "pending"
        assert inv.invited_by == ""

    def test_get_by_token_found(self, test_repository):
        inv = TenantInvitation(tenant_id="t1", email="a@a.com", token="find-tok")
        inv.save()
        found = TenantInvitation.get_by_token("find-tok")
        assert found is not None
        assert found.id == inv.id

    def test_get_by_token_not_found(self, test_repository):
        result = TenantInvitation.get_by_token("nonexistent-token")
        assert result is None

    def test_accept(self, test_repository):
        inv = TenantInvitation(tenant_id="t1", email="c@c.com", token="accept-tok")
        inv.save()
        inv.accept()
        loaded = TenantInvitation.get(inv.id)
        assert loaded.status == "accepted"

    def test_expire(self, test_repository):
        inv = TenantInvitation(tenant_id="t1", email="d@d.com", token="expire-tok")
        inv.save()
        inv.expire()
        loaded = TenantInvitation.get(inv.id)
        assert loaded.status == "expired"

    def test_invited_by_can_be_set(self, test_repository):
        inv = TenantInvitation(
            tenant_id="t1", email="e@e.com", token="by-tok", invited_by="admin-user"
        )
        inv.save()
        loaded = TenantInvitation.get(inv.id)
        assert loaded.invited_by == "admin-user"

    def test_role_can_be_set(self, test_repository):
        inv = TenantInvitation(
            tenant_id="t1", email="f@f.com", token="role-tok", role="admin"
        )
        inv.save()
        loaded = TenantInvitation.get(inv.id)
        assert loaded.role == "admin"

    def test_repr(self, test_repository):
        inv = TenantInvitation(tenant_id="t1", email="g@g.com", token="repr-tok")
        assert "t1" in repr(inv)
        assert "g@g.com" in repr(inv)
        assert "pending" in repr(inv)

    def test_delete(self, test_repository):
        inv = TenantInvitation(tenant_id="t1", email="h@h.com", token="del-tok")
        inv.save()
        iid = inv.id
        inv.delete()
        assert TenantInvitation.get(iid) is None


# ---------------------------------------------------------------------------
# TestTenantContext
# ---------------------------------------------------------------------------


class TestTenantContext:
    def test_set_and_get(self):
        TenantContext.clear()
        TenantContext.set("tenant-abc")
        assert TenantContext.get() == "tenant-abc"
        TenantContext.clear()

    def test_clear(self):
        TenantContext.set("something")
        TenantContext.clear()
        assert TenantContext.get() is None

    def test_default_is_none(self):
        TenantContext.clear()
        assert TenantContext.get() is None

    def test_scope_context_manager(self):
        TenantContext.clear()
        with TenantContext.scope("scoped-tenant"):
            assert TenantContext.get() == "scoped-tenant"
        assert TenantContext.get() is None

    def test_scope_restores_previous_value(self):
        TenantContext.set("outer")
        with TenantContext.scope("inner"):
            assert TenantContext.get() == "inner"
        assert TenantContext.get() == "outer"
        TenantContext.clear()

    def test_scope_restores_on_exception(self):
        TenantContext.set("before")
        with pytest.raises(RuntimeError):
            with TenantContext.scope("during"):
                raise RuntimeError("test")
        assert TenantContext.get() == "before"
        TenantContext.clear()

    def test_nested_scope(self):
        TenantContext.clear()
        with TenantContext.scope("outer"):
            with TenantContext.scope("inner"):
                assert TenantContext.get() == "inner"
            assert TenantContext.get() == "outer"
        assert TenantContext.get() is None

    def test_async_isolation(self):
        """Verify that ContextVar is isolated between coroutines."""

        async def task_a():
            TenantContext.set("tenant-a")
            await asyncio.sleep(0)
            return TenantContext.get()

        async def task_b():
            TenantContext.set("tenant-b")
            await asyncio.sleep(0)
            return TenantContext.get()

        async def run():
            results = await asyncio.gather(task_a(), task_b())
            return results

        results = asyncio.run(run())
        # Each coroutine should see its own value
        assert "tenant-a" in results
        assert "tenant-b" in results

    def test_set_returns_token(self):
        """set() returns a Token that can be used to reset."""
        TenantContext.clear()
        token = TenantContext.set("with-token")
        assert token is not None
        TenantContext.clear()


# ---------------------------------------------------------------------------
# TestTenantService
# ---------------------------------------------------------------------------


class TestTenantService:
    def test_create_tenant(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Org One", slug="org-one")
        assert tenant.id is not None
        assert tenant.name == "Org One"
        assert tenant.slug == "org-one"

    def test_create_tenant_with_options(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Pro Org", slug="pro-org", plan="pro", max_members=50)
        assert tenant.plan == "pro"
        assert tenant.max_members == 50

    def test_create_tenant_duplicate_slug_raises(self, test_repository):
        svc = TenantService()
        svc.create_tenant("First", slug="dup-slug")
        with pytest.raises(ValueError, match="already exists"):
            svc.create_tenant("Second", slug="dup-slug")

    def test_get_tenant_found(self, test_repository):
        svc = TenantService()
        svc.create_tenant("Findable", slug="findable")
        tenant = svc.get_tenant("findable")
        assert tenant is not None
        assert tenant.slug == "findable"

    def test_get_tenant_not_found(self, test_repository):
        svc = TenantService()
        assert svc.get_tenant("ghost-tenant") is None

    def test_deactivate_tenant(self, test_repository):
        svc = TenantService()
        svc.create_tenant("ToDeactivate", slug="to-deactivate-svc")
        result = svc.deactivate_tenant("to-deactivate-svc")
        assert result is True
        tenant = svc.get_tenant("to-deactivate-svc")
        assert tenant.is_active is False

    def test_deactivate_tenant_not_found(self, test_repository):
        svc = TenantService()
        result = svc.deactivate_tenant("nonexistent")
        assert result is False

    def test_add_member(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Addme", slug="addme")
        member = svc.add_member(tenant.id, user_id="user-add", role="admin")
        assert member.id is not None
        assert member.user_id == "user-add"
        assert member.role == "admin"

    def test_add_member_tenant_not_found_raises(self, test_repository):
        svc = TenantService()
        with pytest.raises(ValueError, match="not found"):
            svc.add_member("nonexistent-id", user_id="u1")

    def test_add_member_inactive_tenant_raises(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Inactive", slug="inactive-add", )
        tenant.deactivate()
        with pytest.raises(ValueError, match="not active"):
            svc.add_member(tenant.id, user_id="u1")

    def test_add_member_full_tenant_raises(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Full", slug="full-add", max_members=1)
        svc.add_member(tenant.id, user_id="u1")
        with pytest.raises(ValueError, match="member limit"):
            svc.add_member(tenant.id, user_id="u2")

    def test_add_member_duplicate_raises(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("DupMember", slug="dup-member-add")
        svc.add_member(tenant.id, user_id="u-dup")
        with pytest.raises(ValueError, match="already a member"):
            svc.add_member(tenant.id, user_id="u-dup")

    def test_remove_member(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Remove", slug="remove-member")
        svc.add_member(tenant.id, user_id="u-remove")
        result = svc.remove_member(tenant.id, user_id="u-remove")
        assert result is True
        member = svc.get_member(tenant.id, "u-remove")
        assert member.is_active is False

    def test_remove_member_not_found(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("NoMember", slug="no-member-remove")
        result = svc.remove_member(tenant.id, user_id="ghost")
        assert result is False

    def test_get_member_found(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("GetMember", slug="get-member")
        svc.add_member(tenant.id, user_id="u-get")
        member = svc.get_member(tenant.id, "u-get")
        assert member is not None
        assert member.user_id == "u-get"

    def test_get_member_not_found(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("NoMemberGet", slug="no-member-get")
        assert svc.get_member(tenant.id, "ghost") is None

    def test_get_user_tenants(self, test_repository):
        svc = TenantService()
        t1 = svc.create_tenant("T1", slug="user-tenants-t1")
        t2 = svc.create_tenant("T2", slug="user-tenants-t2")
        svc.add_member(t1.id, user_id="shared-user")
        svc.add_member(t2.id, user_id="shared-user")
        tenants = svc.get_user_tenants("shared-user")
        ids = {t.id for t in tenants}
        assert t1.id in ids
        assert t2.id in ids

    def test_get_user_tenants_excludes_inactive_memberships(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("UTInactive", slug="ut-inactive")
        svc.add_member(tenant.id, user_id="u-inactive-member")
        svc.remove_member(tenant.id, user_id="u-inactive-member")
        tenants = svc.get_user_tenants("u-inactive-member")
        assert all(t.id != tenant.id for t in tenants)

    def test_set_member_role(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("SetRole", slug="set-role")
        svc.add_member(tenant.id, user_id="u-role", role="member")
        result = svc.set_member_role(tenant.id, "u-role", "admin")
        assert result is True
        member = svc.get_member(tenant.id, "u-role")
        assert member.role == "admin"

    def test_set_member_role_not_found(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("SetRoleNF", slug="set-role-nf")
        result = svc.set_member_role(tenant.id, "ghost", "admin")
        assert result is False

    def test_get_tenant_members(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("GTM", slug="get-tenant-members")
        svc.add_member(tenant.id, user_id="m1")
        svc.add_member(tenant.id, user_id="m2")
        members = svc.get_tenant_members(tenant.id)
        user_ids = {m.user_id for m in members}
        assert "m1" in user_ids
        assert "m2" in user_ids

    def test_get_tenant_members_empty(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("EmptyMembers", slug="empty-members-svc")
        members = svc.get_tenant_members(tenant.id)
        assert members == []

    def test_is_tenant_admin_true(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("AdminCheck", slug="admin-check")
        svc.add_member(tenant.id, user_id="u-admin", role="admin")
        assert svc.is_tenant_admin(tenant.id, "u-admin") is True

    def test_is_tenant_admin_false_for_member(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("AdminCheckFalse", slug="admin-check-false")
        svc.add_member(tenant.id, user_id="u-member", role="member")
        assert svc.is_tenant_admin(tenant.id, "u-member") is False

    def test_is_tenant_admin_false_for_nonmember(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("AdminCheckNM", slug="admin-check-nm")
        assert svc.is_tenant_admin(tenant.id, "ghost") is False

    def test_create_invitation(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("InviteTest", slug="invite-test")
        inv = svc.create_invitation(tenant.id, "invite@example.com")
        assert inv.id is not None
        assert inv.email == "invite@example.com"
        assert inv.status == "pending"
        assert len(inv.token) > 0

    def test_create_invitation_generates_unique_tokens(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("UniqueToken", slug="unique-token")
        inv1 = svc.create_invitation(tenant.id, "a@a.com")
        inv2 = svc.create_invitation(tenant.id, "b@b.com")
        assert inv1.token != inv2.token

    def test_create_invitation_expires_previous_pending(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("ExpirePrev", slug="expire-prev")
        inv1 = svc.create_invitation(tenant.id, "same@example.com")
        inv2 = svc.create_invitation(tenant.id, "same@example.com")
        # old invitation should now be expired
        loaded1 = TenantInvitation.get(inv1.id)
        assert loaded1.status == "expired"
        # new invitation is pending
        assert inv2.status == "pending"

    def test_create_invitation_with_role_and_inviter(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("InvRole", slug="inv-role")
        inv = svc.create_invitation(
            tenant.id, "admin@example.com", role="admin", invited_by="owner-user"
        )
        assert inv.role == "admin"
        assert inv.invited_by == "owner-user"

    def test_accept_invitation(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("AcceptInv", slug="accept-inv")
        inv = svc.create_invitation(tenant.id, "new@example.com")
        member = svc.accept_invitation(inv.token, user_id="new-user")
        assert member is not None
        assert member.user_id == "new-user"
        assert member.tenant_id == tenant.id
        # invitation should be marked accepted
        loaded = TenantInvitation.get(inv.id)
        assert loaded.status == "accepted"

    def test_accept_invitation_invalid_token(self, test_repository):
        svc = TenantService()
        result = svc.accept_invitation("bad-token", user_id="u1")
        assert result is None

    def test_accept_invitation_already_accepted(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("AcceptTwice", slug="accept-twice")
        inv = svc.create_invitation(tenant.id, "twice@example.com")
        svc.accept_invitation(inv.token, user_id="u-twice")
        # accepting again should return None (status is no longer "pending")
        result = svc.accept_invitation(inv.token, user_id="u-twice-again")
        assert result is None

    def test_accept_invitation_expired(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("ExpiredAccept", slug="expired-accept")
        inv = svc.create_invitation(tenant.id, "exp@example.com")
        inv.expire()
        result = svc.accept_invitation(inv.token, user_id="u-exp")
        assert result is None

    def test_accept_invitation_inactive_tenant(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("InactiveTenant", slug="inactive-tenant-inv")
        inv = svc.create_invitation(tenant.id, "inact@example.com")
        tenant.deactivate()
        result = svc.accept_invitation(inv.token, user_id="u-inact")
        assert result is None

    def test_accept_invitation_full_tenant(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("FullTenantInv", slug="full-tenant-inv", max_members=1)
        svc.add_member(tenant.id, user_id="u-already")
        inv = svc.create_invitation(tenant.id, "over@example.com")
        result = svc.accept_invitation(inv.token, user_id="u-over")
        assert result is None


# ---------------------------------------------------------------------------
# TestRequireTenant
# ---------------------------------------------------------------------------


class TestRequireTenant:
    @pytest.mark.asyncio
    async def test_resolves_from_ctx(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("CTX Org", slug="ctx-org")
        req = _make_request(ctx_tenant_id=tenant.id)

        @require_tenant(service=svc)
        async def handler(request, current_tenant=None):
            return current_tenant

        result = await handler(req)
        assert result.id == tenant.id

    @pytest.mark.asyncio
    async def test_resolves_from_header(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Header Org", slug="header-org")
        req = _make_request(header_tenant_id=tenant.id)

        @require_tenant(service=svc)
        async def handler(request, current_tenant=None):
            return current_tenant

        result = await handler(req)
        assert result.id == tenant.id

    @pytest.mark.asyncio
    async def test_resolves_from_path_slug(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Path Org", slug="path-org")
        req = _make_request(path="/path-org/dashboard")

        @require_tenant(service=svc)
        async def handler(request, current_tenant=None):
            return current_tenant

        result = await handler(req)
        assert result.id == tenant.id

    @pytest.mark.asyncio
    async def test_raises_404_if_not_resolved(self, test_repository):
        svc = TenantService()
        req = _make_request(path="/no-such-tenant/page")

        @require_tenant(service=svc)
        async def handler(request, current_tenant=None):
            return current_tenant

        with pytest.raises(TenantError) as exc_info:
            await handler(req)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_403_if_tenant_inactive(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Inactive Org", slug="inactive-org-deco")
        tenant.deactivate()
        req = _make_request(ctx_tenant_id=tenant.id)

        @require_tenant(service=svc)
        async def handler(request, current_tenant=None):
            return current_tenant

        with pytest.raises(TenantError) as exc_info:
            await handler(req)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_injects_into_kwargs(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Inject", slug="inject-tenant")
        req = _make_request(ctx_tenant_id=tenant.id)

        @require_tenant(service=svc)
        async def handler(request, current_tenant=None):
            return current_tenant.slug

        result = await handler(req)
        assert result == "inject-tenant"

    def test_sync_handler_resolved(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("Sync Org", slug="sync-org")
        req = _make_request(ctx_tenant_id=tenant.id)

        @require_tenant(service=svc)
        def handler(request, current_tenant=None):
            return current_tenant.slug

        result = handler(req)
        assert result == "sync-org"

    def test_sync_handler_raises_404(self, test_repository):
        svc = TenantService()
        req = _make_request(path="/nonexistent/page")

        @require_tenant(service=svc)
        def handler(request, current_tenant=None):
            return "ok"

        with pytest.raises(TenantError) as exc_info:
            handler(req)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_bare_decorator_no_parens(self, test_repository):
        """@require_tenant (no parentheses) should work too."""
        svc = TenantService()
        tenant = svc.create_tenant("Bare Deco", slug="bare-deco")
        req = _make_request(ctx_tenant_id=tenant.id)

        @require_tenant
        async def handler(request, current_tenant=None):
            return current_tenant

        result = await handler(req)
        assert result.id == tenant.id

    @pytest.mark.asyncio
    async def test_ctx_tenant_id_as_slug_fallback(self, test_repository):
        """ctx.tenant_id not a valid ID — falls through to slug lookup."""
        svc = TenantService()
        tenant = svc.create_tenant("Slug Ctx", slug="slug-ctx-org")
        req = _make_request(ctx_tenant_id="slug-ctx-org")

        @require_tenant(service=svc)
        async def handler(request, current_tenant=None):
            return current_tenant

        result = await handler(req)
        assert result.id == tenant.id


# ---------------------------------------------------------------------------
# TestRequireTenantRole
# ---------------------------------------------------------------------------


class TestRequireTenantRole:
    @pytest.mark.asyncio
    async def test_passes_for_correct_role(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("RoleTest", slug="role-test")
        svc.add_member(tenant.id, user_id="admin-user", role="admin")
        user = _make_user("admin-user")
        req = _make_request()

        @require_tenant_role("admin", service=svc)
        async def handler(request, current_tenant=None, current_user=None):
            return "ok"

        result = await handler(req, current_tenant=tenant, current_user=user)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_passes_for_any_listed_role(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("MultiRole", slug="multi-role")
        svc.add_member(tenant.id, user_id="editor-user", role="editor")
        user = _make_user("editor-user")
        req = _make_request()

        @require_tenant_role("admin", "editor", "owner", service=svc)
        async def handler(request, current_tenant=None, current_user=None):
            return "ok"

        result = await handler(req, current_tenant=tenant, current_user=user)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_raises_403_for_wrong_role(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("WrongRole", slug="wrong-role")
        svc.add_member(tenant.id, user_id="plain-user", role="member")
        user = _make_user("plain-user")
        req = _make_request()

        @require_tenant_role("admin", service=svc)
        async def handler(request, current_tenant=None, current_user=None):
            return "ok"

        with pytest.raises(TenantError) as exc_info:
            await handler(req, current_tenant=tenant, current_user=user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_raises_403_for_non_member(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("NonMemberRole", slug="non-member-role")
        user = _make_user("outsider")
        req = _make_request()

        @require_tenant_role("admin", service=svc)
        async def handler(request, current_tenant=None, current_user=None):
            return "ok"

        with pytest.raises(TenantError) as exc_info:
            await handler(req, current_tenant=tenant, current_user=user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_raises_401_no_current_user(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("NoUser", slug="no-user-role")
        req = _make_request()

        @require_tenant_role("admin", service=svc)
        async def handler(request, current_tenant=None, current_user=None):
            return "ok"

        with pytest.raises(TenantError) as exc_info:
            await handler(req, current_tenant=tenant)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_403_for_inactive_member(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("InactiveMR", slug="inactive-mr")
        svc.add_member(tenant.id, user_id="u-inactive", role="admin")
        svc.remove_member(tenant.id, user_id="u-inactive")
        user = _make_user("u-inactive")
        req = _make_request()

        @require_tenant_role("admin", service=svc)
        async def handler(request, current_tenant=None, current_user=None):
            return "ok"

        with pytest.raises(TenantError) as exc_info:
            await handler(req, current_tenant=tenant, current_user=user)
        assert exc_info.value.status_code == 403

    def test_sync_handler_passes(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("SyncRole", slug="sync-role")
        svc.add_member(tenant.id, user_id="u-sync", role="admin")
        user = _make_user("u-sync")
        req = _make_request()

        @require_tenant_role("admin", service=svc)
        def handler(request, current_tenant=None, current_user=None):
            return "ok"

        result = handler(req, current_tenant=tenant, current_user=user)
        assert result == "ok"

    def test_sync_handler_raises_403(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("SyncRoleDeny", slug="sync-role-deny")
        svc.add_member(tenant.id, user_id="u-sync-deny", role="viewer")
        user = _make_user("u-sync-deny")
        req = _make_request()

        @require_tenant_role("admin", service=svc)
        def handler(request, current_tenant=None, current_user=None):
            return "ok"

        with pytest.raises(TenantError) as exc_info:
            handler(req, current_tenant=tenant, current_user=user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_error_message_contains_roles(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("MsgRoles", slug="msg-roles")
        svc.add_member(tenant.id, user_id="u-msg", role="viewer")
        user = _make_user("u-msg")

        @require_tenant_role("admin", "superadmin", service=svc)
        async def handler(request, current_tenant=None, current_user=None):
            return "ok"

        with pytest.raises(TenantError) as exc_info:
            await handler(_make_request(), current_tenant=tenant, current_user=user)
        assert "admin" in exc_info.value.message


# ---------------------------------------------------------------------------
# TestTenantError
# ---------------------------------------------------------------------------


class TestTenantError:
    def test_default_values(self):
        err = TenantError()
        assert err.status_code == 404
        assert "not found" in err.message.lower()

    def test_custom_message_and_status(self):
        err = TenantError("Forbidden", 403)
        assert err.message == "Forbidden"
        assert err.status_code == 403

    def test_is_exception(self):
        err = TenantError("test")
        assert isinstance(err, Exception)

    def test_401_status(self):
        err = TenantError("Auth required", 401)
        assert err.status_code == 401


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_slug_is_unique(self, test_repository):
        t1 = Tenant(name="A", slug="unique-slug-ec")
        t1.save()
        t2 = Tenant(name="B", slug="other-slug-ec")
        t2.save()
        found = Tenant.get_by_slug("unique-slug-ec")
        assert found.id == t1.id

    def test_inactive_tenant_is_full_not_considered(self, test_repository):
        """is_full counts only active members; inactive don't inflate the count."""
        tenant = Tenant(name="CountCheck", slug="count-check", max_members=2)
        tenant.save()
        TenantMember(tenant_id=tenant.id, user_id="u1", is_active=True).save()
        TenantMember(tenant_id=tenant.id, user_id="u2", is_active=False).save()
        assert not tenant.is_full  # only 1 active member

    def test_invitation_not_found_returns_none(self, test_repository):
        result = TenantInvitation.get_by_token("absolutely-missing")
        assert result is None

    def test_expired_invitation_cannot_be_accepted(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("ExpiredEC", slug="expired-ec")
        inv = svc.create_invitation(tenant.id, "exp-ec@example.com")
        inv.expire()
        result = svc.accept_invitation(inv.token, user_id="u-ec")
        assert result is None

    def test_reactivate_member_after_removal(self, test_repository):
        """After removing a member, they can be re-added (new record)."""
        svc = TenantService()
        tenant = svc.create_tenant("ReAdd", slug="re-add")
        svc.add_member(tenant.id, user_id="u-readd")
        svc.remove_member(tenant.id, user_id="u-readd")
        # Old record is inactive; adding again should create a new record
        member = svc.add_member(tenant.id, user_id="u-readd")
        assert member.is_active is True

    def test_multiple_tenants_separate_member_counts(self, test_repository):
        svc = TenantService()
        t1 = svc.create_tenant("T1Count", slug="t1-count")
        t2 = svc.create_tenant("T2Count", slug="t2-count")
        svc.add_member(t1.id, user_id="shared-mc")
        svc.add_member(t2.id, user_id="shared-mc")
        assert t1.member_count == 1
        assert t2.member_count == 1

    def test_deactivating_tenant_does_not_remove_members(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("DeactNoRemove", slug="deact-no-remove")
        svc.add_member(tenant.id, user_id="u-stays")
        tenant.deactivate()
        members = svc.get_tenant_members(tenant.id)
        assert len(members) == 1  # member still in DB

    def test_user_with_no_tenants(self, test_repository):
        svc = TenantService()
        tenants = svc.get_user_tenants("completely-new-user")
        assert tenants == []

    def test_invitation_role_is_respected_on_accept(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("RoleAccept", slug="role-accept")
        inv = svc.create_invitation(tenant.id, "r@r.com", role="admin")
        member = svc.accept_invitation(inv.token, user_id="u-role-accept")
        assert member is not None
        assert member.role == "admin"

    def test_context_var_does_not_leak_between_calls(self):
        TenantContext.clear()
        TenantContext.set("leak-test")
        TenantContext.clear()
        assert TenantContext.get() is None

    def test_create_invitation_with_no_inviter(self, test_repository):
        svc = TenantService()
        tenant = svc.create_tenant("NoInviter", slug="no-inviter")
        inv = svc.create_invitation(tenant.id, "ni@ni.com")
        assert inv.invited_by == ""

    def test_get_member_returns_inactive_member_too(self, test_repository):
        """get_member returns ANY membership record, active or not."""
        svc = TenantService()
        tenant = svc.create_tenant("GetMemberInactive", slug="get-member-inactive")
        svc.add_member(tenant.id, user_id="u-gmi")
        svc.remove_member(tenant.id, user_id="u-gmi")
        member = svc.get_member(tenant.id, "u-gmi")
        assert member is not None
        assert member.is_active is False
