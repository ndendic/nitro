"""
Tests for nitro.permissions — RBAC permission system.

Covers: Permission, Role, RolePermission entities, PermissionService,
decorators (require_permission, require_any_permission, require_all_permissions),
edge cases, superuser bypass, and integration with auth.User-compatible objects.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from nitro.permissions import (
    Permission,
    PermissionError,
    PermissionService,
    Role,
    RolePermission,
    require_all_permissions,
    require_any_permission,
    require_permission,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(roles: list[str] = None, is_superuser: bool = False):
    """Create a mock user with a role_list property."""
    user = MagicMock()
    user.role_list = roles or []
    user.is_superuser = is_superuser
    return user


# ---------------------------------------------------------------------------
# Permission model
# ---------------------------------------------------------------------------


class TestPermissionModel:
    def test_create_and_save(self, test_repository):
        perm = Permission(resource="post", action="create")
        perm.save()
        loaded = Permission.get(perm.id)
        assert loaded is not None
        assert loaded.resource == "post"
        assert loaded.action == "create"

    def test_key_property(self, test_repository):
        perm = Permission(resource="user", action="delete")
        assert perm.key == "user:delete"

    def test_description_defaults_empty(self, test_repository):
        perm = Permission(resource="post", action="edit")
        assert perm.description == ""

    def test_description_can_be_set(self, test_repository):
        perm = Permission(resource="report", action="view", description="View reports")
        perm.save()
        loaded = Permission.get(perm.id)
        assert loaded.description == "View reports"

    def test_check_existing(self, test_repository):
        perm = Permission(resource="file", action="upload")
        perm.save()
        found = Permission.check("file", "upload")
        assert found is not None
        assert found.id == perm.id

    def test_check_nonexistent_returns_none(self, test_repository):
        result = Permission.check("nonexistent", "missing")
        assert result is None

    def test_get_or_create_new(self, test_repository):
        perm = Permission.get_or_create("widget", "create", "Create widgets")
        assert perm.id is not None
        assert perm.resource == "widget"
        assert perm.action == "create"
        assert perm.description == "Create widgets"

    def test_get_or_create_existing_returns_same(self, test_repository):
        perm1 = Permission.get_or_create("widget", "delete")
        perm2 = Permission.get_or_create("widget", "delete")
        assert perm1.id == perm2.id

    def test_get_or_create_does_not_overwrite_description(self, test_repository):
        perm1 = Permission.get_or_create("tag", "read", "Read tags")
        perm2 = Permission.get_or_create("tag", "read", "Different description")
        # Should return the original
        assert perm2.id == perm1.id
        assert perm2.description == "Read tags"

    def test_permission_repr(self, test_repository):
        perm = Permission(resource="post", action="view")
        assert "post:view" in repr(perm)

    def test_multiple_permissions_different_resources(self, test_repository):
        p1 = Permission.get_or_create("post", "create")
        p2 = Permission.get_or_create("user", "create")
        assert p1.id != p2.id
        assert Permission.check("post", "create") is not None
        assert Permission.check("user", "create") is not None

    def test_permission_delete(self, test_repository):
        perm = Permission(resource="temp", action="delete")
        perm.save()
        perm_id = perm.id
        perm.delete()
        assert Permission.get(perm_id) is None


# ---------------------------------------------------------------------------
# Role model
# ---------------------------------------------------------------------------


class TestRoleModel:
    def test_create_role(self, test_repository):
        role = Role(name="editor", description="Content editor")
        role.save()
        loaded = Role.get(role.id)
        assert loaded is not None
        assert loaded.name == "editor"

    def test_get_by_name_found(self, test_repository):
        role = Role(name="moderator")
        role.save()
        found = Role.get_by_name("moderator")
        assert found is not None
        assert found.id == role.id

    def test_get_by_name_not_found(self, test_repository):
        result = Role.get_by_name("ghost")
        assert result is None

    def test_role_repr(self, test_repository):
        role = Role(name="admin")
        assert "admin" in repr(role)

    def test_add_permission_creates_assignment(self, test_repository):
        role = Role(name="writer")
        role.save()
        added = role.add_permission("post", "create")
        assert added is True
        assert role.has_permission("post", "create")

    def test_add_permission_idempotent(self, test_repository):
        role = Role(name="writer2")
        role.save()
        role.add_permission("post", "edit")
        added_again = role.add_permission("post", "edit")
        assert added_again is False

    def test_remove_permission_removes_assignment(self, test_repository):
        role = Role(name="eraser")
        role.save()
        role.add_permission("post", "publish")
        removed = role.remove_permission("post", "publish")
        assert removed is True
        assert not role.has_permission("post", "publish")

    def test_remove_nonexistent_permission_returns_false(self, test_repository):
        role = Role(name="empty_role")
        role.save()
        result = role.remove_permission("post", "nonexistent")
        assert result is False

    def test_remove_permission_for_nonexistent_perm(self, test_repository):
        role = Role(name="another_role")
        role.save()
        result = role.remove_permission("xyz", "abc")
        assert result is False

    def test_has_permission_false_when_not_assigned(self, test_repository):
        role = Role(name="viewer")
        role.save()
        assert not role.has_permission("post", "delete")

    def test_has_permission_for_unknown_perm(self, test_repository):
        role = Role(name="norole")
        role.save()
        assert not role.has_permission("unknown", "resource")

    def test_permission_list_empty(self, test_repository):
        role = Role(name="blank_role")
        role.save()
        assert role.permission_list == []

    def test_permission_list_with_permissions(self, test_repository):
        role = Role(name="super_editor")
        role.save()
        role.add_permission("post", "create")
        role.add_permission("post", "edit")
        perms = role.permission_list
        assert len(perms) == 2
        keys = {p.key for p in perms}
        assert "post:create" in keys
        assert "post:edit" in keys

    def test_add_permission_auto_creates_permission(self, test_repository):
        role = Role(name="lazy_role")
        role.save()
        # Permission doesn't exist yet
        assert Permission.check("newres", "newact") is None
        role.add_permission("newres", "newact")
        # Now it should exist
        assert Permission.check("newres", "newact") is not None


# ---------------------------------------------------------------------------
# RolePermission join table
# ---------------------------------------------------------------------------


class TestRolePermissionModel:
    def test_create_role_permission_entry(self, test_repository):
        role = Role(name="rp_role")
        role.save()
        perm = Permission(resource="rp_res", action="rp_act")
        perm.save()
        rp = RolePermission(role_id=role.id, permission_id=perm.id)
        rp.save()
        loaded = RolePermission.get(rp.id)
        assert loaded is not None
        assert loaded.role_id == role.id
        assert loaded.permission_id == perm.id

    def test_role_permission_repr(self, test_repository):
        rp = RolePermission(role_id="r1", permission_id="p1")
        assert "r1" in repr(rp)
        assert "p1" in repr(rp)

    def test_find_by_role_id(self, test_repository):
        role = Role(name="find_role")
        role.save()
        perm = Permission(resource="find_res", action="find_act")
        perm.save()
        rp = RolePermission(role_id=role.id, permission_id=perm.id)
        rp.save()
        results = RolePermission.where(RolePermission.role_id == role.id)
        assert results is not None
        assert len(results) >= 1
        assert any(e.id == rp.id for e in results)


# ---------------------------------------------------------------------------
# PermissionService
# ---------------------------------------------------------------------------


class TestPermissionService:
    def test_create_permission(self, test_repository):
        svc = PermissionService()
        perm = svc.create_permission("article", "read")
        assert perm.id is not None
        assert perm.resource == "article"
        assert perm.action == "read"

    def test_create_permission_with_description(self, test_repository):
        svc = PermissionService()
        perm = svc.create_permission("article", "write", "Write articles")
        assert perm.description == "Write articles"

    def test_create_permission_idempotent(self, test_repository):
        svc = PermissionService()
        p1 = svc.create_permission("article", "delete")
        p2 = svc.create_permission("article", "delete")
        assert p1.id == p2.id

    def test_create_role(self, test_repository):
        svc = PermissionService()
        role = svc.create_role("journalist", description="News writer")
        assert role.id is not None
        assert role.name == "journalist"

    def test_create_role_with_permissions(self, test_repository):
        svc = PermissionService()
        role = svc.create_role(
            "full_editor",
            permissions=[("article", "create"), ("article", "edit")],
        )
        keys = {p.key for p in role.permission_list}
        assert "article:create" in keys
        assert "article:edit" in keys

    def test_create_role_idempotent(self, test_repository):
        svc = PermissionService()
        r1 = svc.create_role("duplicate_role")
        r2 = svc.create_role("duplicate_role")
        assert r1.id == r2.id

    def test_get_role_found(self, test_repository):
        svc = PermissionService()
        svc.create_role("findable")
        role = svc.get_role("findable")
        assert role is not None
        assert role.name == "findable"

    def test_get_role_not_found(self, test_repository):
        svc = PermissionService()
        assert svc.get_role("ghost_role") is None

    def test_assign_permission_to_role(self, test_repository):
        svc = PermissionService()
        svc.create_role("assign_role")
        svc.create_permission("thing", "do")
        result = svc.assign_permission_to_role("assign_role", "thing", "do")
        assert result is True
        role = svc.get_role("assign_role")
        assert role.has_permission("thing", "do")

    def test_assign_permission_to_nonexistent_role(self, test_repository):
        svc = PermissionService()
        result = svc.assign_permission_to_role("ghost", "res", "act")
        assert result is False

    def test_assign_permission_already_assigned(self, test_repository):
        svc = PermissionService()
        svc.create_role("assign2_role")
        svc.assign_permission_to_role("assign2_role", "res", "act")
        result = svc.assign_permission_to_role("assign2_role", "res", "act")
        assert result is False  # Already exists

    def test_revoke_permission_from_role(self, test_repository):
        svc = PermissionService()
        svc.create_role("revoke_role")
        svc.assign_permission_to_role("revoke_role", "thing", "remove")
        result = svc.revoke_permission_from_role("revoke_role", "thing", "remove")
        assert result is True
        role = svc.get_role("revoke_role")
        assert not role.has_permission("thing", "remove")

    def test_revoke_permission_from_nonexistent_role(self, test_repository):
        svc = PermissionService()
        result = svc.revoke_permission_from_role("ghost", "res", "act")
        assert result is False

    def test_revoke_unassigned_permission(self, test_repository):
        svc = PermissionService()
        svc.create_role("partial_role")
        result = svc.revoke_permission_from_role("partial_role", "not", "assigned")
        assert result is False

    def test_get_role_permissions(self, test_repository):
        svc = PermissionService()
        svc.create_role("perm_role", permissions=[("x", "read"), ("x", "write")])
        perms = svc.get_role_permissions("perm_role")
        assert len(perms) == 2
        keys = {p.key for p in perms}
        assert "x:read" in keys
        assert "x:write" in keys

    def test_get_role_permissions_nonexistent_role(self, test_repository):
        svc = PermissionService()
        result = svc.get_role_permissions("nonexistent")
        assert result == []

    def test_user_has_permission_true(self, test_repository):
        svc = PermissionService()
        svc.create_role("checker_role", permissions=[("doc", "read")])
        user = _make_user(roles=["checker_role"])
        assert svc.user_has_permission(user, "doc", "read") is True

    def test_user_has_permission_false(self, test_repository):
        svc = PermissionService()
        svc.create_role("limited_role", permissions=[("doc", "read")])
        user = _make_user(roles=["limited_role"])
        assert svc.user_has_permission(user, "doc", "delete") is False

    def test_user_has_permission_no_roles(self, test_repository):
        svc = PermissionService()
        svc.create_permission("doc", "view")
        user = _make_user(roles=[])
        assert svc.user_has_permission(user, "doc", "view") is False

    def test_user_has_permission_nonexistent_permission(self, test_repository):
        svc = PermissionService()
        svc.create_role("any_role")
        user = _make_user(roles=["any_role"])
        assert svc.user_has_permission(user, "ghost", "action") is False

    def test_user_has_permission_nonexistent_role(self, test_repository):
        svc = PermissionService()
        svc.create_permission("doc", "read")
        user = _make_user(roles=["ghost_role"])
        assert svc.user_has_permission(user, "doc", "read") is False

    def test_user_has_permission_multiple_roles(self, test_repository):
        svc = PermissionService()
        svc.create_role("role_a", permissions=[("res", "read")])
        svc.create_role("role_b", permissions=[("res", "write")])
        user = _make_user(roles=["role_a", "role_b"])
        assert svc.user_has_permission(user, "res", "read") is True
        assert svc.user_has_permission(user, "res", "write") is True

    def test_superuser_always_has_permission(self, test_repository):
        svc = PermissionService()
        # No roles, no permissions, but is_superuser=True
        user = _make_user(roles=[], is_superuser=True)
        assert svc.user_has_permission(user, "anything", "everything") is True

    def test_get_user_permissions_empty(self, test_repository):
        svc = PermissionService()
        user = _make_user(roles=[])
        assert svc.get_user_permissions(user) == []

    def test_get_user_permissions_with_roles(self, test_repository):
        svc = PermissionService()
        svc.create_role("perm_user_role", permissions=[("u", "read"), ("u", "write")])
        user = _make_user(roles=["perm_user_role"])
        perms = svc.get_user_permissions(user)
        assert len(perms) == 2
        keys = {p.key for p in perms}
        assert "u:read" in keys

    def test_get_user_permissions_deduplicates(self, test_repository):
        svc = PermissionService()
        svc.create_permission("shared", "view")
        svc.create_role("dedup_a", permissions=[("shared", "view")])
        svc.create_role("dedup_b", permissions=[("shared", "view")])
        user = _make_user(roles=["dedup_a", "dedup_b"])
        perms = svc.get_user_permissions(user)
        # "shared:view" should appear only once
        keys = [p.key for p in perms]
        assert keys.count("shared:view") == 1

    def test_get_user_permissions_superuser_returns_all(self, test_repository):
        svc = PermissionService()
        svc.create_permission("a", "read")
        svc.create_permission("b", "write")
        user = _make_user(is_superuser=True)
        perms = svc.get_user_permissions(user)
        keys = {p.key for p in perms}
        assert "a:read" in keys
        assert "b:write" in keys

    def test_get_user_permissions_skips_unknown_role(self, test_repository):
        svc = PermissionService()
        svc.create_role("known_role", permissions=[("k", "act")])
        user = _make_user(roles=["known_role", "unknown_role"])
        perms = svc.get_user_permissions(user)
        assert len(perms) == 1


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def _make_request():
    """Create a lightweight mock request."""
    req = MagicMock()
    req.headers = {}
    req.cookies = {}
    return req


class TestRequirePermission:
    @pytest.mark.asyncio
    async def test_grants_permission(self, test_repository):
        svc = PermissionService()
        svc.create_role("dec_role", permissions=[("art", "create")])
        user = _make_user(roles=["dec_role"])

        @require_permission("art", "create", service=svc)
        async def handler(request, current_user=None):
            return "ok"

        result = await handler(_make_request(), current_user=user)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_denies_missing_permission(self, test_repository):
        svc = PermissionService()
        svc.create_role("dec_viewer", permissions=[("art", "view")])
        user = _make_user(roles=["dec_viewer"])

        @require_permission("art", "delete", service=svc)
        async def handler(request, current_user=None):
            return "ok"

        with pytest.raises(PermissionError) as exc_info:
            await handler(_make_request(), current_user=user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_no_current_user_raises_401(self, test_repository):
        svc = PermissionService()

        @require_permission("art", "view", service=svc)
        async def handler(request, current_user=None):
            return "ok"

        with pytest.raises(PermissionError) as exc_info:
            await handler(_make_request())
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_superuser_bypass(self, test_repository):
        svc = PermissionService()
        user = _make_user(is_superuser=True)

        @require_permission("art", "nuke", service=svc)
        async def handler(request, current_user=None):
            return "ok"

        result = await handler(_make_request(), current_user=user)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_default_service_created_when_none(self, test_repository):
        """require_permission works without explicit service argument."""
        svc = PermissionService()
        svc.create_role("default_role", permissions=[("res", "act")])
        user = _make_user(roles=["default_role"])

        @require_permission("res", "act")
        async def handler(request, current_user=None):
            return "ok"

        result = await handler(_make_request(), current_user=user)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_error_message_contains_resource_action(self, test_repository):
        svc = PermissionService()
        user = _make_user(roles=[])

        @require_permission("myres", "myact", service=svc)
        async def handler(request, current_user=None):
            return "ok"

        with pytest.raises(PermissionError) as exc_info:
            await handler(_make_request(), current_user=user)
        assert "myres:myact" in exc_info.value.message


class TestRequireAnyPermission:
    @pytest.mark.asyncio
    async def test_passes_with_first_permission(self, test_repository):
        svc = PermissionService()
        svc.create_role("any_role1", permissions=[("p", "a")])
        user = _make_user(roles=["any_role1"])

        @require_any_permission(("p", "a"), ("p", "b"), service=svc)
        async def handler(request, current_user=None):
            return "ok"

        result = await handler(_make_request(), current_user=user)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_passes_with_second_permission(self, test_repository):
        svc = PermissionService()
        svc.create_role("any_role2", permissions=[("p", "b")])
        user = _make_user(roles=["any_role2"])

        @require_any_permission(("p", "a"), ("p", "b"), service=svc)
        async def handler(request, current_user=None):
            return "ok"

        result = await handler(_make_request(), current_user=user)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_fails_with_none_matching(self, test_repository):
        svc = PermissionService()
        svc.create_role("any_role3", permissions=[("p", "c")])
        user = _make_user(roles=["any_role3"])

        @require_any_permission(("p", "a"), ("p", "b"), service=svc)
        async def handler(request, current_user=None):
            return "ok"

        with pytest.raises(PermissionError) as exc_info:
            await handler(_make_request(), current_user=user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_no_current_user_raises_401(self, test_repository):
        svc = PermissionService()

        @require_any_permission(("p", "a"), service=svc)
        async def handler(request, current_user=None):
            return "ok"

        with pytest.raises(PermissionError) as exc_info:
            await handler(_make_request())
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_superuser_bypass(self, test_repository):
        svc = PermissionService()
        user = _make_user(is_superuser=True)

        @require_any_permission(("x", "y"), ("z", "w"), service=svc)
        async def handler(request, current_user=None):
            return "superuser"

        result = await handler(_make_request(), current_user=user)
        assert result == "superuser"

    @pytest.mark.asyncio
    async def test_error_lists_all_options(self, test_repository):
        svc = PermissionService()
        user = _make_user(roles=[])

        @require_any_permission(("r1", "a1"), ("r2", "a2"), service=svc)
        async def handler(request, current_user=None):
            return "ok"

        with pytest.raises(PermissionError) as exc_info:
            await handler(_make_request(), current_user=user)
        assert "r1:a1" in exc_info.value.message
        assert "r2:a2" in exc_info.value.message


class TestRequireAllPermissions:
    @pytest.mark.asyncio
    async def test_passes_with_all_permissions(self, test_repository):
        svc = PermissionService()
        svc.create_role("all_role", permissions=[("q", "x"), ("q", "y")])
        user = _make_user(roles=["all_role"])

        @require_all_permissions(("q", "x"), ("q", "y"), service=svc)
        async def handler(request, current_user=None):
            return "ok"

        result = await handler(_make_request(), current_user=user)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_fails_if_one_missing(self, test_repository):
        svc = PermissionService()
        svc.create_role("partial_all_role", permissions=[("q", "x")])
        user = _make_user(roles=["partial_all_role"])

        @require_all_permissions(("q", "x"), ("q", "z"), service=svc)
        async def handler(request, current_user=None):
            return "ok"

        with pytest.raises(PermissionError) as exc_info:
            await handler(_make_request(), current_user=user)
        assert exc_info.value.status_code == 403
        assert "q:z" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_fails_if_all_missing(self, test_repository):
        svc = PermissionService()
        svc.create_role("empty_all_role")
        user = _make_user(roles=["empty_all_role"])

        @require_all_permissions(("q", "x"), ("q", "y"), service=svc)
        async def handler(request, current_user=None):
            return "ok"

        with pytest.raises(PermissionError) as exc_info:
            await handler(_make_request(), current_user=user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_no_current_user_raises_401(self, test_repository):
        svc = PermissionService()

        @require_all_permissions(("q", "x"), service=svc)
        async def handler(request, current_user=None):
            return "ok"

        with pytest.raises(PermissionError) as exc_info:
            await handler(_make_request())
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_superuser_bypass(self, test_repository):
        svc = PermissionService()
        user = _make_user(is_superuser=True)

        @require_all_permissions(("a", "b"), ("c", "d"), ("e", "f"), service=svc)
        async def handler(request, current_user=None):
            return "superuser_ok"

        result = await handler(_make_request(), current_user=user)
        assert result == "superuser_ok"

    @pytest.mark.asyncio
    async def test_passes_permissions_across_multiple_roles(self, test_repository):
        svc = PermissionService()
        svc.create_role("role_x", permissions=[("m", "read")])
        svc.create_role("role_y", permissions=[("m", "write")])
        user = _make_user(roles=["role_x", "role_y"])

        @require_all_permissions(("m", "read"), ("m", "write"), service=svc)
        async def handler(request, current_user=None):
            return "ok"

        result = await handler(_make_request(), current_user=user)
        assert result == "ok"


# ---------------------------------------------------------------------------
# PermissionError exception
# ---------------------------------------------------------------------------


class TestPermissionError:
    def test_default_values(self):
        err = PermissionError()
        assert err.status_code == 403
        assert "denied" in err.message.lower()

    def test_custom_message_and_status(self):
        err = PermissionError("Not allowed", 403)
        assert err.message == "Not allowed"
        assert err.status_code == 403

    def test_401_status(self):
        err = PermissionError("Login required", 401)
        assert err.status_code == 401

    def test_is_exception(self):
        err = PermissionError("oops")
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# Integration: auth.User compatible objects
# ---------------------------------------------------------------------------


class TestAuthUserCompatibility:
    """Verify PermissionService works with real auth.User-compatible objects."""

    def test_with_auth_user_role_list(self, test_repository):
        """Simulate auth.User's role_list interface."""
        from nitro.auth import User

        svc = PermissionService()
        svc.create_role("compat_editor", permissions=[("blog", "write")])

        user = User(email="author@example.com", roles="compat_editor")
        # Don't save — we're testing the interface, not persistence
        assert svc.user_has_permission(user, "blog", "write") is True
        assert svc.user_has_permission(user, "blog", "delete") is False

    def test_with_empty_roles_string(self, test_repository):
        """auth.User defaults to empty roles string."""
        from nitro.auth import User

        svc = PermissionService()
        svc.create_permission("blog", "post")
        user = User(email="nobody@example.com")
        assert svc.user_has_permission(user, "blog", "post") is False

    def test_superuser_flag_on_auth_user(self, test_repository):
        """auth.User.is_superuser bypasses all checks."""
        from nitro.auth import User

        svc = PermissionService()
        user = User(email="root@example.com", is_superuser=True)
        assert svc.user_has_permission(user, "everything", "allowed") is True
