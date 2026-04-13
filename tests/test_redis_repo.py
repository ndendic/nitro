"""
Tests for nitro.domain.repository.redis — Redis-backed entity repository.

Covers: save, get, find, delete, exists, all, count, flush, TTL,
        pub/sub notifications, singleton pattern, key format.
"""

import json
import sys
from unittest.mock import MagicMock, call, patch

import pytest
from pydantic import BaseModel

# Ensure a mock 'redis' module is available before importing the repository,
# since the real redis package may not be installed.
_mock_redis_module = MagicMock()
sys.modules.setdefault("redis", _mock_redis_module)

from nitro.domain.repository.redis import RedisRepository  # noqa: E402


# ---------------------------------------------------------------------------
# Test entity
# ---------------------------------------------------------------------------

class FakeEntity(BaseModel):
    id: str = ""
    name: str = ""
    value: int = 0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure the RedisRepository singleton is torn down between every test."""
    RedisRepository._instance = None
    yield
    RedisRepository._instance = None


@pytest.fixture
def mock_redis():
    """Patch redis module and return a MagicMock client."""
    mock_client = MagicMock()
    mock_redis_mod = MagicMock()
    mock_redis_mod.from_url.return_value = mock_client
    with patch.dict("nitro.domain.repository.redis.__dict__", {"redis": mock_redis_mod, "HAS_REDIS": True}):
        yield mock_client


@pytest.fixture
def repo(mock_redis):
    """Return a RedisRepository instance wired to the mock client."""
    return RedisRepository(url="redis://localhost:6379/0", prefix="test", default_ttl=None)


@pytest.fixture
def entity():
    """Return a simple FakeEntity for use in tests."""
    return FakeEntity(id="e1", name="Widget", value=7)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

class TestRedisRepositorySingleton:
    """RedisRepository follows the singleton pattern."""

    def test_singleton_returns_same_instance(self, mock_redis):
        r1 = RedisRepository(url="redis://localhost/0", prefix="test")
        r2 = RedisRepository(url="redis://localhost/0", prefix="test")
        assert r1 is r2

    def test_second_init_does_not_reconnect(self, mock_redis):
        """After the singleton exists, __init__ exits early — from_url called once."""
        RedisRepository(url="redis://localhost/0", prefix="test")
        RedisRepository(url="redis://localhost/0", prefix="test")
        import nitro.domain.repository.redis as redis_mod
        redis_mod.redis.from_url.assert_called_once()

    def test_raises_without_redis_package(self):
        with patch("nitro.domain.repository.redis.HAS_REDIS", False):
            with pytest.raises(ImportError, match="redis package required"):
                RedisRepository()


# ---------------------------------------------------------------------------
# Key format
# ---------------------------------------------------------------------------

class TestKeyFormat:
    """Internal _key() builds the correct Redis key strings."""

    def test_key_with_id(self, repo):
        assert repo._key(FakeEntity, "abc") == "test:FakeEntity:abc"

    def test_key_pattern_without_id(self, repo):
        assert repo._key(FakeEntity) == "test:FakeEntity:*"

    def test_key_uses_prefix(self, mock_redis):
        r = RedisRepository(url="redis://localhost/0", prefix="myapp")
        # reset for fresh instance
        RedisRepository._instance = None
        r2 = RedisRepository(url="redis://localhost/0", prefix="myapp")
        assert r2._key(FakeEntity, "1") == "myapp:FakeEntity:1"


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------

class TestRedisRepositorySave:
    """RedisRepository.save() serialises and stores entities."""

    def test_save_without_ttl_calls_set(self, repo, mock_redis, entity):
        result = repo.save(entity)
        assert result is True
        expected_key = "test:FakeEntity:e1"
        expected_payload = json.dumps(entity.model_dump(mode="json"))
        mock_redis.set.assert_called_once_with(expected_key, expected_payload)
        mock_redis.setex.assert_not_called()

    def test_save_with_ttl_calls_setex(self, repo, mock_redis, entity):
        result = repo.save(entity, ttl=60)
        assert result is True
        expected_key = "test:FakeEntity:e1"
        expected_payload = json.dumps(entity.model_dump(mode="json"))
        mock_redis.setex.assert_called_once_with(expected_key, 60, expected_payload)
        mock_redis.set.assert_not_called()

    def test_save_with_default_ttl_calls_setex(self, mock_redis):
        repo = RedisRepository(url="redis://localhost/0", prefix="test", default_ttl=120)
        entity = FakeEntity(id="d1", name="Default TTL", value=0)
        repo.save(entity)
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[1] == 120  # TTL argument

    def test_save_publishes_change_notification(self, repo, mock_redis, entity):
        repo.save(entity)
        channel = "test:changes:FakeEntity"
        expected_msg = json.dumps({"action": "save", "id": "e1"})
        mock_redis.publish.assert_called_once_with(channel, expected_msg)

    def test_save_returns_true(self, repo, mock_redis, entity):
        assert repo.save(entity) is True


# ---------------------------------------------------------------------------
# get()
# ---------------------------------------------------------------------------

class TestRedisRepositoryGet:
    """RedisRepository.get() deserialises entities from Redis."""

    def test_get_returns_entity_when_found(self, repo, mock_redis, entity):
        mock_redis.get.return_value = json.dumps(entity.model_dump(mode="json"))
        result = repo.get(FakeEntity, "e1")
        assert isinstance(result, FakeEntity)
        assert result.id == "e1"
        assert result.name == "Widget"
        assert result.value == 7
        mock_redis.get.assert_called_once_with("test:FakeEntity:e1")

    def test_get_returns_none_when_missing(self, repo, mock_redis):
        mock_redis.get.return_value = None
        result = repo.get(FakeEntity, "missing")
        assert result is None

    def test_get_uses_correct_key(self, repo, mock_redis):
        mock_redis.get.return_value = None
        repo.get(FakeEntity, "xyz")
        mock_redis.get.assert_called_once_with("test:FakeEntity:xyz")


# ---------------------------------------------------------------------------
# find()
# ---------------------------------------------------------------------------

class TestRedisRepositoryFind:
    """RedisRepository.find() is intentionally unimplemented."""

    def test_find_always_returns_none(self, repo):
        result = repo.find("any-id")
        assert result is None

    def test_find_does_not_touch_redis(self, repo, mock_redis):
        repo.find("some-id")
        mock_redis.get.assert_not_called()
        mock_redis.keys.assert_not_called()


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------

class TestRedisRepositoryDelete:
    """RedisRepository.delete() removes entities and publishes notifications."""

    def test_delete_by_class_and_id_returns_true(self, repo, mock_redis):
        mock_redis.delete.return_value = 1
        result = repo.delete(FakeEntity, "e1")
        assert result is True
        mock_redis.delete.assert_called_once_with("test:FakeEntity:e1")

    def test_delete_by_class_and_id_returns_false_when_missing(self, repo, mock_redis):
        mock_redis.delete.return_value = 0
        result = repo.delete(FakeEntity, "ghost")
        assert result is False

    def test_delete_by_entity_object(self, repo, mock_redis, entity):
        mock_redis.delete.return_value = 1
        result = repo.delete(entity)
        assert result is True
        mock_redis.delete.assert_called_once_with("test:FakeEntity:e1")

    def test_delete_publishes_notification_on_success(self, repo, mock_redis, entity):
        mock_redis.delete.return_value = 1
        repo.delete(entity)
        channel = "test:changes:FakeEntity"
        expected_msg = json.dumps({"action": "delete", "id": "e1"})
        mock_redis.publish.assert_called_once_with(channel, expected_msg)

    def test_delete_does_not_publish_when_key_missing(self, repo, mock_redis, entity):
        mock_redis.delete.return_value = 0
        repo.delete(entity)
        mock_redis.publish.assert_not_called()

    def test_delete_by_class_publishes_correct_channel(self, repo, mock_redis):
        mock_redis.delete.return_value = 1
        repo.delete(FakeEntity, "42")
        channel = "test:changes:FakeEntity"
        expected_msg = json.dumps({"action": "delete", "id": "42"})
        mock_redis.publish.assert_called_once_with(channel, expected_msg)


# ---------------------------------------------------------------------------
# exists()
# ---------------------------------------------------------------------------

class TestRedisRepositoryExists:
    """RedisRepository.exists() checks key presence."""

    def test_exists_returns_true_when_key_present(self, repo, mock_redis):
        mock_redis.exists.return_value = 1
        assert repo.exists(FakeEntity, "e1") is True
        mock_redis.exists.assert_called_once_with("test:FakeEntity:e1")

    def test_exists_returns_false_when_key_absent(self, repo, mock_redis):
        mock_redis.exists.return_value = 0
        assert repo.exists(FakeEntity, "ghost") is False


# ---------------------------------------------------------------------------
# all()
# ---------------------------------------------------------------------------

class TestRedisRepositoryAll:
    """RedisRepository.all() returns every entity of a class."""

    def test_all_returns_empty_list_when_no_keys(self, repo, mock_redis):
        mock_redis.keys.return_value = []
        result = repo.all(FakeEntity)
        assert result == []
        mock_redis.mget.assert_not_called()

    def test_all_returns_entities_when_keys_exist(self, repo, mock_redis):
        e1 = FakeEntity(id="1", name="A", value=1)
        e2 = FakeEntity(id="2", name="B", value=2)
        mock_redis.keys.return_value = ["test:FakeEntity:1", "test:FakeEntity:2"]
        mock_redis.mget.return_value = [
            json.dumps(e1.model_dump(mode="json")),
            json.dumps(e2.model_dump(mode="json")),
        ]
        result = repo.all(FakeEntity)
        assert len(result) == 2
        assert all(isinstance(r, FakeEntity) for r in result)
        ids = {r.id for r in result}
        assert ids == {"1", "2"}

    def test_all_skips_none_values_from_mget(self, repo, mock_redis):
        """mget may return None for keys that expired between keys() and mget()."""
        e1 = FakeEntity(id="1", name="A", value=1)
        mock_redis.keys.return_value = ["test:FakeEntity:1", "test:FakeEntity:2"]
        mock_redis.mget.return_value = [
            json.dumps(e1.model_dump(mode="json")),
            None,
        ]
        result = repo.all(FakeEntity)
        assert len(result) == 1
        assert result[0].id == "1"

    def test_all_uses_pattern_key(self, repo, mock_redis):
        mock_redis.keys.return_value = []
        repo.all(FakeEntity)
        mock_redis.keys.assert_called_once_with("test:FakeEntity:*")


# ---------------------------------------------------------------------------
# count()
# ---------------------------------------------------------------------------

class TestRedisRepositoryCount:
    """RedisRepository.count() returns the number of stored entities."""

    def test_count_returns_zero_when_empty(self, repo, mock_redis):
        mock_redis.keys.return_value = []
        assert repo.count(FakeEntity) == 0

    def test_count_returns_correct_number(self, repo, mock_redis):
        mock_redis.keys.return_value = ["k1", "k2", "k3"]
        assert repo.count(FakeEntity) == 3

    def test_count_uses_pattern_key(self, repo, mock_redis):
        mock_redis.keys.return_value = []
        repo.count(FakeEntity)
        mock_redis.keys.assert_called_once_with("test:FakeEntity:*")


# ---------------------------------------------------------------------------
# flush()
# ---------------------------------------------------------------------------

class TestRedisRepositoryFlush:
    """RedisRepository.flush() bulk-deletes keys."""

    def test_flush_with_model_class_deletes_matching_keys(self, repo, mock_redis):
        keys = ["test:FakeEntity:1", "test:FakeEntity:2"]
        mock_redis.keys.return_value = keys
        repo.flush(FakeEntity)
        mock_redis.keys.assert_called_once_with("test:FakeEntity:*")
        mock_redis.delete.assert_called_once_with(*keys)

    def test_flush_without_model_class_uses_prefix_pattern(self, repo, mock_redis):
        keys = ["test:FakeEntity:1", "test:OtherEntity:99"]
        mock_redis.keys.return_value = keys
        repo.flush()
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_called_once_with(*keys)

    def test_flush_does_not_call_delete_when_no_keys(self, repo, mock_redis):
        mock_redis.keys.return_value = []
        repo.flush(FakeEntity)
        mock_redis.delete.assert_not_called()


# ---------------------------------------------------------------------------
# subscribe_changes()
# ---------------------------------------------------------------------------

class TestRedisRepositorySubscribeChanges:
    """RedisRepository.subscribe_changes() returns a configured pubsub object."""

    def test_subscribe_changes_returns_pubsub(self, repo, mock_redis):
        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub
        result = repo.subscribe_changes(FakeEntity)
        assert result is mock_pubsub

    def test_subscribe_changes_subscribes_to_correct_channel(self, repo, mock_redis):
        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub
        repo.subscribe_changes(FakeEntity)
        mock_pubsub.subscribe.assert_called_once_with("test:changes:FakeEntity")

    def test_subscribe_changes_calls_pubsub_on_client(self, repo, mock_redis):
        repo.subscribe_changes(FakeEntity)
        mock_redis.pubsub.assert_called_once()
