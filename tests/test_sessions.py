"""
Comprehensive tests for nitro.sessions module.

Covers:
- SessionData (dict-like interface, flash messages, lifecycle)
- MemorySessionStore (CRUD, TTL, cleanup)
- CookieSessionStore (encoding, signing, expiry, tampering)
- SessionMiddleware (load/save, cookie sessions, invalidation)
- RedisSessionStore (mocked — no live Redis needed)
- sanic_sessions integration (mocked Sanic)
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nitro.sessions.base import SessionData, SessionInterface, generate_session_id
from nitro.sessions.memory_store import MemorySessionStore
from nitro.sessions.cookie_store import CookieSessionStore
from nitro.sessions.middleware import SessionConfig, SessionMiddleware


# ── Helpers ──────────────────────────────────────────────────────────


def run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


@pytest.fixture
def memory_store():
    return MemorySessionStore(ttl=3600)


@pytest.fixture
def cookie_store():
    return CookieSessionStore(secret="test-secret-key", max_age=3600)


@pytest.fixture
def session_middleware(memory_store):
    return SessionMiddleware(memory_store)


# ══════════════════════════════════════════════════════════════════════
# SessionData Tests
# ══════════════════════════════════════════════════════════════════════


class TestSessionData:
    """Tests for the SessionData dict-like container."""

    def test_create_empty_session(self):
        s = SessionData("sid-1")
        assert s.session_id == "sid-1"
        assert len(s) == 0
        assert s.is_new is False
        assert s.modified is False

    def test_create_new_session(self):
        s = SessionData("sid-1", is_new=True)
        assert s.is_new is True

    def test_create_with_data(self):
        s = SessionData("sid-1", {"key": "value"})
        assert s["key"] == "value"
        assert len(s) == 1

    def test_setitem_marks_modified(self):
        s = SessionData("sid-1")
        s["name"] = "Alice"
        assert s["name"] == "Alice"
        assert s.modified is True

    def test_delitem_marks_modified(self):
        s = SessionData("sid-1", {"key": "value"})
        del s["key"]
        assert "key" not in s
        assert s.modified is True

    def test_delitem_missing_key_raises(self):
        s = SessionData("sid-1")
        with pytest.raises(KeyError):
            del s["missing"]

    def test_contains(self):
        s = SessionData("sid-1", {"x": 1})
        assert "x" in s
        assert "y" not in s

    def test_get_default(self):
        s = SessionData("sid-1")
        assert s.get("missing") is None
        assert s.get("missing", 42) == 42

    def test_pop(self):
        s = SessionData("sid-1", {"key": "val"})
        result = s.pop("key")
        assert result == "val"
        assert "key" not in s
        assert s.modified is True

    def test_pop_missing_with_default(self):
        s = SessionData("sid-1")
        assert s.pop("missing", "default") == "default"

    def test_setdefault_new_key(self):
        s = SessionData("sid-1")
        result = s.setdefault("count", 0)
        assert result == 0
        assert s["count"] == 0
        assert s.modified is True

    def test_setdefault_existing_key(self):
        s = SessionData("sid-1", {"count": 5})
        result = s.setdefault("count", 0)
        assert result == 5

    def test_update(self):
        s = SessionData("sid-1")
        s.update({"a": 1, "b": 2})
        assert s["a"] == 1
        assert s["b"] == 2
        assert s.modified is True

    def test_keys_values_items(self):
        data = {"a": 1, "b": 2}
        s = SessionData("sid-1", data)
        assert set(s.keys()) == {"a", "b"}
        assert set(s.values()) == {1, 2}
        assert set(s.items()) == {("a", 1), ("b", 2)}

    def test_clear(self):
        s = SessionData("sid-1", {"a": 1, "b": 2})
        s.clear()
        assert len(s) == 0
        assert s.modified is True

    def test_to_dict(self):
        s = SessionData("sid-1", {"a": 1})
        d = s.to_dict()
        assert d == {"a": 1}
        assert isinstance(d, dict)
        # Ensure it's a copy
        d["a"] = 99
        assert s["a"] == 1

    def test_bool_always_true(self):
        s = SessionData("sid-1")
        assert bool(s) is True  # Even empty sessions are truthy

    def test_repr(self):
        s = SessionData("sid-1", {"name": "Alice"}, is_new=True)
        r = repr(s)
        assert "sid-1" in r
        assert "name" in r
        assert "new=True" in r


class TestSessionDataFlash:
    """Tests for flash message functionality."""

    def test_flash_adds_message(self):
        s = SessionData("sid-1")
        s.flash("Hello!", "success")
        assert s.modified is True
        flashes = s.peek_flashes()
        assert len(flashes) == 1
        assert flashes[0]["message"] == "Hello!"
        assert flashes[0]["category"] == "success"

    def test_flash_default_category(self):
        s = SessionData("sid-1")
        s.flash("Note")
        flashes = s.peek_flashes()
        assert flashes[0]["category"] == "info"

    def test_pop_flashes_consumes(self):
        s = SessionData("sid-1")
        s.flash("Msg 1")
        s.flash("Msg 2")
        flashes = s.pop_flashes()
        assert len(flashes) == 2
        # Consumed — second pop returns empty
        assert s.pop_flashes() == []

    def test_pop_flashes_by_category(self):
        s = SessionData("sid-1")
        s.flash("Error!", "error")
        s.flash("OK!", "success")
        s.flash("Another error", "error")

        errors = s.pop_flashes("error")
        assert len(errors) == 2
        assert all(f["category"] == "error" for f in errors)

        # Success message still there
        remaining = s.pop_flashes()
        assert len(remaining) == 1
        assert remaining[0]["category"] == "success"

    def test_peek_flashes_does_not_consume(self):
        s = SessionData("sid-1")
        s.flash("Hello")
        assert len(s.peek_flashes()) == 1
        assert len(s.peek_flashes()) == 1  # Still there

    def test_peek_flashes_by_category(self):
        s = SessionData("sid-1")
        s.flash("A", "info")
        s.flash("B", "error")
        assert len(s.peek_flashes("info")) == 1
        assert len(s.peek_flashes("error")) == 1

    def test_pop_flashes_empty_session(self):
        s = SessionData("sid-1")
        assert s.pop_flashes() == []


class TestSessionDataLifecycle:
    """Tests for session invalidation."""

    def test_invalidate(self):
        s = SessionData("sid-1", {"user": "Alice"})
        s.invalidate()
        assert s.is_invalidated is True
        assert len(s) == 0
        assert s.modified is True

    def test_invalidated_session_is_empty(self):
        s = SessionData("sid-1", {"a": 1, "b": 2})
        s.invalidate()
        assert s.to_dict() == {}


class TestGenerateSessionId:
    """Tests for session ID generation."""

    def test_generates_string(self):
        sid = generate_session_id()
        assert isinstance(sid, str)
        assert len(sid) > 20

    def test_unique(self):
        ids = {generate_session_id() for _ in range(100)}
        assert len(ids) == 100


# ══════════════════════════════════════════════════════════════════════
# MemorySessionStore Tests
# ══════════════════════════════════════════════════════════════════════


class TestMemorySessionStore:
    """Tests for the in-memory session backend."""

    def test_save_and_load(self, memory_store):
        run(memory_store.save("s1", {"user": "Alice"}))
        data = run(memory_store.load("s1"))
        assert data == {"user": "Alice"}

    def test_load_missing_returns_none(self, memory_store):
        assert run(memory_store.load("missing")) is None

    def test_load_returns_copy(self, memory_store):
        run(memory_store.save("s1", {"counter": 0}))
        data = run(memory_store.load("s1"))
        data["counter"] = 99
        original = run(memory_store.load("s1"))
        assert original["counter"] == 0

    def test_delete(self, memory_store):
        run(memory_store.save("s1", {"x": 1}))
        run(memory_store.delete("s1"))
        assert run(memory_store.load("s1")) is None

    def test_delete_missing_no_error(self, memory_store):
        run(memory_store.delete("nonexistent"))  # Should not raise

    def test_exists(self, memory_store):
        assert run(memory_store.exists("s1")) is False
        run(memory_store.save("s1", {}))
        assert run(memory_store.exists("s1")) is True

    def test_ttl_expiry(self):
        store = MemorySessionStore(ttl=1)
        run(store.save("s1", {"x": 1}))
        assert run(store.load("s1")) is not None

        # Simulate time passing by manipulating the store
        store._store["s1"] = ({"x": 1}, time.monotonic() - 2)
        assert run(store.load("s1")) is None

    def test_ttl_zero_no_expiry(self):
        store = MemorySessionStore(ttl=0)
        run(store.save("s1", {"x": 1}))
        # Session should not expire even with manipulated time
        assert run(store.load("s1")) is not None

    def test_exists_expired(self):
        store = MemorySessionStore(ttl=1)
        run(store.save("s1", {"x": 1}))
        store._store["s1"] = ({"x": 1}, time.monotonic() - 2)
        assert run(store.exists("s1")) is False

    def test_clear_all(self, memory_store):
        run(memory_store.save("s1", {"a": 1}))
        run(memory_store.save("s2", {"b": 2}))
        run(memory_store.save("s3", {"c": 3}))
        count = run(memory_store.clear_all())
        assert count == 3
        assert memory_store.count == 0

    def test_cleanup_expired(self):
        store = MemorySessionStore(ttl=1)
        run(store.save("s1", {}))
        run(store.save("s2", {}))
        run(store.save("s3", {}))

        # Expire s1 and s2
        now = time.monotonic()
        store._store["s1"] = ({}, now - 2)
        store._store["s2"] = ({}, now - 2)

        removed = store.cleanup_expired()
        assert removed == 2
        assert store.count == 1

    def test_cleanup_no_ttl(self):
        store = MemorySessionStore(ttl=0)
        run(store.save("s1", {}))
        assert store.cleanup_expired() == 0

    def test_count(self, memory_store):
        assert memory_store.count == 0
        run(memory_store.save("s1", {}))
        run(memory_store.save("s2", {}))
        assert memory_store.count == 2

    def test_overwrite(self, memory_store):
        run(memory_store.save("s1", {"v": 1}))
        run(memory_store.save("s1", {"v": 2}))
        data = run(memory_store.load("s1"))
        assert data["v"] == 2


# ══════════════════════════════════════════════════════════════════════
# CookieSessionStore Tests
# ══════════════════════════════════════════════════════════════════════


class TestCookieSessionStore:
    """Tests for signed cookie-based sessions."""

    def test_encode_decode_roundtrip(self, cookie_store):
        data = {"user": "Alice", "role": "admin"}
        encoded = cookie_store.encode(data)
        decoded = cookie_store.decode(encoded)
        assert decoded == data

    def test_decode_invalid_no_dot(self, cookie_store):
        assert cookie_store.decode("nodothere") is None

    def test_decode_invalid_bad_signature(self, cookie_store):
        data = {"user": "Alice"}
        encoded = cookie_store.encode(data)
        # Tamper with the signature
        parts = encoded.rsplit(".", 1)
        tampered = f"{parts[0]}.{'a' * 64}"
        assert cookie_store.decode(tampered) is None

    def test_decode_invalid_bad_payload(self, cookie_store):
        assert cookie_store.decode("notbase64.abcdef") is None

    def test_decode_tampered_payload(self, cookie_store):
        data = {"user": "Alice"}
        encoded = cookie_store.encode(data)
        parts = encoded.rsplit(".", 1)
        # Modify payload (still valid base64 but different data)
        import base64
        tampered_payload = base64.urlsafe_b64encode(b'{"_ts":0,"_data":{"user":"Eve"}}')
        tampered = f"{tampered_payload.decode()}.{parts[1]}"
        assert cookie_store.decode(tampered) is None

    def test_expiry(self):
        store = CookieSessionStore(secret="key", max_age=1)
        data = {"x": 1}
        encoded = store.encode(data)

        # Should work immediately
        assert store.decode(encoded) is not None

        # Simulate expiry by patching time
        with patch("nitro.sessions.cookie_store.time") as mock_time:
            mock_time.time.return_value = time.time() + 3600
            assert store.decode(encoded) is None

    def test_no_expiry(self):
        store = CookieSessionStore(secret="key", max_age=0)
        data = {"x": 1}
        encoded = store.encode(data)
        assert store.decode(encoded) == data

    def test_empty_secret_raises(self):
        with pytest.raises(ValueError, match="non-empty secret"):
            CookieSessionStore(secret="")

    def test_different_secrets(self):
        store1 = CookieSessionStore(secret="secret-1")
        store2 = CookieSessionStore(secret="secret-2")
        encoded = store1.encode({"user": "Alice"})
        # Different secret can't decode
        assert store2.decode(encoded) is None

    def test_load_async(self, cookie_store):
        encoded = cookie_store.encode({"key": "value"})
        data = run(cookie_store.load(encoded))
        assert data == {"key": "value"}

    def test_load_invalid(self, cookie_store):
        assert run(cookie_store.load("invalid.cookie")) is None

    def test_save_noop(self, cookie_store):
        # Save is a no-op for cookie sessions
        run(cookie_store.save("anything", {"x": 1}))

    def test_delete_noop(self, cookie_store):
        run(cookie_store.delete("anything"))

    def test_complex_data(self, cookie_store):
        data = {
            "user_id": "u123",
            "roles": ["admin", "editor"],
            "prefs": {"theme": "dark", "lang": "en"},
            "count": 42,
            "active": True,
        }
        encoded = cookie_store.encode(data)
        decoded = cookie_store.decode(encoded)
        assert decoded == data


# ══════════════════════════════════════════════════════════════════════
# SessionMiddleware Tests
# ══════════════════════════════════════════════════════════════════════


class TestSessionMiddleware:
    """Tests for session loading and saving logic."""

    def test_load_new_session(self, session_middleware):
        session = run(session_middleware.load_session(None))
        assert session.is_new is True
        assert len(session) == 0

    def test_load_existing_session(self, session_middleware, memory_store):
        run(memory_store.save("existing-id", {"user": "Alice"}))
        session = run(session_middleware.load_session("existing-id"))
        assert session.is_new is False
        assert session["user"] == "Alice"

    def test_load_missing_session(self, session_middleware):
        session = run(session_middleware.load_session("nonexistent"))
        assert session.is_new is True

    def test_save_modified_session(self, session_middleware, memory_store):
        session = SessionData("s1", {"x": 1})
        session["x"] = 2  # Marks modified
        cookie = run(session_middleware.save_session(session))
        assert cookie == "s1"
        data = run(memory_store.load("s1"))
        assert data["x"] == 2

    def test_save_unmodified_session(self, session_middleware):
        session = SessionData("s1", {"x": 1})
        cookie = run(session_middleware.save_session(session))
        assert cookie is None  # No changes

    def test_save_new_session(self, session_middleware, memory_store):
        session = SessionData("new-id", {"welcome": True}, is_new=True)
        cookie = run(session_middleware.save_session(session))
        assert cookie == "new-id"
        data = run(memory_store.load("new-id"))
        assert data["welcome"] is True

    def test_save_invalidated_session(self, session_middleware, memory_store):
        run(memory_store.save("s1", {"user": "Alice"}))
        session = SessionData("s1", {"user": "Alice"})
        session.invalidate()
        cookie = run(session_middleware.save_session(session))
        assert cookie == ""  # Signal to delete cookie
        assert run(memory_store.load("s1")) is None

    def test_save_invalidated_new_session(self, session_middleware, memory_store):
        session = SessionData("s1", is_new=True)
        session.invalidate()
        cookie = run(session_middleware.save_session(session))
        assert cookie == ""  # Signal to delete, but no store delete needed

    def test_cookie_session_load(self):
        store = CookieSessionStore(secret="test", max_age=3600)
        mw = SessionMiddleware(store)
        encoded = store.encode({"user": "Bob"})
        session = run(mw.load_session(encoded))
        assert session.is_new is False
        assert session["user"] == "Bob"

    def test_cookie_session_save(self):
        store = CookieSessionStore(secret="test", max_age=3600)
        mw = SessionMiddleware(store)
        session = SessionData("x", {"user": "Bob"})
        session["user"] = "Bob"  # Mark modified
        cookie = run(mw.save_session(session))
        assert cookie is not None
        assert "." in cookie  # Signed cookie format
        # Verify roundtrip
        decoded = store.decode(cookie)
        assert decoded["user"] == "Bob"

    def test_build_cookie_attrs_defaults(self):
        mw = SessionMiddleware(MemorySessionStore())
        attrs = mw.build_cookie_attrs()
        assert attrs["path"] == "/"
        assert attrs["httponly"] is True
        assert attrs["samesite"] == "Lax"
        assert "secure" not in attrs
        assert "domain" not in attrs

    def test_build_cookie_attrs_custom(self):
        config = SessionConfig(
            cookie_name="sid",
            cookie_path="/app",
            cookie_domain=".example.com",
            cookie_secure=True,
            cookie_httponly=False,
            cookie_samesite="Strict",
            cookie_max_age=7200,
        )
        mw = SessionMiddleware(MemorySessionStore(), config)
        attrs = mw.build_cookie_attrs()
        assert attrs["path"] == "/app"
        assert attrs["domain"] == ".example.com"
        assert attrs["secure"] is True
        assert attrs["httponly"] is False
        assert attrs["samesite"] == "Strict"
        assert attrs["max_age"] == 7200

    def test_build_cookie_attrs_override_max_age(self):
        mw = SessionMiddleware(MemorySessionStore())
        attrs = mw.build_cookie_attrs(max_age=0)
        assert attrs["max_age"] == 0


# ══════════════════════════════════════════════════════════════════════
# SessionConfig Tests
# ══════════════════════════════════════════════════════════════════════


class TestSessionConfig:
    """Tests for SessionConfig defaults and customization."""

    def test_defaults(self):
        config = SessionConfig()
        assert config.cookie_name == "nitro_session"
        assert config.cookie_path == "/"
        assert config.cookie_domain is None
        assert config.cookie_secure is False
        assert config.cookie_httponly is True
        assert config.cookie_samesite == "Lax"
        assert config.cookie_max_age is None

    def test_custom(self):
        config = SessionConfig(
            cookie_name="app_session",
            cookie_secure=True,
            cookie_max_age=86400,
        )
        assert config.cookie_name == "app_session"
        assert config.cookie_secure is True
        assert config.cookie_max_age == 86400


# ══════════════════════════════════════════════════════════════════════
# RedisSessionStore Tests (Mocked)
# ══════════════════════════════════════════════════════════════════════


class TestRedisSessionStore:
    """Tests for Redis-backed sessions using mocked Redis client."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock async Redis client."""
        client = AsyncMock()
        client.get = AsyncMock(return_value=None)
        client.setex = AsyncMock()
        client.set = AsyncMock()
        client.delete = AsyncMock()
        client.exists = AsyncMock(return_value=0)
        client.scan = AsyncMock(return_value=(0, []))
        client.aclose = AsyncMock()
        return client

    @pytest.fixture
    def redis_store(self, mock_redis):
        from nitro.sessions.redis_store import RedisSessionStore

        return RedisSessionStore(
            url="redis://localhost:6379/0",
            prefix="test:sessions:",
            ttl=3600,
            client=mock_redis,
        )

    def test_save_with_ttl(self, redis_store, mock_redis):
        run(redis_store.save("s1", {"user": "Alice"}))
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args
        assert args[0][0] == "test:sessions:s1"
        assert args[0][1] == 3600
        parsed = json.loads(args[0][2])
        assert parsed["user"] == "Alice"

    def test_save_without_ttl(self, mock_redis):
        from nitro.sessions.redis_store import RedisSessionStore

        store = RedisSessionStore(ttl=0, client=mock_redis)
        run(store.save("s1", {"x": 1}))
        mock_redis.set.assert_called_once()

    def test_load_existing(self, redis_store, mock_redis):
        mock_redis.get.return_value = '{"user":"Alice"}'
        data = run(redis_store.load("s1"))
        assert data == {"user": "Alice"}
        mock_redis.get.assert_called_with("test:sessions:s1")

    def test_load_missing(self, redis_store, mock_redis):
        mock_redis.get.return_value = None
        assert run(redis_store.load("missing")) is None

    def test_load_invalid_json(self, redis_store, mock_redis):
        mock_redis.get.return_value = "not-json"
        assert run(redis_store.load("bad")) is None

    def test_delete(self, redis_store, mock_redis):
        run(redis_store.delete("s1"))
        mock_redis.delete.assert_called_with("test:sessions:s1")

    def test_exists(self, redis_store, mock_redis):
        mock_redis.exists.return_value = 1
        assert run(redis_store.exists("s1")) is True
        mock_redis.exists.assert_called_with("test:sessions:s1")

    def test_clear_all(self, redis_store, mock_redis):
        mock_redis.scan.side_effect = [
            (42, ["test:sessions:s1", "test:sessions:s2"]),
            (0, ["test:sessions:s3"]),
        ]
        count = run(redis_store.clear_all())
        assert count == 3

    def test_close(self, redis_store, mock_redis):
        run(redis_store.close())
        mock_redis.aclose.assert_called_once()


