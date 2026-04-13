"""
Metrics middleware for Sanic — auto-instruments HTTP request metrics.

Tracks:
- ``http_requests_total`` — counter by method + status code
- ``http_request_duration_seconds`` — histogram of response time
- ``http_requests_in_progress`` — gauge of concurrent requests
"""

from __future__ import annotations

import time
from typing import Any, Optional

from .base import Counter, Gauge, Histogram
from .registry import MetricsRegistry


def metrics_middleware(
    app: Any,
    registry: Optional[MetricsRegistry] = None,
    *,
    prefix: str = "http",
    buckets: tuple = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")),
) -> MetricsRegistry:
    """Attach HTTP metrics middleware to a Sanic app.

    Creates three metrics:
    - ``{prefix}_requests_total`` — Counter(method, status)
    - ``{prefix}_request_duration_seconds`` — Histogram(method)
    - ``{prefix}_requests_in_progress`` — Gauge

    Args:
        app: Sanic application instance.
        registry: Optional existing registry. Creates one if not provided.
        prefix: Metric name prefix (default ``http``).
        buckets: Histogram buckets for duration.

    Returns:
        The MetricsRegistry with the three metrics registered.

    Example::

        from sanic import Sanic
        from nitro.metrics import MetricsRegistry, metrics_middleware

        app = Sanic("MyApp")
        registry = metrics_middleware(app)
    """
    if registry is None:
        registry = MetricsRegistry()

    requests_total = registry.counter(
        f"{prefix}_requests_total",
        "Total HTTP requests",
        labels=["method", "status"],
    )
    duration = registry.histogram(
        f"{prefix}_request_duration_seconds",
        "HTTP request duration in seconds",
        labels=["method"],
        buckets=buckets,
    )
    in_progress = registry.gauge(
        f"{prefix}_requests_in_progress",
        "HTTP requests currently being processed",
    )

    @app.middleware("request")
    async def _metrics_request(request: Any) -> None:
        request.ctx._metrics_start = time.monotonic()
        in_progress.inc()

    @app.middleware("response")
    async def _metrics_response(request: Any, response: Any) -> None:
        elapsed = time.monotonic() - getattr(
            request.ctx, "_metrics_start", time.monotonic()
        )
        method = request.method
        status = str(response.status)
        requests_total.inc(method=method, status=status)
        duration.observe(elapsed, method=method)
        in_progress.dec()

    return registry
