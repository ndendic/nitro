"""
Abstract base interface and data types for Nitro health checks.

All health-check implementations must subclass ``HealthCheck`` and implement
the ``check()`` method. This ensures checks are interchangeable and composable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class HealthStatus(str, Enum):
    """Health check result status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class CheckResult:
    """Result of a single health check.

    Attributes:
        name: Name of the check.
        status: Overall status (healthy / degraded / unhealthy).
        message: Optional human-readable description.
        details: Arbitrary metadata (latency, version, etc.).
        duration_ms: How long the check took to execute, in milliseconds.
    """

    name: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY

    @property
    def is_degraded(self) -> bool:
        return self.status == HealthStatus.DEGRADED

    @property
    def is_unhealthy(self) -> bool:
        return self.status == HealthStatus.UNHEALTHY

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "name": self.name,
            "status": self.status.value,
        }
        if self.message:
            d["message"] = self.message
        if self.details:
            d["details"] = self.details
        if self.duration_ms:
            d["duration_ms"] = round(self.duration_ms, 2)
        return d


@dataclass
class HealthReport:
    """Aggregated result of all registered health checks.

    Attributes:
        status: Overall status (worst-of across all checks).
        checks: Individual check results.
        version: Optional application version string.
    """

    status: HealthStatus
    checks: list[CheckResult] = field(default_factory=list)
    version: str = ""

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "status": self.status.value,
            "checks": [c.to_dict() for c in self.checks],
        }
        if self.version:
            d["version"] = self.version
        return d


class HealthCheck(ABC):
    """Abstract base class for health checks.

    Subclass this and implement ``check()`` to create a custom health check.

    Args:
        name: Human-readable name for the check (e.g. ``"database"``).
        critical: If ``True``, a failure marks the entire report as unhealthy.
            If ``False``, a failure only marks the report as degraded.
    """

    def __init__(self, name: str, *, critical: bool = True):
        self.name = name
        self.critical = critical

    @abstractmethod
    def check(self) -> CheckResult:
        """Execute the health check and return a result.

        Implementations should catch their own exceptions and return an
        unhealthy ``CheckResult`` rather than raising.
        """

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r}, critical={self.critical})"
