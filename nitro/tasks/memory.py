"""
In-memory task queue backend for development and testing.

Uses ``asyncio.Queue`` for task storage. All data is lost when the process
exits — for production, use ``RedisTaskQueue``.
"""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from typing import Dict, List, Optional

from .base import (
    TaskMessage,
    TaskQueueInterface,
    TaskResult,
    TaskStatus,
)


class MemoryTaskQueue(TaskQueueInterface):
    """In-process task queue backed by ``asyncio.Queue``.

    Suitable for development, testing, and single-process applications.

    Args:
        max_size: Maximum number of pending tasks. ``0`` = unlimited.
        result_ttl: Seconds to keep completed results (default: 3600).
    """

    def __init__(self, max_size: int = 0, result_ttl: int = 3600):
        self._queue: asyncio.Queue[TaskMessage] = asyncio.Queue(maxsize=max_size)
        self._results: OrderedDict[str, TaskResult] = OrderedDict()
        self._pending: Dict[str, TaskMessage] = {}
        self._result_ttl = result_ttl

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    async def enqueue(self, message: TaskMessage) -> str:
        """Add a task to the in-memory queue."""
        self._pending[message.task_id] = message
        await self._queue.put(message)
        return message.task_id

    async def dequeue(self, timeout: Optional[float] = None) -> Optional[TaskMessage]:
        """Retrieve the next task, respecting ETA scheduling.

        If the next message has a future ``eta``, it is re-queued and the
        method waits briefly before retrying (up to *timeout*).
        """
        deadline = time.time() + timeout if timeout is not None else None

        while True:
            remaining = None
            if deadline is not None:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return None

            try:
                msg = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=remaining,
                )
            except asyncio.TimeoutError:
                return None

            # Check cancellation
            if msg.task_id not in self._pending:
                # Already cancelled — skip
                continue

            # Check ETA
            if msg.eta is not None and time.time() < msg.eta:
                # Not ready yet — put back and yield briefly
                await self._queue.put(msg)
                await asyncio.sleep(0.05)
                continue

            self._pending.pop(msg.task_id, None)
            return msg

    async def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Look up a stored result by task ID."""
        self._evict_expired_results()
        return self._results.get(task_id)

    async def store_result(self, result: TaskResult) -> None:
        """Store a task result in memory."""
        self._results[result.task_id] = result

    async def size(self) -> int:
        """Number of tasks waiting in the queue."""
        return self._queue.qsize()

    async def cancel(self, task_id: str) -> bool:
        """Cancel a pending task by removing it from the pending index.

        The actual ``TaskMessage`` will be skipped when dequeued.
        """
        if task_id in self._pending:
            del self._pending[task_id]
            result = TaskResult(
                task_id=task_id,
                name="-",
                status=TaskStatus.CANCELLED,
                created_at=time.time(),
                finished_at=time.time(),
            )
            self._results[task_id] = result
            return True
        return False

    async def clear(self) -> int:
        """Remove all pending tasks."""
        count = len(self._pending)
        self._pending.clear()
        # Drain the asyncio queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        return count

    # ------------------------------------------------------------------
    # Listing / inspection
    # ------------------------------------------------------------------

    async def list_pending(self) -> List[TaskMessage]:
        """Return all pending task messages."""
        return list(self._pending.values())

    async def list_results(self, limit: int = 100) -> List[TaskResult]:
        """Return recent results, most recent first."""
        self._evict_expired_results()
        items = list(self._results.values())
        items.reverse()
        return items[:limit]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evict_expired_results(self) -> None:
        """Remove results older than ``result_ttl``."""
        if not self._result_ttl:
            return
        cutoff = time.time() - self._result_ttl
        expired = [
            tid
            for tid, r in self._results.items()
            if r.finished_at is not None and r.finished_at < cutoff
        ]
        for tid in expired:
            del self._results[tid]
