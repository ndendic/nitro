"""
Sanic integration for the Nitro health check system.

Registers ``/health``, ``/health/live``, and ``/health/ready`` endpoints
on a Sanic app with a single function call.

Example::

    from sanic import Sanic
    from nitro.health import HealthRegistry, DatabaseCheck, sanic_health

    app = Sanic("MyApp")
    registry = HealthRegistry(version="1.0.0")
    registry.register(DatabaseCheck())

    sanic_health(app, registry)
    # Now: GET /health, GET /health/live, GET /health/ready
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import HealthStatus

if TYPE_CHECKING:
    from sanic import Sanic

    from .registry import HealthRegistry


def sanic_health(
    app: "Sanic",
    registry: "HealthRegistry",
    *,
    prefix: str = "/health",
) -> None:
    """Register health-check routes on a Sanic app.

    Args:
        app: The Sanic application instance.
        registry: A configured ``HealthRegistry``.
        prefix: URL prefix for the health endpoints (default ``"/health"``).

    Routes registered:
        - ``GET {prefix}``      — full report (all checks)
        - ``GET {prefix}/live`` — liveness probe (critical checks)
        - ``GET {prefix}/ready``— readiness probe
    """
    from sanic.response import json as json_response

    def _status_code(status: HealthStatus) -> int:
        if status == HealthStatus.HEALTHY:
            return 200
        elif status == HealthStatus.DEGRADED:
            return 200
        else:
            return 503

    @app.get(prefix)
    async def health_all(request):
        report = registry.run_all()
        return json_response(report.to_dict(), status=_status_code(report.status))

    @app.get(f"{prefix}/live")
    async def health_live(request):
        report = registry.liveness()
        return json_response(report.to_dict(), status=_status_code(report.status))

    @app.get(f"{prefix}/ready")
    async def health_ready(request):
        report = registry.readiness()
        return json_response(report.to_dict(), status=_status_code(report.status))
