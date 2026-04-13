"""
Scheduler engine — manages and executes periodic jobs.

The scheduler runs as an ``asyncio.Task`` and supports both cron
expressions and interval-based schedules.
"""

from __future__ import annotations

import asyncio
import logging
import time
import traceback
from typing import Any, Callable, Dict, List, Optional

from .base import JobRun, JobStatus, ScheduleEntry, generate_run_id
from .cron import CronExpr
from .interval import extract_interval, is_interval_schedule

logger = logging.getLogger("nitro.scheduler")


class Scheduler:
    """Async periodic task scheduler.

    Manages a set of named jobs that execute on cron or interval schedules.

    Args:
        tick_interval: Seconds between scheduler ticks (precision ceiling).
            Smaller values = more precise timing but higher CPU. Default 1.0.

    Examples::

        scheduler = Scheduler()

        @scheduler.job("*/5 * * * *")
        async def every_five_minutes():
            ...

        @scheduler.job("@every/30s")
        async def every_thirty_seconds():
            ...

        await scheduler.start()
    """

    def __init__(self, tick_interval: float = 1.0) -> None:
        self.tick_interval = tick_interval
        self._jobs: Dict[str, ScheduleEntry] = {}
        self._cron_cache: Dict[str, CronExpr] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # Job registration
    # ------------------------------------------------------------------

    def job(
        self,
        schedule: str,
        *,
        name: Optional[str] = None,
        max_history: int = 10,
    ) -> Callable:
        """Decorator to register a function as a scheduled job.

        Args:
            schedule: Cron expression (``"*/5 * * * *"``) or interval
                      (``"@every/30s"`` or via ``every("30s")``).
            name: Job name. Defaults to function's qualified name.
            max_history: Max run records to keep per job.

        Returns:
            The original function, unmodified.

        Examples::

            @scheduler.job("0 9 * * 1-5")
            async def morning_report():
                ...
        """

        def decorator(func: Callable) -> Callable:
            job_name = name or func.__name__
            self.add_job(job_name, schedule, func, max_history=max_history)
            return func

        return decorator

    def add_job(
        self,
        name: str,
        schedule: str,
        func: Callable,
        *,
        max_history: int = 10,
    ) -> ScheduleEntry:
        """Programmatically add a scheduled job.

        Args:
            name: Unique job name.
            schedule: Cron expression or interval string.
            func: Sync or async callable.
            max_history: Max run records to keep.

        Returns:
            The created ``ScheduleEntry``.

        Raises:
            ValueError: If a job with this name already exists.
        """
        if name in self._jobs:
            raise ValueError(f"Job {name!r} already registered")

        entry = ScheduleEntry(
            name=name,
            schedule=schedule,
            func=func,
            max_history=max_history,
        )

        # Validate and cache schedule
        if is_interval_schedule(schedule):
            extract_interval(schedule)  # validates
        else:
            self._cron_cache[name] = CronExpr(schedule)

        # Compute initial next_run_at
        entry.next_run_at = self._compute_next_run(entry)
        self._jobs[name] = entry
        logger.info("Registered job %r with schedule %r", name, schedule)
        return entry

    def remove_job(self, name: str) -> bool:
        """Remove a job by name.

        Returns:
            ``True`` if the job was found and removed.
        """
        if name in self._jobs:
            self._jobs[name].status = JobStatus.REMOVED
            del self._jobs[name]
            self._cron_cache.pop(name, None)
            logger.info("Removed job %r", name)
            return True
        return False

    def pause_job(self, name: str) -> bool:
        """Pause a job (skip execution until resumed).

        Returns:
            ``True`` if the job was found and paused.
        """
        if name in self._jobs:
            self._jobs[name].status = JobStatus.PAUSED
            logger.info("Paused job %r", name)
            return True
        return False

    def resume_job(self, name: str) -> bool:
        """Resume a paused job.

        Returns:
            ``True`` if the job was found and resumed.
        """
        if name in self._jobs:
            entry = self._jobs[name]
            entry.status = JobStatus.ACTIVE
            entry.next_run_at = self._compute_next_run(entry)
            logger.info("Resumed job %r", name)
            return True
        return False

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def get_job(self, name: str) -> Optional[ScheduleEntry]:
        """Retrieve a job entry by name."""
        return self._jobs.get(name)

    def list_jobs(self) -> List[ScheduleEntry]:
        """Return all registered jobs."""
        return list(self._jobs.values())

    @property
    def job_count(self) -> int:
        """Number of registered jobs."""
        return len(self._jobs)

    @property
    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the scheduler loop.

        Returns immediately — the loop runs in the background.
        """
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "Scheduler started (tick=%.1fs, jobs=%d)",
            self.tick_interval,
            len(self._jobs),
        )

    async def stop(self, timeout: float = 5.0) -> None:
        """Gracefully stop the scheduler.

        Args:
            timeout: Seconds to wait for in-flight jobs to complete.
        """
        self._running = False
        if self._task is not None:
            try:
                await asyncio.wait_for(asyncio.shield(self._task), timeout=timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._task.cancel()
            self._task = None
        logger.info("Scheduler stopped")

    # ------------------------------------------------------------------
    # Run loop
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        """Main scheduler loop — checks and executes due jobs each tick."""
        while self._running:
            now = time.time()
            due_jobs = [
                entry
                for entry in self._jobs.values()
                if (
                    entry.status == JobStatus.ACTIVE
                    and entry.next_run_at is not None
                    and now >= entry.next_run_at
                )
            ]

            if due_jobs:
                # Run due jobs concurrently
                await asyncio.gather(
                    *(self._execute_job(entry) for entry in due_jobs),
                    return_exceptions=True,
                )

            await asyncio.sleep(self.tick_interval)

    async def _execute_job(self, entry: ScheduleEntry) -> None:
        """Execute a single job and record the result."""
        run = JobRun(
            run_id=generate_run_id(),
            job_name=entry.name,
            started_at=time.time(),
        )

        try:
            if asyncio.iscoroutinefunction(entry.func):
                result = await entry.func()
            else:
                result = entry.func()
            run.result = result
            run.success = True
            logger.debug("Job %r completed successfully", entry.name)
        except Exception as exc:
            run.success = False
            run.error = f"{type(exc).__name__}: {exc}"
            logger.error("Job %r failed: %s", entry.name, exc)

        run.finished_at = time.time()
        entry.record_run(run)
        entry.next_run_at = self._compute_next_run(entry)

    # ------------------------------------------------------------------
    # Schedule computation
    # ------------------------------------------------------------------

    def _compute_next_run(self, entry: ScheduleEntry) -> float:
        """Compute the next run time for a job."""
        now = time.time()
        if is_interval_schedule(entry.schedule):
            interval = extract_interval(entry.schedule)
            base = entry.last_run_at or now
            next_time = base + interval
            # If we're already past the next time, schedule from now
            if next_time <= now:
                next_time = now + interval
            return next_time
        else:
            cron = self._cron_cache.get(entry.name)
            if cron is None:
                cron = CronExpr(entry.schedule)
                self._cron_cache[entry.name] = cron
            return cron.next_fire_time(after=now)
