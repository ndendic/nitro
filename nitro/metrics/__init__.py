"""nitro.metrics — Application metrics and observability.

Provides Prometheus-compatible metric types with thread-safe collection,
decorators for auto-instrumentation, HTTP middleware, and export endpoints.

Metric types:
- Counter      : Monotonically increasing (requests, errors)
- Gauge        : Up/down values (connections, queue depth)
- Histogram    : Distribution in buckets (latency, sizes)
- Summary      : Quantile estimation over sliding window (p50, p99)

Quick start::

    from nitro.metrics import MetricsRegistry

    registry = MetricsRegistry()
    requests = registry.counter("http_requests_total", "Total requests", labels=["method"])
    latency = registry.histogram("request_duration_seconds", "Duration")

    requests.inc(method="GET")
    latency.observe(0.042)

Sanic integration::

    from sanic import Sanic
    from nitro.metrics import metrics_middleware, sanic_metrics

    app = Sanic("MyApp")
    registry = metrics_middleware(app)
    sanic_metrics(app, registry)
    # GET /metrics → Prometheus text format

Decorators::

    from nitro.metrics import Histogram, timed

    duration = Histogram("handler_seconds", "Handler duration")

    @timed(duration, handler="index")
    async def index(request):
        ...
"""

from .base import (
    Counter,
    DEFAULT_BUCKETS,
    Gauge,
    Histogram,
    Metric,
    MetricSample,
    MetricType,
    Summary,
)
from .decorators import counted, timed
from .export import sanic_metrics, to_prometheus
from .middleware import metrics_middleware
from .registry import MetricsRegistry

__all__ = [
    # Metric types
    "Counter",
    "Gauge",
    "Histogram",
    "Summary",
    "Metric",
    "MetricSample",
    "MetricType",
    "DEFAULT_BUCKETS",
    # Registry
    "MetricsRegistry",
    # Decorators
    "timed",
    "counted",
    # Middleware
    "metrics_middleware",
    # Export
    "to_prometheus",
    "sanic_metrics",
]
