"""
Export metrics in Prometheus text exposition format and JSON.

Provides a Sanic route handler for ``/metrics``.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from .base import MetricSample, MetricType
from .registry import MetricsRegistry


def to_prometheus(registry: MetricsRegistry) -> str:
    """Render all metrics in Prometheus text exposition format.

    Example::

        from nitro.metrics import MetricsRegistry, to_prometheus

        registry = MetricsRegistry()
        counter = registry.counter("requests_total", "Total requests")
        counter.inc(10)
        print(to_prometheus(registry))
    """
    lines = []
    seen_names = set()

    for metric in registry._metrics.values():
        base_name = metric.name
        if base_name not in seen_names:
            seen_names.add(base_name)
            lines.append(f"# HELP {base_name} {metric.description}")
            lines.append(f"# TYPE {base_name} {metric.metric_type.value}")

        for sample in metric.collect():
            label_str = ""
            if sample.labels:
                parts = [f'{k}="{v}"' for k, v in sample.labels.items()]
                label_str = "{" + ",".join(parts) + "}"
            lines.append(f"{sample.name}{label_str} {_format_value(sample.value)}")

    return "\n".join(lines) + "\n"


def _format_value(v: float) -> str:
    """Format a metric value for Prometheus output."""
    if math.isinf(v):
        return "+Inf" if v > 0 else "-Inf"
    if math.isnan(v):
        return "NaN"
    if v == int(v):
        return str(int(v))
    return str(v)


def sanic_metrics(
    app: Any,
    registry: MetricsRegistry,
    *,
    path: str = "/metrics",
    content_type: str = "text/plain; version=0.0.4; charset=utf-8",
) -> None:
    """Register a ``/metrics`` endpoint on a Sanic app.

    Serves metrics in Prometheus text exposition format.

    Args:
        app: Sanic application instance.
        registry: The metrics registry to expose.
        path: URL path for the endpoint (default ``/metrics``).
        content_type: Response content type.

    Example::

        from sanic import Sanic
        from nitro.metrics import MetricsRegistry, metrics_middleware, sanic_metrics

        app = Sanic("MyApp")
        registry = metrics_middleware(app)
        sanic_metrics(app, registry)
        # GET /metrics → Prometheus text format
    """
    from sanic.response import text as sanic_text

    @app.get(path)
    async def _metrics_endpoint(request: Any) -> Any:
        body = to_prometheus(registry)
        return sanic_text(body, content_type=content_type)
