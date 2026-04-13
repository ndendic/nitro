"""
Health check registry — manages checks and produces aggregated reports.

The ``HealthRegistry`` is the central coordinator. Register checks at
startup, then call ``run_all()``, ``liveness()``, or ``readiness()`` to
produce health reports.

Liveness vs. Readiness:
- **Liveness** (``/health/live``): Is the process alive? If unhealthy,
  the orchestrator should restart the container.
- **Readiness** (``/health/ready``): Can this instance serve traffic?
  If not ready, the load balancer should stop sending requests.

By default, all checks contribute to both. Use ``liveness_only=True`` or
``readiness_only=True`` when registering to scope a check.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from .base import CheckResult, HealthCheck, HealthReport, HealthStatus


@dataclass
class _RegisteredCheck:
    """Internal wrapper tracking a check's scope."""

    check: HealthCheck
    liveness: bool = True
    readiness: bool = True


class HealthRegistry:
    """Central registry for health checks.

    Args:
        version: Optional application version string included in reports.

    Example::

        from nitro.health import HealthRegistry, DatabaseCheck, DiskSpaceCheck

        registry = HealthRegistry(version="1.2.3")
        registry.register(DatabaseCheck())
        registry.register(DiskSpaceCheck("/data"), readiness_only=True)

        report = registry.run_all()
        print(report.to_dict())
    """

    def __init__(self, version: str = ""):
        self.version = version
        self._checks: List[_RegisteredCheck] = []

    def register(
        self,
        check: HealthCheck,
        *,
        liveness_only: bool = False,
        readiness_only: bool = False,
    ) -> None:
        """Register a health check.

        Args:
            check: The health check instance.
            liveness_only: If ``True``, this check only runs for liveness probes.
            readiness_only: If ``True``, this check only runs for readiness probes.

        Raises:
            ValueError: If both ``liveness_only`` and ``readiness_only`` are set.
        """
        if liveness_only and readiness_only:
            raise ValueError("Cannot set both liveness_only and readiness_only")

        rc = _RegisteredCheck(
            check=check,
            liveness=not readiness_only,
            readiness=not liveness_only,
        )
        self._checks.append(rc)

    def unregister(self, name: str) -> bool:
        """Remove a check by name.

        Returns:
            ``True`` if a check was found and removed, ``False`` otherwise.
        """
        before = len(self._checks)
        self._checks = [rc for rc in self._checks if rc.check.name != name]
        return len(self._checks) < before

    @property
    def check_names(self) -> List[str]:
        """Return names of all registered checks."""
        return [rc.check.name for rc in self._checks]

    def _run(self, checks: List[_RegisteredCheck]) -> HealthReport:
        """Execute a list of checks and aggregate results."""
        results: List[CheckResult] = []
        worst = HealthStatus.HEALTHY

        for rc in checks:
            start = time.monotonic()
            result = rc.check.check()
            if result.duration_ms == 0:
                result.duration_ms = (time.monotonic() - start) * 1000
            results.append(result)

            if result.status == HealthStatus.UNHEALTHY:
                if rc.check.critical:
                    worst = HealthStatus.UNHEALTHY
                elif worst != HealthStatus.UNHEALTHY:
                    worst = HealthStatus.DEGRADED
            elif result.status == HealthStatus.DEGRADED:
                if worst == HealthStatus.HEALTHY:
                    worst = HealthStatus.DEGRADED

        return HealthReport(
            status=worst,
            checks=results,
            version=self.version,
        )

    def run_all(self) -> HealthReport:
        """Run all registered checks and return an aggregated report."""
        return self._run(self._checks)

    def liveness(self) -> HealthReport:
        """Run liveness checks only.

        Returns a report suitable for ``/health/live`` endpoints.
        """
        return self._run([rc for rc in self._checks if rc.liveness])

    def readiness(self) -> HealthReport:
        """Run readiness checks only.

        Returns a report suitable for ``/health/ready`` endpoints.
        """
        return self._run([rc for rc in self._checks if rc.readiness])
