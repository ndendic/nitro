"""
Built-in health checks for common infrastructure components.

Provides ready-to-use checks for:
- Database connectivity (SQLModel / SQLAlchemy)
- Redis connectivity
- Disk space
- Memory usage
- Custom callable checks
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, Optional

from .base import CheckResult, HealthCheck, HealthStatus


class DatabaseCheck(HealthCheck):
    """Check database connectivity by executing ``SELECT 1``.

    Uses the Nitro Entity repository to verify the database is reachable.

    Args:
        name: Check name (default ``"database"``).
        critical: Whether failure makes the whole report unhealthy.
    """

    def __init__(self, name: str = "database", *, critical: bool = True):
        super().__init__(name, critical=critical)

    def check(self) -> CheckResult:
        start = time.monotonic()
        try:
            from nitro.domain.entities.base_entity import Entity

            repo = Entity.repository()
            if repo is None:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message="No repository configured",
                    duration_ms=(time.monotonic() - start) * 1000,
                )
            with repo._session() as session:
                from sqlalchemy import text

                session.execute(text("SELECT 1"))
            elapsed = (time.monotonic() - start) * 1000
            return CheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Database is reachable",
                details={"latency_ms": round(elapsed, 2)},
                duration_ms=elapsed,
            )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {exc}",
                duration_ms=elapsed,
            )


class DiskSpaceCheck(HealthCheck):
    """Check available disk space on a given path.

    Args:
        path: Filesystem path to check (default ``"/"``).
        min_free_mb: Minimum free space in MB to be healthy (default 100).
        warn_free_mb: Below this MB, report as degraded (default 500).
        name: Check name (default ``"disk_space"``).
        critical: Whether failure makes the whole report unhealthy.
    """

    def __init__(
        self,
        path: str = "/",
        *,
        min_free_mb: int = 100,
        warn_free_mb: int = 500,
        name: str = "disk_space",
        critical: bool = False,
    ):
        super().__init__(name, critical=critical)
        self.path = path
        self.min_free_mb = min_free_mb
        self.warn_free_mb = warn_free_mb

    def check(self) -> CheckResult:
        start = time.monotonic()
        try:
            stat = os.statvfs(self.path)
            free_bytes = stat.f_bavail * stat.f_frsize
            total_bytes = stat.f_blocks * stat.f_frsize
            free_mb = free_bytes / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)
            used_pct = ((total_bytes - free_bytes) / total_bytes) * 100 if total_bytes else 0

            details: Dict[str, Any] = {
                "free_mb": round(free_mb, 1),
                "total_mb": round(total_mb, 1),
                "used_percent": round(used_pct, 1),
                "path": self.path,
            }

            elapsed = (time.monotonic() - start) * 1000

            if free_mb < self.min_free_mb:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Disk space critically low: {free_mb:.0f} MB free",
                    details=details,
                    duration_ms=elapsed,
                )
            elif free_mb < self.warn_free_mb:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message=f"Disk space low: {free_mb:.0f} MB free",
                    details=details,
                    duration_ms=elapsed,
                )
            else:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message=f"Disk OK: {free_mb:.0f} MB free",
                    details=details,
                    duration_ms=elapsed,
                )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Disk check failed: {exc}",
                duration_ms=elapsed,
            )


class MemoryCheck(HealthCheck):
    """Check system memory usage.

    Reads from ``/proc/meminfo`` on Linux. Returns degraded/unhealthy based
    on configurable thresholds.

    Args:
        max_used_pct: Usage percentage above which the check is unhealthy (default 95).
        warn_used_pct: Usage percentage above which the check is degraded (default 85).
        name: Check name (default ``"memory"``).
        critical: Whether failure makes the whole report unhealthy.
    """

    def __init__(
        self,
        *,
        max_used_pct: float = 95.0,
        warn_used_pct: float = 85.0,
        name: str = "memory",
        critical: bool = False,
    ):
        super().__init__(name, critical=critical)
        self.max_used_pct = max_used_pct
        self.warn_used_pct = warn_used_pct

    def check(self) -> CheckResult:
        start = time.monotonic()
        try:
            meminfo: Dict[str, int] = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().split()[0]
                        meminfo[key] = int(val)

            total_kb = meminfo.get("MemTotal", 0)
            available_kb = meminfo.get("MemAvailable", 0)

            if total_kb == 0:
                raise ValueError("Could not read MemTotal from /proc/meminfo")

            used_pct = ((total_kb - available_kb) / total_kb) * 100
            available_mb = available_kb / 1024
            total_mb = total_kb / 1024

            details: Dict[str, Any] = {
                "total_mb": round(total_mb, 1),
                "available_mb": round(available_mb, 1),
                "used_percent": round(used_pct, 1),
            }

            elapsed = (time.monotonic() - start) * 1000

            if used_pct >= self.max_used_pct:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Memory critically high: {used_pct:.1f}% used",
                    details=details,
                    duration_ms=elapsed,
                )
            elif used_pct >= self.warn_used_pct:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message=f"Memory high: {used_pct:.1f}% used",
                    details=details,
                    duration_ms=elapsed,
                )
            else:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message=f"Memory OK: {used_pct:.1f}% used",
                    details=details,
                    duration_ms=elapsed,
                )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {exc}",
                duration_ms=elapsed,
            )


class CallableCheck(HealthCheck):
    """Wrap any callable as a health check.

    The callable should return a ``CheckResult``, or raise an exception
    (which will be caught and converted to an unhealthy result).

    Args:
        name: Check name.
        fn: Callable that returns a ``CheckResult``.
        critical: Whether failure makes the whole report unhealthy.

    Example::

        def check_api():
            resp = requests.get("https://api.example.com/status", timeout=5)
            if resp.ok:
                return CheckResult("api", HealthStatus.HEALTHY)
            return CheckResult("api", HealthStatus.UNHEALTHY, message=f"HTTP {resp.status_code}")

        check = CallableCheck("api", check_api)
    """

    def __init__(
        self,
        name: str,
        fn: Callable[[], CheckResult],
        *,
        critical: bool = True,
    ):
        super().__init__(name, critical=critical)
        self.fn = fn

    def check(self) -> CheckResult:
        start = time.monotonic()
        try:
            result = self.fn()
            result.duration_ms = (time.monotonic() - start) * 1000
            return result
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {exc}",
                duration_ms=elapsed,
            )
