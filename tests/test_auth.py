"""
Tests for nitro.auth — framework-agnostic authentication.

Covers: AuthService (password hashing, tokens), User entity, SessionStore, decorators.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from nitro.auth import (
    AuthError,
    AuthService,
    Session,
    SessionStore,
    TokenPayload,
    User,
    require_auth,
    require_role,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def auth():
    """AuthService with short TTLs for testing."""
    return AuthService(secret="test-secret-key", access_ttl_minutes=5, refresh_ttl_minutes=60)


@pytest.fixture
def session_store():
    """SessionStore with short TTL."""
    return SessionStore(ttl_seconds=300)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


class TestPasswordHashing:
    def test_hash_returns_pbkdf2_format(self, auth):
        hashed = auth.hash_password("mypassword")
        assert hashed.startswith("pbkdf2:sha256:")
        parts = hashed.split(":")
        assert len(parts) == 4

    def test_verify_correct_password(self, auth):
        hashed = auth.hash_password("secret123")
        assert auth.verify_password("secret123", hashed) is True

    def test_verify_wrong_password(self, auth):
        hashed = auth.hash_password("secret123")
        assert auth.verify_password("wrong", hashed) is False

    def test_verify_malformed_hash(self, auth):
        assert auth.verify_password("anything", "not-a-valid-hash") is False
        assert auth.verify_password("anything", "") is False

    def test_different_salts_per_hash(self, auth):
        h1 = auth.hash_password("same")
        h2 = auth.hash_password("same")
        assert h1 != h2  # different salts
        assert auth.verify_password("same", h1) is True
        assert auth.verify_password("same", h2) is True


# ---------------------------------------------------------------------------
# Token creation & decoding
# ---------------------------------------------------------------------------


class TestTokens:
    def test_create_access_token(self, auth):
        token = auth.create_access_token("user1", roles=["admin"])
        assert isinstance(token, str)
        assert "." in token  # data.signature format

    def test_create_refresh_token(self, auth):
        token = auth.create_refresh_token("user1")
        assert isinstance(token, str)

    def test_decode_valid_access_token(self, auth):
        token = auth.create_access_token("user1", roles=["editor", "admin"])
        payload = auth.decode_token(token)
        assert payload is not None
        assert isinstance(payload, TokenPayload)
        assert payload.sub == "user1"
        assert payload.type == "access"
        assert "editor" in payload.roles
        assert "admin" in payload.roles

    def test_decode_valid_refresh_token(self, auth):
        token = auth.create_refresh_token("user2")
        payload = auth.decode_token(token)
        assert payload is not None
        assert payload.sub == "user2"
        assert payload.type == "refresh"
        assert payload.roles == []

    def test_decode_tampered_token_returns_none(self, auth):
        token = auth.create_access_token("user1")
        # Tamper with the signature
        parts = token.rsplit(".", 1)
        tampered = parts[0] + ".deadbeef"
        assert auth.decode_token(tampered) is None

    def test_decode_garbage_returns_none(self, auth):
        assert auth.decode_token("not.a.token") is None
        assert auth.decode_token("") is None
        assert auth.decode_token("just-text") is None

    def test_decode_expired_token_returns_none(self):
        # Create service with 0-minute TTL (already expired)
        auth = AuthService(secret="key", access_ttl_minutes=0)
        token = auth.create_access_token("user1")
        # Token is created with exp = now + 0 minutes = now, which is ≤ now
        payload = auth.decode_token(token)
        assert payload is None

    def test_different_secret_cannot_decode(self, auth):
        token = auth.create_access_token("user1")
        other = AuthService(secret="different-secret")
        assert other.decode_token(token) is None


# ---------------------------------------------------------------------------
# User entity
# ---------------------------------------------------------------------------


class TestUserEntity:
    def test_role_list_empty(self):
        user = User(id="u1", email="test@example.com")
        assert user.role_list == []

    def test_role_list_single(self):
        user = User(id="u2", email="test@example.com", roles="admin")
        assert user.role_list == ["admin"]

    def test_role_list_multiple(self):
        user = User(id="u3", email="test@example.com", roles="admin,editor,viewer")
        assert user.role_list == ["admin", "editor", "viewer"]

    def test_has_role_true(self):
        user = User(id="u4", email="test@example.com", roles="admin,editor")
        assert user.has_role("admin") is True
        assert user.has_role("editor") is True

    def test_has_role_false(self):
        user = User(id="u5", email="test@example.com", roles="viewer")
        assert user.has_role("admin") is False

    def test_add_role(self):
        user = User(id="u6", email="test@example.com")
        user.add_role("admin")
        assert user.has_role("admin")
        assert user.roles == "admin"

    def test_add_role_no_duplicate(self):
        user = User(id="u7", email="test@example.com", roles="admin")
        user.add_role("admin")
        assert user.roles == "admin"

    def test_remove_role(self):
        user = User(id="u8", email="test@example.com", roles="admin,editor")
        user.remove_role("admin")
        assert not user.has_role("admin")
        assert user.has_role("editor")

    def test_remove_nonexistent_role(self):
        user = User(id="u9", email="test@example.com", roles="admin")
        user.remove_role("viewer")
        assert user.roles == "admin"


# ---------------------------------------------------------------------------
# User registration & authentication (requires DB)
# ---------------------------------------------------------------------------


class TestAuthServiceIntegration:
    def test_register_creates_user(self, test_repository, auth):
        test_repository.init_db()
        user = auth.register("alice@example.com", "password123", roles=["editor"])
        assert user.email == "alice@example.com"
        assert user.has_role("editor")
        assert user.hashed_password != "password123"
        # Verify persisted
        loaded = User.get(user.id)
        assert loaded is not None
        assert loaded.email == "alice@example.com"

    def test_register_duplicate_email_raises(self, test_repository, auth):
        test_repository.init_db()
        auth.register("bob@example.com", "pass1")
        with pytest.raises(ValueError, match="already exists"):
            auth.register("bob@example.com", "pass2")

    def test_authenticate_success(self, test_repository, auth):
        test_repository.init_db()
        auth.register("charlie@example.com", "secret", roles=["admin"])
        result = auth.authenticate("charlie@example.com", "secret")
        assert result is not None
        user, access_token, refresh_token = result
        assert user.email == "charlie@example.com"
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        # Verify tokens are valid
        payload = auth.decode_token(access_token)
        assert payload.sub == user.id

    def test_authenticate_wrong_password(self, test_repository, auth):
        test_repository.init_db()
        auth.register("dave@example.com", "correct")
        result = auth.authenticate("dave@example.com", "wrong")
        assert result is None

    def test_authenticate_unknown_email(self, test_repository, auth):
        test_repository.init_db()
        result = auth.authenticate("nobody@example.com", "anything")
        assert result is None

    def test_authenticate_inactive_user(self, test_repository, auth):
        test_repository.init_db()
        user = auth.register("eve@example.com", "pass")
        user.is_active = False
        user.save()
        result = auth.authenticate("eve@example.com", "pass")
        assert result is None

    def test_authenticate_updates_last_login(self, test_repository, auth):
        test_repository.init_db()
        auth.register("frank@example.com", "pass")
        before = datetime.now(timezone.utc)
        auth.authenticate("frank@example.com", "pass")
        user = User.find_by(email="frank@example.com")
        if isinstance(user, list):
            user = user[0]
        assert user.last_login is not None


# ---------------------------------------------------------------------------
# SessionStore
# ---------------------------------------------------------------------------


class TestSessionStore:
    def test_create_session(self, session_store):
        session = session_store.create("user1", data={"role": "admin"})
        assert isinstance(session, Session)
        assert session.user_id == "user1"
        assert session.get("role") == "admin"

    def test_get_session(self, session_store):
        created = session_store.create("user2")
        retrieved = session_store.get(created.id)
        assert retrieved is not None
        assert retrieved.user_id == "user2"

    def test_get_nonexistent_returns_none(self, session_store):
        assert session_store.get("nonexistent") is None

    def test_destroy_session(self, session_store):
        session = session_store.create("user3")
        session_store.destroy(session.id)
        assert session_store.get(session.id) is None

    def test_destroy_nonexistent_is_noop(self, session_store):
        session_store.destroy("nonexistent")  # should not raise

    def test_session_data_operations(self):
        session = Session("s1", "user1")
        session.set("key", "value")
        assert session.get("key") == "value"
        session.delete("key")
        assert session.get("key") is None
        assert session.get("missing", "default") == "default"

    def test_session_repr(self):
        session = Session("abc123", "user42")
        assert "abc123" in repr(session)
        assert "user42" in repr(session)


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def _make_request(headers=None, cookies=None):
    """Create a mock request object."""
    req = MagicMock()
    req.headers = headers or {}
    req.cookies = cookies or {}
    return req


class TestRequireAuth:
    @pytest.mark.asyncio
    async def test_bearer_token_extraction(self, auth):
        token = auth.create_access_token("user1", roles=["admin"])

        @require_auth(auth)
        async def handler(request, current_user=None):
            return current_user

        req = _make_request(headers={"authorization": f"Bearer {token}"})
        result = await handler(req)
        assert isinstance(result, TokenPayload)
        assert result.sub == "user1"

    @pytest.mark.asyncio
    async def test_cookie_token_extraction(self, auth):
        token = auth.create_access_token("user2")

        @require_auth(auth)
        async def handler(request, current_user=None):
            return current_user

        req = _make_request(cookies={"auth_token": token})
        result = await handler(req)
        assert result.sub == "user2"

    @pytest.mark.asyncio
    async def test_signals_token_extraction(self, auth):
        token = auth.create_access_token("user3")

        @require_auth(auth)
        async def handler(request, current_user=None, **kwargs):
            return current_user

        req = _make_request()
        result = await handler(req, signals={"auth_token": token})
        assert result.sub == "user3"

    @pytest.mark.asyncio
    async def test_no_token_raises_auth_error(self, auth):
        @require_auth(auth)
        async def handler(request, current_user=None):
            return current_user

        req = _make_request()
        with pytest.raises(AuthError) as exc_info:
            await handler(req)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_raises_auth_error(self, auth):
        @require_auth(auth)
        async def handler(request, current_user=None):
            return current_user

        req = _make_request(headers={"authorization": "Bearer invalid.token"})
        with pytest.raises(AuthError) as exc_info:
            await handler(req)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_custom_token_extractor(self, auth):
        token = auth.create_access_token("user4")

        def custom_extractor(request):
            return request.headers.get("x-custom-auth")

        @require_auth(auth, token_extractor=custom_extractor)
        async def handler(request, current_user=None):
            return current_user

        req = _make_request(headers={"x-custom-auth": token})
        result = await handler(req)
        assert result.sub == "user4"


class TestRequireRole:
    @pytest.mark.asyncio
    async def test_matching_role_passes(self, auth):
        token = auth.create_access_token("user1", roles=["admin", "editor"])

        @require_auth(auth)
        @require_role("admin")
        async def handler(request, current_user=None):
            return "ok"

        req = _make_request(headers={"authorization": f"Bearer {token}"})
        result = await handler(req)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_any_matching_role_passes(self, auth):
        token = auth.create_access_token("user1", roles=["viewer"])

        @require_auth(auth)
        @require_role("admin", "viewer")
        async def handler(request, current_user=None):
            return "ok"

        req = _make_request(headers={"authorization": f"Bearer {token}"})
        result = await handler(req)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_no_matching_role_raises_403(self, auth):
        token = auth.create_access_token("user1", roles=["viewer"])

        @require_auth(auth)
        @require_role("admin")
        async def handler(request, current_user=None):
            return "ok"

        req = _make_request(headers={"authorization": f"Bearer {token}"})
        with pytest.raises(AuthError) as exc_info:
            await handler(req)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_no_current_user_raises_401(self):
        @require_role("admin")
        async def handler(request, current_user=None):
            return "ok"

        req = _make_request()
        with pytest.raises(AuthError) as exc_info:
            await handler(req)
        assert exc_info.value.status_code == 401
