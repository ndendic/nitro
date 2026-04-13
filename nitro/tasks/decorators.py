"""
Task decorators for the Nitro task queue.

Provides:
- ``@task``    : Decorator that turns a function into a queueable task.
- ``TaskProxy``: Wrapper returned by ``@task`` — provides ``.delay()``
  and ``.apply_async()`` for enqueueing.
"""

from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Callable, Optional

from .base import TaskMessage, TaskQueueInterface, TaskResult, generate_task_id


class TaskProxy:
    """Wrapper around a task function that enables deferred execution.

    Created by the ``@task`` decorator. Call the proxy directly to run
    synchronously; use ``.delay()`` or ``.apply_async()`` to enqueue.

    Attributes:
        name: Registered task name (``module.qualname``).
        func: The original callable.
        queue: Bound queue backend (set via ``bind``).
        max_retries: Default retry count for this task.
    """

    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        max_retries: int = 0,
    ):
        self.func = func
        self.name = name or f"{func.__module__}.{func.__qualname__}"
        self.max_retries = max_retries
        self._queue: Optional[TaskQueueInterface] = None
        functools.update_wrapper(self, func)

    def bind(self, queue: TaskQueueInterface) -> "TaskProxy":
        """Bind this task to a queue backend.

        Must be called before ``.delay()`` or ``.apply_async()``.
        Typically done automatically by ``Worker.register()``.
        """
        self._queue = queue
        return self

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the task function synchronously (no queue involved)."""
        return self.func(*args, **kwargs)

    async def delay(self, *args: Any, **kwargs: Any) -> str:
        """Enqueue the task with default settings.

        Shorthand for ``apply_async(args=args, kwargs=kwargs)``.

        Returns:
            The task ID.

        Raises:
            RuntimeError: If no queue is bound.
        """
        return await self.apply_async(args=args, kwargs=kwargs)

    async def apply_async(
        self,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        max_retries: Optional[int] = None,
        eta: Optional[float] = None,
        countdown: Optional[float] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """Enqueue the task with full control over execution parameters.

        Args:
            args: Positional arguments for the task function.
            kwargs: Keyword arguments for the task function.
            max_retries: Override the default max retry count.
            eta: Earliest eligible execution time (unix timestamp).
            countdown: Delay in seconds from now (converted to *eta*).
            task_id: Custom task ID (auto-generated if omitted).

        Returns:
            The task ID.

        Raises:
            RuntimeError: If no queue is bound.
        """
        if self._queue is None:
            raise RuntimeError(
                f"Task '{self.name}' is not bound to a queue. "
                "Call task.bind(queue) or register it with a Worker first."
            )

        if countdown is not None and eta is None:
            eta = time.time() + countdown

        msg = TaskMessage(
            task_id=task_id or generate_task_id(),
            name=self.name,
            args=args,
            kwargs=kwargs or {},
            max_retries=max_retries if max_retries is not None else self.max_retries,
            eta=eta,
        )
        return await self._queue.enqueue(msg)


def task(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    max_retries: int = 0,
) -> Any:
    """Decorator that turns a function into a queueable background task.

    Can be used with or without parentheses::

        @task
        def send_email(to, subject, body):
            ...

        @task(max_retries=3)
        async def process_upload(file_id):
            ...

    The decorated function becomes a ``TaskProxy`` instance. Call it
    directly for synchronous execution, or use ``.delay()`` /
    ``.apply_async()`` for background execution via a queue.

    Args:
        func: The function to decorate (when used without parentheses).
        name: Custom task name. Defaults to ``module.qualname``.
        max_retries: Number of automatic retries on failure (default: 0).

    Returns:
        A ``TaskProxy`` wrapping the original function.
    """
    if func is not None:
        # @task without parentheses
        return TaskProxy(func, name=name, max_retries=max_retries)

    # @task(...) with parentheses
    def decorator(fn: Callable) -> TaskProxy:
        return TaskProxy(fn, name=name, max_retries=max_retries)

    return decorator
