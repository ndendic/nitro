"""
Redis-backed distributed task queue for the Nitro framework.

Requires the ``redis`` package::

    pip install redis

Uses Redis lists for FIFO task queuing and hashes for result storage.
Task messages and results are serialised to JSON.

Usage::

    from nitro.tasks.redis_queue import RedisTaskQueue
    from nitro.tasks import Worker, task

    queue = RedisTaskQueue(url="redis://localhost:6379/0")
    worker = Worker(queue, concurrency=4)

    @task(max_retries=3)
    async def send_email(to, subject, body):
        ...

    send_email.bind(queue)
    worker.register(send_email.name, send_email.func)
    await worker.start()
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from .base import (
    TaskMessage,
    TaskQueueInterface,
    TaskResult,
    TaskStatus,
)

try:
    import redis as _redis_module

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


def _task_message_to_dict(msg: TaskMessage) -> Dict[str, Any]:
    """Serialise a ``TaskMessage`` to a JSON-compatible dict."""
    return {
        "task_id": msg.task_id,
        "name": msg.name,
        "args": list(msg.args),
        "kwargs": msg.kwargs,
        "max_retries": msg.max_retries,
        "retry_count": msg.retry_count,
        "created_at": msg.created_at,
        "eta": msg.eta,
    }


def _dict_to_task_message(d: Dict[str, Any]) -> TaskMessage:
    """Deserialise a dict back into a ``TaskMessage``."""
    return TaskMessage(
        task_id=d["task_id"],
        name=d["name"],
        args=tuple(d.get("args", ())),
        kwargs=d.get("kwargs", {}),
        max_retries=d.get("max_retries", 0),
        retry_count=d.get("retry_count", 0),
        created_at=d.get("created_at", 0.0),
        eta=d.get("eta"),
    )


def _task_result_to_dict(result: TaskResult) -> Dict[str, Any]:
    """Serialise a ``TaskResult`` to a JSON-compatible dict."""
    return {
        "task_id": result.task_id,
        "name": result.name,
        "status": result.status.value,
        "result": result.result,
        "error": result.error,
        "created_at": result.created_at,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "retries": result.retries,
    }


def _dict_to_task_result(d: Dict[str, Any]) -> TaskResult:
    """Deserialise a dict back into a ``TaskResult``."""
    return TaskResult(
        task_id=d["task_id"],
        name=d["name"],
        status=TaskStatus(d["status"]),
        result=d.get("result"),
        error=d.get("error"),
        created_at=d.get("created_at", 0.0),
        started_at=d.get("started_at"),
        finished_at=d.get("finished_at"),
        retries=d.get("retries", 0),
    )


class RedisTaskQueue(TaskQueueInterface):
    """Redis-backed distributed task queue.

    Uses a Redis list for FIFO task storage and a hash for result
    persistence.  Supports ETA-based deferred tasks, cancellation,
    and result TTL.

    All keys are stored under ``{prefix}:*`` to avoid collisions
    with other Redis data in the same database.

    Args:
        url: Redis connection URL, e.g. ``redis://localhost:6379/0``.
        prefix: Namespace prefix for all Redis keys
            (default ``"nitro:tasks"``).
        result_ttl: Seconds to keep completed results in Redis
            (default: 3600).  ``None`` disables expiry.

    Raises:
        ImportError: If the ``redis`` package is not installed.

    Redis key layout::

        {prefix}:queue          — LIST  (FIFO task messages)
        {prefix}:pending:{id}   — STRING (pending task message JSON)
        {prefix}:result:{id}    — STRING (task result JSON, with TTL)
        {prefix}:cancelled      — SET   (cancelled task IDs)

    Example::

        queue = RedisTaskQueue(
            url="redis://localhost:6379/0",
            prefix="myapp:tasks",
            result_ttl=7200,
        )
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        prefix: str = "nitro:tasks",
        result_ttl: Optional[int] = 3600,
    ) -> None:
        if not HAS_REDIS:
            raise ImportError(
                "redis package is required for RedisTaskQueue: pip install redis"
            )
        self._url = url
        self._prefix = prefix
        self._result_ttl = result_ttl
        self._client = _redis_module.from_url(url, decode_responses=True)

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------

    def _k(self, suffix: str) -> str:
        """Return the namespaced Redis key."""
        return f"{self._prefix}:{suffix}"

    @property
    def _queue_key(self) -> str:
        return self._k("queue")

    @property
    def _cancelled_key(self) -> str:
        return self._k("cancelled")

    def _pending_key(self, task_id: str) -> str:
        return self._k(f"pending:{task_id}")

    def _result_key(self, task_id: str) -> str:
        return self._k(f"result:{task_id}")

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    async def enqueue(self, message: TaskMessage) -> str:
        """Add a task to the Redis queue.

        Stores the full message under a pending key and pushes it
        onto the queue list for FIFO ordering.
        """
        data = json.dumps(_task_message_to_dict(message))
        pipe = self._client.pipeline(transaction=False)
        pipe.set(self._pending_key(message.task_id), data)
        pipe.rpush(self._queue_key, data)
        pipe.execute()
        return message.task_id

    async def dequeue(self, timeout: Optional[float] = None) -> Optional[TaskMessage]:
        """Retrieve the next task from the Redis queue.

        Uses ``BLPOP`` for efficient blocking. Respects ETA scheduling
        and skips cancelled tasks.

        Args:
            timeout: Maximum seconds to wait. ``None`` waits up to 1s
                per attempt (avoids blocking forever in async context).
        """
        deadline = time.time() + timeout if timeout is not None else None

        while True:
            remaining = None
            if deadline is not None:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return None

            # BLPOP with a bounded wait — use min of remaining and 1s
            blpop_timeout = 1.0
            if remaining is not None:
                blpop_timeout = min(remaining, 1.0)

            result = self._client.blpop(self._queue_key, timeout=blpop_timeout)
            if result is None:
                if deadline is not None and time.time() >= deadline:
                    return None
                continue

            _, raw = result
            msg = _dict_to_task_message(json.loads(raw))

            # Check cancellation
            if self._client.sismember(self._cancelled_key, msg.task_id):
                # Remove from cancelled set (cleanup)
                self._client.srem(self._cancelled_key, msg.task_id)
                self._client.delete(self._pending_key(msg.task_id))
                continue

            # Check ETA
            if msg.eta is not None and time.time() < msg.eta:
                # Not ready yet — push back to the end and continue
                data = json.dumps(_task_message_to_dict(msg))
                self._client.rpush(self._queue_key, data)
                # Brief pause to avoid tight loop
                import asyncio

                await asyncio.sleep(0.05)
                continue

            # Remove pending key
            self._client.delete(self._pending_key(msg.task_id))
            return msg

    async def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Fetch the result for a previously enqueued task."""
        raw = self._client.get(self._result_key(task_id))
        if raw is None:
            return None
        return _dict_to_task_result(json.loads(raw))

    async def store_result(self, result: TaskResult) -> None:
        """Persist a task result in Redis with optional TTL."""
        data = json.dumps(_task_result_to_dict(result))
        key = self._result_key(result.task_id)
        if self._result_ttl is not None:
            self._client.setex(key, self._result_ttl, data)
        else:
            self._client.set(key, data)

    async def size(self) -> int:
        """Return the number of tasks currently in the queue."""
        return self._client.llen(self._queue_key)

    async def cancel(self, task_id: str) -> bool:
        """Cancel a pending task.

        Adds the task ID to a cancelled set. The task is skipped
        when dequeued.  A CANCELLED result is stored immediately.
        """
        # Check if the task is pending
        if not self._client.exists(self._pending_key(task_id)):
            return False

        pipe = self._client.pipeline(transaction=False)
        pipe.sadd(self._cancelled_key, task_id)
        pipe.delete(self._pending_key(task_id))
        pipe.execute()

        # Store cancellation result
        result = TaskResult(
            task_id=task_id,
            name="-",
            status=TaskStatus.CANCELLED,
            created_at=time.time(),
            finished_at=time.time(),
        )
        await self.store_result(result)
        return True

    async def clear(self) -> int:
        """Remove all pending tasks from the queue.

        Uses SCAN to find and delete all pending keys, then deletes
        the queue list.
        """
        # Count pending tasks
        count = self._client.llen(self._queue_key)

        pipe = self._client.pipeline(transaction=False)
        pipe.delete(self._queue_key)
        pipe.delete(self._cancelled_key)
        pipe.execute()

        # Clean up pending keys
        pattern = self._k("pending:*")
        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor, match=pattern, count=200)
            if keys:
                self._client.delete(*keys)
            if cursor == 0:
                break

        return count

    # ------------------------------------------------------------------
    # Listing / inspection
    # ------------------------------------------------------------------

    async def list_pending(self) -> List[TaskMessage]:
        """Return all pending task messages from the queue."""
        raw_items = self._client.lrange(self._queue_key, 0, -1)
        messages = []
        for raw in raw_items:
            try:
                msg = _dict_to_task_message(json.loads(raw))
                # Skip cancelled
                if not self._client.sismember(self._cancelled_key, msg.task_id):
                    messages.append(msg)
            except (json.JSONDecodeError, KeyError):
                continue
        return messages

    async def list_results(self, limit: int = 100) -> List[TaskResult]:
        """Return recent results by scanning result keys.

        Results are returned sorted by ``finished_at`` descending.
        """
        pattern = self._k("result:*")
        results: List[TaskResult] = []
        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor, match=pattern, count=200)
            for key in keys:
                raw = self._client.get(key)
                if raw is not None:
                    try:
                        results.append(_dict_to_task_result(json.loads(raw)))
                    except (json.JSONDecodeError, KeyError):
                        continue
            if cursor == 0:
                break

        # Sort by finished_at descending, None values last
        results.sort(
            key=lambda r: r.finished_at if r.finished_at is not None else 0.0,
            reverse=True,
        )
        return results[:limit]
