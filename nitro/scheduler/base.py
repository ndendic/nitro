"""
Base types for the Nitro scheduler module.
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


class JobStatus(enum.Enum):
    """Lifecycle states for a scheduled job."""

    ACTIVE = "active"
    PAUSED = "paused"
    REMOVED = "removed"


@dataclass
class JobRun:
    """Record of a single job execution.

    Attributes:
        run_id: Unique identifier for this run.
        job_name: Name of the scheduled job.
        started_at: Unix timestamp when execution began.
        finished_at: Unix timestamp when execution ended, or ``None``.
        success: Whether the run completed without error.
        result: Return value on success.
        error: Exception message on failure.
    """

    run_id: str
    job_name: str
    started_at: float
    finished_at: Optional[float] = None
    success: bool = True
    result: Any = None
    error: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        """Wall-clock seconds between start and finish, or ``None``."""
        if self.finished_at is not None:
            return self.finished_at - self.started_at
        return None


def generate_run_id() -> str:
    """Return a short, unique run identifier."""
    return uuid.uuid4().hex[:12]


@dataclass
class ScheduleEntry:
    """A single scheduled job definition.

    Attributes:
        name: Unique job name (defaults to function qualname).
        schedule: Cron expression string or interval string (e.g. ``"30s"``, ``"5m"``).
        func: The callable to execute.
        status: Current lifecycle state.
        max_history: Maximum number of ``JobRun`` records to keep.
        last_run_at: Unix timestamp of last execution, or ``None``.
        next_run_at: Unix timestamp of next scheduled execution, or ``None``.
        run_count: Total number of times this job has executed.
        error_count: Total number of failed executions.
        history: Recent ``JobRun`` records (bounded by ``max_history``).
    """

    name: str
    schedule: str
    func: Callable
    status: JobStatus = JobStatus.ACTIVE
    max_history: int = 10
    last_run_at: Optional[float] = None
    next_run_at: Optional[float] = None
    run_count: int = 0
    error_count: int = 0
    history: list[JobRun] = field(default_factory=list)

    def record_run(self, run: JobRun) -> None:
        """Append a run record, trimming history to ``max_history``."""
        self.history.append(run)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        self.run_count += 1
        if not run.success:
            self.error_count += 1
        self.last_run_at = run.started_at

    @property
    def last_run(self) -> Optional[JobRun]:
        """Most recent run, or ``None``."""
        return self.history[-1] if self.history else None

    @property
    def success_rate(self) -> float:
        """Fraction of successful runs (0.0–1.0). Returns 1.0 if no runs."""
        if self.run_count == 0:
            return 1.0
        return (self.run_count - self.error_count) / self.run_count
