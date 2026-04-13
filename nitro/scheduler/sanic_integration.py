"""
Sanic lifecycle integration for the Nitro scheduler.

One-line setup::

    from nitro.scheduler import Scheduler, sanic_scheduler

    app = Sanic("MyApp")
    scheduler = Scheduler()
    sanic_scheduler(app, scheduler)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sanic import Sanic

    from .scheduler import Scheduler

logger = logging.getLogger("nitro.scheduler.sanic")


def sanic_scheduler(app: "Sanic", scheduler: "Scheduler") -> None:
    """Wire a ``Scheduler`` into a Sanic app's lifecycle.

    Registers ``before_server_start`` and ``after_server_stop`` hooks
    that start and stop the scheduler automatically.

    Args:
        app: Sanic application instance.
        scheduler: Scheduler instance to manage.
    """

    @app.before_server_start
    async def _start_scheduler(app, loop):
        await scheduler.start()
        logger.info("Scheduler started with Sanic app %r", app.name)

    @app.after_server_stop
    async def _stop_scheduler(app, loop):
        await scheduler.stop()
        logger.info("Scheduler stopped with Sanic app %r", app.name)
