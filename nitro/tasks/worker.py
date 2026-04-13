"""
Task worker — pulls messages from a queue and executes them.

The worker runs as an ``asyncio.Task`` and can be started/stopped
programmatically or integrated into a web framework's lifespan.
"""

from __future__ import annotations

import asyncio
import logging
import time
import traceback
from typing import Any, Callable, Dict, Optional

from .base import (
    TaskMessage,
    TaskQueueInterface,
    TaskResult,
    TaskStatus,
)

logger = logging.getLogger("nitro.tasks.worker")


class Worker:
    """Async task worker that processes messages from a queue.

    Args:
        queue: Task queue backend to pull work from.
        concurrency: Maximum number of tasks to process in parallel.
        poll_interval: Seconds between dequeue attempts when idle.
    """

    def __init__(
        self,
        queue: TaskQueueInterface,
        concurrency: int = 4,
        poll_interval: float = 0.5,
    ):
        self.queue = queue
        self.concurrency = concurrency
        self.poll_interval = poll_interval

        self._registry: Dict[str, Callable] = {}
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._semaphore: Optional[asyncio.Semaphore] = None

    # ------------------------------------------------------------------
    # Task registration
    # ------------------------------------------------------------------

    def register(self, name: str, func: Callable) -> None:
        """Register a callable under a task name.

        Args:
            name: Unique task name (usually ``module.qualname``).
            func: Sync or async callable to invoke.
        """
        self._registry[name] = func

    def get_registered(self, name: str) -> Optional[Callable]:
        """Look up a registered task function by name."""
        return self._registry.get(name)

    @property
    def registered_tasks(self) -> Dict[str, Callable]:
        """Read-only view of all registered task names and callables."""
        return dict(self._registry)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the worker loop.

        Spawns *concurrency* consumer coroutines that pull from the queue.
        Returns immediately — the consumers run in the background.
        """
        if self._running:
            return
        self._running = True
        self._semaphore = asyncio.Semaphore(self.concurrency)
        logger.info(
            "Worker starting (concurrency=%d, poll=%.1fs)",
            self.concurrency,
            self.poll_interval,
        )
        self._tasks = [
            asyncio.create_task(self._consumer_loop(i))
            for i in range(self.concurrency)
        ]

    async def stop(self, timeout: float = 5.0) -> None:
        """Gracefully stop the worker.

        Args:
            timeout: Seconds to wait for in-flight tasks to complete.
        """
        self._running = False
        if self._tasks:
            done, pending = await asyncio.wait(
                self._tasks, timeout=timeout
            )
            for t in pending:
                t.cancel()
            self._tasks.clear()
        logger.info("Worker stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Consumer loop
    # ------------------------------------------------------------------

    async def _consumer_loop(self, worker_id: int) -> None:
        """Single consumer coroutine that dequeues and executes tasks."""
        while self._running:
            msg = await self.queue.dequeue(timeout=self.poll_interval)
            if msg is None:
                continue
            await self._execute(msg, worker_id)

    async def _execute(self, msg: TaskMessage, worker_id: int) -> None:
        """Execute a single task message and store the result."""
        func = self._registry.get(msg.name)
        if func is None:
            logger.error("No handler registered for task '%s'", msg.name)
            result = TaskResult(
                task_id=msg.task_id,
                name=msg.name,
                status=TaskStatus.FAILED,
                error=f"No handler registered for task '{msg.name}'",
                created_at=msg.created_at,
                started_at=time.time(),
                finished_at=time.time(),
                retries=msg.retry_count,
            )
            await self.queue.store_result(result)
            return

        started = time.time()
        try:
            if asyncio.iscoroutinefunction(func):
                ret = await func(*msg.args, **msg.kwargs)
            else:
                ret = func(*msg.args, **msg.kwargs)

            result = TaskResult(
                task_id=msg.task_id,
                name=msg.name,
                status=TaskStatus.COMPLETED,
                result=ret,
                created_at=msg.created_at,
                started_at=started,
                finished_at=time.time(),
                retries=msg.retry_count,
            )
            logger.debug(
                "Worker-%d completed task %s (%s) in %.3fs",
                worker_id,
                msg.task_id,
                msg.name,
                result.duration,
            )
        except Exception as exc:
            # Retry logic
            if msg.retry_count < msg.max_retries:
                msg.retry_count += 1
                logger.warning(
                    "Worker-%d retrying task %s (%s) attempt %d/%d: %s",
                    worker_id,
                    msg.task_id,
                    msg.name,
                    msg.retry_count,
                    msg.max_retries,
                    exc,
                )
                await self.queue.enqueue(msg)
                return

            result = TaskResult(
                task_id=msg.task_id,
                name=msg.name,
                status=TaskStatus.FAILED,
                error=f"{type(exc).__name__}: {exc}",
                created_at=msg.created_at,
                started_at=started,
                finished_at=time.time(),
                retries=msg.retry_count,
            )
            logger.error(
                "Worker-%d task %s (%s) failed: %s",
                worker_id,
                msg.task_id,
                msg.name,
                exc,
            )

        await self.queue.store_result(result)