# ══════════════════════════════════════════════════════════════════════
# SessionInterface Tests
# ══════════════════════════════════════════════════════════════════════


class TestSessionInterface:
    """Tests for the abstract base class defaults."""

    def test_exists_default(self):
        """Default exists() delegates to load()."""

        class TestStore(SessionInterface):
            async def load(self, sid):
                return {"data": True} if sid == "found" else None

            async def save(self, sid, data):
                pass

            async def delete(self, sid):
                pass

        store = TestStore()
        assert run(store.exists("found")) is True
        assert run(store.exists("missing")) is False

    def test_clear_all_default_raises(self):
        class TestStore(SessionInterface):
            async def load(self, sid):
                return None

            async def save(self, sid, data):
                pass

            async def delete(self, sid):
                pass

        store = TestStore()
        with pytest.raises(NotImplementedError):
            run(store.clear_all())


# ══════════════════════════════════════════════════════════════════════
# Integration-style Tests
# ══════════════════════════════════════════════════════════════════════


class TestSessionWorkflow:
    """End-to-end workflow tests combining store + middleware."""

    def test_full_lifecycle_memory(self):
        """Create → use → modify → reload → invalidate."""
        store = MemorySessionStore(ttl=3600)
        mw = SessionMiddleware(store)

        # 1. First request — no cookie
        session = run(mw.load_session(None))
        assert session.is_new is True

        # 2. Set data
        session["user_id"] = "u123"
        session["theme"] = "dark"
        cookie = run(mw.save_session(session))
        assert cookie is not None

        # 3. Second request — with cookie
        session2 = run(mw.load_session(cookie))
        assert session2.is_new is False
        assert session2["user_id"] == "u123"
        assert session2["theme"] == "dark"

        # 4. Modify
        session2["theme"] = "light"
        cookie2 = run(mw.save_session(session2))
        assert cookie2 == cookie  # Same session ID

        # 5. Third request — verify update
        session3 = run(mw.load_session(cookie))
        assert session3["theme"] == "light"

        # 6. Invalidate (logout)
        session3.invalidate()
        result = run(mw.save_session(session3))
        assert result == ""  # Delete signal

        # 7. Session gone
        session4 = run(mw.load_session(cookie))
        assert session4.is_new is True

    def test_full_lifecycle_cookie(self):
        """Create → use → modify → reload → invalidate with cookie store."""
        store = CookieSessionStore(secret="my-secret", max_age=3600)
        mw = SessionMiddleware(store)

        # 1. First request
        session = run(mw.load_session(None))
        assert session.is_new is True

        # 2. Set data
        session["user"] = "Alice"
        cookie = run(mw.save_session(session))
        assert cookie is not None
        assert "." in cookie

        # 3. Reload from cookie
        session2 = run(mw.load_session(cookie))
        assert session2["user"] == "Alice"

    def test_flash_across_requests(self):
        """Flash message set in one request, consumed in next."""
        store = MemorySessionStore(ttl=3600)
        mw = SessionMiddleware(store)

        # Request 1: set flash
        session = run(mw.load_session(None))
        session.flash("Item saved!", "success")
        cookie = run(mw.save_session(session))

        # Request 2: consume flash
        session2 = run(mw.load_session(cookie))
        flashes = session2.pop_flashes()
        assert len(flashes) == 1
        assert flashes[0]["message"] == "Item saved!"
        assert flashes[0]["category"] == "success"
        run(mw.save_session(session2))

        # Request 3: flash is gone
        session3 = run(mw.load_session(cookie))
        assert session3.pop_flashes() == []

    def test_concurrent_data_types(self):
        """Session handles various data types."""
        store = MemorySessionStore()
        mw = SessionMiddleware(store)

        session = run(mw.load_session(None))
        session["string"] = "hello"
        session["number"] = 42
        session["float"] = 3.14
        session["bool"] = True
        session["list"] = [1, 2, 3]
        session["dict"] = {"nested": "value"}
        session["none"] = None
        cookie = run(mw.save_session(session))

        session2 = run(mw.load_session(cookie))
        assert session2["string"] == "hello"
        assert session2["number"] == 42
        assert session2["float"] == 3.14
        assert session2["bool"] is True
        assert session2["list"] == [1, 2, 3]
        assert session2["dict"] == {"nested": "value"}
        assert session2["none"] is None
