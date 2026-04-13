"""
nitro.health — Framework-agnostic health checks for the Nitro framework.

Provides:
- HealthCheck       : Abstract base for health check implementations
- HealthStatus      : Enum (healthy / degraded / unhealthy)
- CheckResult       : Result of a single health check
- HealthReport      : Aggregated result across all checks
- HealthRegistry    : Central coordinator — register checks, run probes

Built-in checks:
- DatabaseCheck     : Verify database connectivity via SELECT 1
- DiskSpaceCheck    : Monitor free disk space with configurable thresholds
- MemoryCheck       : Monitor system memory usage (Linux /proc/meminfo)
- CallableCheck     : Wrap any callable as a health check

Sanic integration:
- sanic_health      : Register /health, /health/live, /health/ready routes

Quick start::

    from nitro.health import HealthRegistry, DatabaseCheck, DiskSpaceCheck

    registry = HealthRegistry(version="1.0.0")
    registry.register(DatabaseCheck())
    registry.register(DiskSpaceCheck("/data"), readiness_only=True)

    report = registry.run_all()
    print(report.status)        # HealthStatus.HEALTHY
    print(report.to_dict())     # JSON-serialisable dict

Sanic integration::

    from sanic import Sanic
    from nitro.health import HealthRegistry, DatabaseCheck, sanic_health

    app = Sanic("MyApp")
    registry = HealthRegistry(version="1.0.0")
    registry.register(DatabaseCheck())
    sanic_health(app, registry)
    # GET /health, GET /health/live, GET /health/ready

Kubernetes probe configuration::

    livenessProbe:
      httpGet:
        path: /health/live
        port: 8000
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8000
"""

from .base import CheckResult, HealthCheck, HealthReport, HealthStatus
from .checks import CallableCheck, DatabaseCheck, DiskSpaceCheck, MemoryCheck
from .registry import HealthRegistry
from .sanic_integration import sanic_health

__all__ = [
    "HealthCheck",
    "HealthStatus",
    "CheckResult",
    "HealthReport",
    "HealthRegistry",
    "DatabaseCheck",
    "DiskSpaceCheck",
    "MemoryCheck",
    "CallableCheck",
    "sanic_health",
]
