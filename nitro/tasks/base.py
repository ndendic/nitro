"""
Abstract base interface for Nitro task queue backends.

All task queue implementations must subclass ``TaskQueueInterface`` and
implement every abstract method. This ensures backends are interchangeable.
"""

from __future__ import annotations

import enum
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(enum.Enum):
    """Lifecycle states for a queued task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class TaskResult:
    """Outcome of a completed (or failed) task execution.

    Attributes:
        task_id: Unique identifier for the task.
        name: Registered task name (``module.qualname``).
        status: Final status after execution.
        result: Return value on success, ``None`` otherwise.
        error: Exception message on failure, ``None`` otherwise.
        created_at: Unix timestamp when the task was enqueued.
        started_at: Unix timestamp when execution began, or ``None``.
        finished_at: Unix timestamp when execution ended, or ``None``.
        retries: Number of retry attempts consumed so far.
    """

    task_id: str
    name: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    retries: int = 0

    @property
    def duration(self) -> Optional[float]:
        """Wall-clock seconds between start and finish, or ``None``."""
        if self.started_at is not None and self.finished_at is not None:
            return self.finished_at - self.started_at
        return None

    @property
    def is_done(self) -> bool:
        """``True`` if the task reached a terminal state."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )


@dataclass
class TaskMessage:
    """Internal message placed on the queue.

    Carries everything a worker needs to execute a task.
    """

    task_id: str
    name: str
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = 0
    retry_count: int = 0
    created_at: float = field(default_factory=time.time)
    eta: Optional[float] = None  # earliest eligible execution time


def generate_task_id() -> str:
    """Return a short, unique task identifier."""
    return uuid.uuid4().hex[:12]


class TaskQueueInterface(ABC):
    """Abstract base class for task queue backends.

    Provides a consistent interface for enqueuing, fetching, and
    managing background tasks. Subclasses must implement all abstract
    methods.

    The queue is *not* responsible for executing tasks — that is the
    ``Worker``'s job. The queue only stores and retrieves ``TaskMessage``
    objects.
    """

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    @abstractmethod
    async def enqueue(self, message: TaskMessage) -> str:
        """Add a task to the queue.

        Args:
            message: Task message to enqueue.

        Returns:
            The ``task_id`` of the enqueued message.
        """

    @abstractmethod
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[TaskMessage]:
        """Retrieve the next task from the queue.

        Blocks (up to *timeout* seconds) until a task is available.
        Returns ``None`` if the timeout is reached with no task.

        Args:
            timeout: Maximum seconds to wait. ``None`` = wait forever.
        """

    @abstractmethod
    async def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Fetch the result for a previously enqueued task.

        Args:
            task_id: Unique task identifier.

        Returns:
            ``TaskResult`` if the task has been processed, ``None`` otherwise.
        """

    @abstractmethod
    async def store_result(self, result: TaskResult) -> None:
        """Persist a task result after execution.

        Args:
            result: The outcome to store.
        """

    @abstractmethod
    async def size(self) -> int:
        """Return the number of tasks currently waiting in the queue."""

    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """Attempt to cancel a pending task before it starts.

        Args:
            task_id: Task to cancel.

        Returns:
            ``True`` if the task was found and cancelled, ``False`` otherwise.
        """

    @abstractmethod
    async def clear(self) -> int:
        """Remove all pending tasks from the queue.

        Returns:
            Number of tasks removed.
        """

    # ------------------------------------------------------------------
    # Listing / inspection (default implementations)
    # ------------------------------------------------------------------

    async def list_pending(self) -> List[TaskMessage]:
        """Return all pending task messages. Default returns empty list."""
        return []

    async def list_results(self, limit: int = 100) -> List[TaskResult]:
        """Return recent results. Default returns empty list."""
        return []
