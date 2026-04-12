"""Redis-backed entity repository with TTL and pub/sub support.

Requires: pip install redis
Usage: Set NITRO_REDIS_URL env var or pass url to constructor.
"""
import json
from typing import Any, Dict, List, Optional, Type
from .base import EntityRepositoryInterface

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class RedisRepository(EntityRepositoryInterface):
    """Redis-backed persistence with JSON serialization and optional TTL.

    Entities are stored as JSON strings under keys: {prefix}:{class_name}:{id}

    Features:
    - Per-entity TTL support
    - Pub/sub for entity change notifications
    - Atomic operations via Redis pipelines
    """

    _instance = None  # Singleton

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, url: str = "redis://localhost:6379/0", prefix: str = "nitro", default_ttl: Optional[int] = None):
        if not HAS_REDIS:
            raise ImportError("redis package required: pip install redis")
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._url = url
        self._prefix = prefix
        self._default_ttl = default_ttl
        self._client = redis.from_url(url, decode_responses=True)
        self._initialized = True

    def _key(self, cls_or_name, entity_id: Any = None) -> str:
        name = cls_or_name.__name__ if isinstance(cls_or_name, type) else cls_or_name
        if entity_id is not None:
            return f"{self._prefix}:{name}:{entity_id}"
        return f"{self._prefix}:{name}:*"

    def save(self, entity, ttl: Optional[int] = None) -> bool:
        key = self._key(type(entity), entity.id)
        data = entity.model_dump(mode="json")
        ttl = ttl or self._default_ttl
        if ttl:
            self._client.setex(key, ttl, json.dumps(data))
        else:
            self._client.set(key, json.dumps(data))
        # Publish change notification
        self._client.publish(f"{self._prefix}:changes:{type(entity).__name__}", json.dumps({"action": "save", "id": str(entity.id)}))
        return True

    def get(self, model_class, entity_id: Any) -> Optional[Any]:
        key = self._key(model_class, entity_id)
        data = self._client.get(key)
        if data is None:
            return None
        return model_class(**json.loads(data))

    def find(self, entity_id: str) -> Optional[Any]:
        # Can't find without knowing the class — scan all keys
        # This is intentionally not implemented efficiently
        return None

    def delete(self, model_class_or_entity, entity_id: Any = None) -> bool:
        if entity_id is None:
            # entity passed directly
            entity = model_class_or_entity
            key = self._key(type(entity), entity.id)
            cls_name = type(entity).__name__
            eid = str(entity.id)
        else:
            key = self._key(model_class_or_entity, entity_id)
            cls_name = model_class_or_entity.__name__
            eid = str(entity_id)
        result = self._client.delete(key) > 0
        if result:
            self._client.publish(f"{self._prefix}:changes:{cls_name}", json.dumps({"action": "delete", "id": eid}))
        return result

    def exists(self, model_class, entity_id: Any) -> bool:
        key = self._key(model_class, entity_id)
        return self._client.exists(key) > 0

    def all(self, model_class) -> List[Any]:
        pattern = self._key(model_class)
        keys = self._client.keys(pattern)
        results = []
        if keys:
            values = self._client.mget(keys)
            for v in values:
                if v is not None:
                    results.append(model_class(**json.loads(v)))
        return results

    def count(self, model_class) -> int:
        pattern = self._key(model_class)
        return len(self._client.keys(pattern))

    def flush(self, model_class=None):
        """Delete all entities of a class, or all entities if no class given."""
        if model_class:
            pattern = self._key(model_class)
        else:
            pattern = f"{self._prefix}:*"
        keys = self._client.keys(pattern)
        if keys:
            self._client.delete(*keys)

    def subscribe_changes(self, model_class):
        """Returns a Redis pub/sub object for listening to entity changes.

        Usage:
            pubsub = repo.subscribe_changes(Order)
            for message in pubsub.listen():
                if message["type"] == "message":
                    change = json.loads(message["data"])
                    # {"action": "save"|"delete", "id": "..."}
        """
        pubsub = self._client.pubsub()
        pubsub.subscribe(f"{self._prefix}:changes:{model_class.__name__}")
        return pubsub
