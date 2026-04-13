"""
MetricsRegistry — central coordinator for application metrics.

Register metrics at startup, then collect or query at any time.

Example::

    from nitro.metrics import MetricsRegistry, Counter, Histogram

    registry = MetricsRegistry()
    requests = registry.counter("http_requests_total", "Total requests", labels=["method", "status"])
    duration = registry.histogram("request_duration_seconds", "Request duration")

    requests.inc(method="GET", status="200")
    duration.observe(0.042)

    for metric_dict in registry.collect_json():
        print(metric_dict)
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional, Sequence

from .base import (
    Counter,
    Gauge,
    Histogram,
    Metric,
    MetricSample,
    MetricType,
    Summary,
    DEFAULT_BUCKETS,
)


class MetricsRegistry:
    """Central registry for application metrics.

    Thread-safe. Typically one per application.

    Args:
        prefix: Optional prefix prepended to all metric names.
    """

    def __init__(self, prefix: str = "") -> None:
        self._prefix = prefix
        self._metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()

    def _prefixed(self, name: str) -> str:
        if self._prefix:
            return f"{self._prefix}_{name}"
        return name

    def register(self, metric: Metric) -> Metric:
        """Register an existing metric instance.

        Raises:
            ValueError: If a metric with this name is already registered.
        """
        with self._lock:
            if metric.name in self._metrics:
                raise ValueError(f"Metric '{metric.name}' already registered")
            self._metrics[metric.name] = metric
        return metric

    def unregister(self, name: str) -> bool:
        """Remove a metric by name.

        Returns:
            ``True`` if found and removed, ``False`` otherwise.
        """
        with self._lock:
            return self._metrics.pop(name, None) is not None

    def get(self, name: str) -> Optional[Metric]:
        """Retrieve a metric by name."""
        with self._lock:
            return self._metrics.get(name)

    @property
    def metric_names(self) -> List[str]:
        """Names of all registered metrics."""
        with self._lock:
            return list(self._metrics.keys())

    def counter(
        self,
        name: str,
        description: str = "",
        labels: Sequence[str] = (),
    ) -> Counter:
        """Create and register a :class:`Counter`."""
        full_name = self._prefixed(name)
        c = Counter(full_name, description, labels)
        self.register(c)
        return c

    def gauge(
        self,
        name: str,
        description: str = "",
        labels: Sequence[str] = (),
    ) -> Gauge:
        """Create and register a :class:`Gauge`."""
        full_name = self._prefixed(name)
        g = Gauge(full_name, description, labels)
        self.register(g)
        return g

    def histogram(
        self,
        name: str,
        description: str = "",
        labels: Sequence[str] = (),
        buckets: Sequence[float] = DEFAULT_BUCKETS,
    ) -> Histogram:
        """Create and register a :class:`Histogram`."""
        full_name = self._prefixed(name)
        h = Histogram(full_name, description, labels, buckets)
        self.register(h)
        return h

    def summary(
        self,
        name: str,
        description: str = "",
        labels: Sequence[str] = (),
        quantiles: Sequence[float] = (0.5, 0.9, 0.99),
        max_age_seconds: float = 600.0,
    ) -> Summary:
        """Create and register a :class:`Summary`."""
        full_name = self._prefixed(name)
        s = Summary(full_name, description, labels, quantiles, max_age_seconds)
        self.register(s)
        return s

    def collect(self) -> List[MetricSample]:
        """Collect all samples from all registered metrics."""
        with self._lock:
            metrics = list(self._metrics.values())
        samples = []
        for m in metrics:
            samples.extend(m.collect())
        return samples

    def collect_json(self) -> List[Dict[str, Any]]:
        """Collect all metrics as JSON-serialisable dicts."""
        with self._lock:
            metrics = list(self._metrics.values())
        return [m.to_dict() for m in metrics]

    def reset_all(self) -> None:
        """Reset all registered metrics."""
        with self._lock:
            metrics = list(self._metrics.values())
        for m in metrics:
            m.reset()
