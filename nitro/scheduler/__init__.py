"""
nitro.scheduler — Periodic task scheduler for the Nitro framework.

Complements ``nitro.tasks`` (one-shot background jobs) with cron-style
periodic execution.

Provides:
- Scheduler       : Async scheduler engine — manages and runs periodic jobs
- ScheduleEntry   : A single scheduled job definition
- CronExpr        : Lightweight cron expression parser (no external deps)
- JobStatus       : Job lifecycle states
- JobRun          : Record of a single job execution
- every           : Convenience builder for interval-based schedules

Quick start::

    from nitro.scheduler import Scheduler, every

    scheduler = Scheduler()

    @scheduler.job(every("30s"))
    async def cleanup_sessions():
        expired = Session.where(lambda s: s.is_expired)
        for s in expired:
            s.delete()
        return {"cleaned": len(expired)}

    @scheduler.job("*/5 * * * *")  # every 5 minutes (cron)
    async def send_digest():
        ...

    # Start/stop with your app:
    await scheduler.start()
    await scheduler.stop()

Sanic integration::

    from sanic import Sanic
    from nitro.scheduler import Scheduler, sanic_scheduler, every

    app = Sanic("MyApp")
    scheduler = Scheduler()

    @scheduler.job(every("1m"))
    async def heartbeat():
        print("alive")

    sanic_scheduler(app, scheduler)  # auto start/stop with Sanic lifecycle
"""

from .base import JobRun, JobStatus, ScheduleEntry
from .cron import CronExpr
from .interval import every
from .scheduler import Scheduler
from .sanic_integration import sanic_scheduler

__all__ = [
    "Scheduler",
    "ScheduleEntry",
    "CronExpr",
    "JobStatus",
    "JobRun",
    "every",
    "sanic_scheduler",
]
