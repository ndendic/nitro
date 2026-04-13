"""
Redis-backed session store for distributed deployments.

Requires the ``redis`` package::

    pip install redis

Example::

    from nitro.sessions.redis_store import RedisSessionStore

    store = RedisSessionStore(
        url="redis://localhost:6379/0",
        prefix="sessions:",
        ttl=3600,
    )
"""

from __future__ import annotations

import json
from typing import Any, Optional

from .base import SessionInterface

try:
    import redis.asyncio as aioredis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    aioredis = None  # type: ignore[assignment]


class RedisSessionStore(SessionInterface):
    """Redis-backed distributed session store.

    Sessions are stored as JSON strings with Redis TTL for automatic expiry.

    Args:
        url: Redis connection URL (default: "redis://localhost:6379/0").
        prefix: Key prefix for session keys (default: "nitro:sessions:").
        ttl: Session time-to-live in seconds (default: 3600).
        client: Optional pre-configured async Redis client.

    Raises:
        ImportError: If the ``redis`` package is not installed.

    Example::

        store = RedisSessionStore(
            url="redis://localhost:6379/0",
            prefix="myapp:sessions:",
            ttl=7200,
        )
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        prefix: str = "nitro:sessions:",
        ttl: int = 3600,
        client: Any = None,
    ):
        if not HAS_REDIS and client is None:
            raise ImportError(
                "Redis session store requires the redis package. "
                "Install with: pip install redis"
            )
        self._url = url
        self._prefix = prefix
        self._ttl = ttl
        self._client = client

    async def _get_client(self) -> Any:
        if self._client is None:
            self._client = aioredis.from_url(self._url, decode_responses=True)
        return self._client

    def _key(self, session_id: str) -> str:
        return f"{self._prefix}{session_id}"

    async def load(self, session_id: str) -> Optional[dict[str, Any]]:
        client = await self._get_client()
        raw = await client.get(self._key(session_id))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    async def save(self, session_id: str, data: dict[str, Any]) -> None:
        client = await self._get_client()
        raw = json.dumps(data, separators=(",", ":"))
        if self._ttl > 0:
            await client.setex(self._key(session_id), self._ttl, raw)
        else:
            await client.set(self._key(session_id), raw)

    async def delete(self, session_id: str) -> None:
        client = await self._get_client()
        await client.delete(self._key(session_id))

    async def exists(self, session_id: str) -> bool:
        client = await self._get_client()
        return bool(await client.exists(self._key(session_id)))

    async def clear_all(self) -> int:
        """Delete all sessions with this store's prefix.

        Uses SCAN to find matching keys, then deletes them in batches.
        """
        client = await self._get_client()
        pattern = f"{self._prefix}*"
        count = 0
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
                count += len(keys)
            if cursor == 0:
                break
        return count

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
