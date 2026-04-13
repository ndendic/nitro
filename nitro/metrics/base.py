"""
Core metric types — Counter, Gauge, Histogram, Summary.

All metric types are thread-safe via threading locks.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple


class MetricType(str, Enum):
    """Classification of a metric."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricSample:
    """A single data point from a metric.

    Attributes:
        name: Metric name (may include suffix like ``_total``, ``_bucket``).
        labels: Label key-value pairs.
        value: Numeric value.
        timestamp: Optional epoch timestamp in seconds.
    """

    name: str
    labels: Dict[str, str]
    value: float
    timestamp: Optional[float] = None


class Metric:
    """Base class for all metric types.

    Args:
        name: Metric name (should follow ``snake_case`` convention).
        description: Human-readable description.
        labels: Default label names for this metric.
    """

    metric_type: MetricType = MetricType.COUNTER  # overridden by subclasses

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Sequence[str] = (),
    ) -> None:
        self.name = name
        self.description = description
        self.label_names: Tuple[str, ...] = tuple(labels)
        self._lock = threading.Lock()

    def collect(self) -> List[MetricSample]:
        """Return current samples. Subclasses must implement."""
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """JSON-serialisable representation."""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "description": self.description,
            "samples": [
                {"name": s.name, "labels": s.labels, "value": s.value}
                for s in self.collect()
            ],
        }


class Counter(Metric):
    """Monotonically increasing counter.

    Use for: request counts, errors, bytes sent.

    Example::

        from nitro.metrics import Counter

        requests = Counter("http_requests_total", "Total HTTP requests")
        requests.inc()
        requests.inc(5)
        print(requests.value)  # 6.0
    """

    metric_type = MetricType.COUNTER

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Sequence[str] = (),
    ) -> None:
        super().__init__(name, description, labels)
        self._values: Dict[Tuple[str, ...], float] = {}

    def inc(self, amount: float = 1.0, **label_values: str) -> None:
        """Increment the counter.

        Args:
            amount: Value to add (must be >= 0).
            **label_values: Label key-value pairs.

        Raises:
            ValueError: If amount is negative.
        """
        if amount < 0:
            raise ValueError("Counter increment must be >= 0")
        key = self._label_key(label_values)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + amount

    @property
    def value(self) -> float:
        """Current value for the default (unlabelled) instance."""
        with self._lock:
            return self._values.get((), 0.0)

    def get(self, **label_values: str) -> float:
        """Get value for specific label combination."""
        key = self._label_key(label_values)
        with self._lock:
            return self._values.get(key, 0.0)

    def reset(self) -> None:
        """Reset all values to zero."""
        with self._lock:
            self._values.clear()

    def collect(self) -> List[MetricSample]:
        with self._lock:
            samples = []
            for key, val in self._values.items():
                labels = dict(zip(self.label_names, key))
                samples.append(MetricSample(
                    name=f"{self.name}_total", labels=labels, value=val,
                ))
            if not self._values:
                samples.append(MetricSample(
                    name=f"{self.name}_total", labels={}, value=0.0,
                ))
            return samples

    def _label_key(self, label_values: Dict[str, str]) -> Tuple[str, ...]:
        if not label_values:
            return ()
        return tuple(label_values.get(k, "") for k in self.label_names)


class Gauge(Metric):
    """Value that can go up and down.

    Use for: temperature, queue size, active connections.

    Example::

        from nitro.metrics import Gauge

        connections = Gauge("active_connections", "Active connections")
        connections.set(42)
        connections.inc(3)
        connections.dec(1)
        print(connections.value)  # 44.0
    """

    metric_type = MetricType.GAUGE

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Sequence[str] = (),
    ) -> None:
        super().__init__(name, description, labels)
        self._values: Dict[Tuple[str, ...], float] = {}

    def set(self, value: float, **label_values: str) -> None:
        """Set gauge to a specific value."""
        key = self._label_key(label_values)
        with self._lock:
            self._values[key] = value

    def inc(self, amount: float = 1.0, **label_values: str) -> None:
        """Increment the gauge."""
        key = self._label_key(label_values)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + amount

    def dec(self, amount: float = 1.0, **label_values: str) -> None:
        """Decrement the gauge."""
        key = self._label_key(label_values)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) - amount

    @property
    def value(self) -> float:
        """Current value for the default (unlabelled) instance."""
        with self._lock:
            return self._values.get((), 0.0)

    def get(self, **label_values: str) -> float:
        """Get value for specific label combination."""
        key = self._label_key(label_values)
        with self._lock:
            return self._values.get(key, 0.0)

    def set_to_current_time(self, **label_values: str) -> None:
        """Set gauge to the current Unix epoch time."""
        self.set(time.time(), **label_values)

    def reset(self) -> None:
        """Reset all values to zero."""
        with self._lock:
            self._values.clear()

    def collect(self) -> List[MetricSample]:
        with self._lock:
            samples = []
            for key, val in self._values.items():
                labels = dict(zip(self.label_names, key))
                samples.append(MetricSample(
                    name=self.name, labels=labels, value=val,
                ))
            if not self._values:
                samples.append(MetricSample(
                    name=self.name, labels={}, value=0.0,
                ))
            return samples

    def _label_key(self, label_values: Dict[str, str]) -> Tuple[str, ...]:
        if not label_values:
            return ()
        return tuple(label_values.get(k, "") for k in self.label_names)


# Default Prometheus-style histogram buckets
DEFAULT_BUCKETS: Tuple[float, ...] = (
    0.005, 0.01, 0.025, 0.05, 0.075,
    0.1, 0.25, 0.5, 0.75, 1.0,
    2.5, 5.0, 7.5, 10.0, float("inf"),
)


class Histogram(Metric):
    """Samples observations and counts them in configurable buckets.

    Use for: request durations, response sizes.

    Example::

        from nitro.metrics import Histogram

        duration = Histogram("request_duration_seconds", "Request duration")
        duration.observe(0.25)
        duration.observe(1.3)
        print(duration.count)   # 2
        print(duration.sum)     # 1.55
    """

    metric_type = MetricType.HISTOGRAM

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Sequence[str] = (),
        buckets: Sequence[float] = DEFAULT_BUCKETS,
    ) -> None:
        super().__init__(name, description, labels)
        self._buckets = tuple(sorted(set(buckets)))
        if self._buckets[-1] != float("inf"):
            self._buckets = self._buckets + (float("inf"),)
        # Per-label-key storage
        self._bucket_counts: Dict[Tuple[str, ...], List[int]] = {}
        self._sums: Dict[Tuple[str, ...], float] = {}
        self._counts: Dict[Tuple[str, ...], int] = {}

    def observe(self, value: float, **label_values: str) -> None:
        """Record an observation.

        Args:
            value: The observed value.
            **label_values: Label key-value pairs.
        """
        key = self._label_key(label_values)
        with self._lock:
            if key not in self._bucket_counts:
                self._bucket_counts[key] = [0] * len(self._buckets)
                self._sums[key] = 0.0
                self._counts[key] = 0
            for i, bound in enumerate(self._buckets):
                if value <= bound:
                    self._bucket_counts[key][i] += 1
                    break
            self._sums[key] += value
            self._counts[key] += 1

    @property
    def count(self) -> int:
        """Total observation count for the default instance."""
        with self._lock:
            return self._counts.get((), 0)

    @property
    def sum(self) -> float:
        """Sum of all observations for the default instance."""
        with self._lock:
            return self._sums.get((), 0.0)

    @property
    def buckets(self) -> Tuple[float, ...]:
        """Configured bucket boundaries."""
        return self._buckets

    def get_bucket_counts(self, **label_values: str) -> List[Tuple[float, int]]:
        """Get cumulative bucket counts for a label combination."""
        key = self._label_key(label_values)
        with self._lock:
            counts = self._bucket_counts.get(key, [0] * len(self._buckets))
            cumulative = []
            running = 0
            for i, bound in enumerate(self._buckets):
                running += counts[i]
                cumulative.append((bound, running))
            return cumulative

    def reset(self) -> None:
        """Reset all observations."""
        with self._lock:
            self._bucket_counts.clear()
            self._sums.clear()
            self._counts.clear()

    def collect(self) -> List[MetricSample]:
        with self._lock:
            samples = []
            keys = list(self._counts.keys()) or [()]
            for key in keys:
                labels = dict(zip(self.label_names, key))
                counts = self._bucket_counts.get(key, [0] * len(self._buckets))
                running = 0
                for i, bound in enumerate(self._buckets):
                    running += counts[i]
                    le_label = "+Inf" if math.isinf(bound) else str(bound)
                    samples.append(MetricSample(
                        name=f"{self.name}_bucket",
                        labels={**labels, "le": le_label},
                        value=float(running),
                    ))
                samples.append(MetricSample(
                    name=f"{self.name}_count",
                    labels=labels,
                    value=float(self._counts.get(key, 0)),
                ))
                samples.append(MetricSample(
                    name=f"{self.name}_sum",
                    labels=labels,
                    value=self._sums.get(key, 0.0),
                ))
            return samples

    def _label_key(self, label_values: Dict[str, str]) -> Tuple[str, ...]:
        if not label_values:
            return ()
        return tuple(label_values.get(k, "") for k in self.label_names)


class Summary(Metric):
    """Tracks observations and calculates quantiles over a sliding window.

    Use for: request latency percentiles (p50, p90, p99).

    Note: This is a simple implementation that stores all observations in the
    current window. For high-throughput production use, consider the Histogram
    type which uses fixed bucket boundaries.

    Example::

        from nitro.metrics import Summary

        latency = Summary(
            "request_latency_seconds",
            "Request latency",
            quantiles=(0.5, 0.9, 0.99),
            max_age_seconds=600,
        )
        for val in [0.1, 0.2, 0.3, 0.4, 0.5]:
            latency.observe(val)
        print(latency.count)  # 5
    """

    metric_type = MetricType.SUMMARY

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Sequence[str] = (),
        quantiles: Sequence[float] = (0.5, 0.9, 0.99),
        max_age_seconds: float = 600.0,
    ) -> None:
        super().__init__(name, description, labels)
        self._quantiles = tuple(quantiles)
        self._max_age = max_age_seconds
        # Per-label storage: list of (timestamp, value)
        self._observations: Dict[Tuple[str, ...], List[Tuple[float, float]]] = {}
        self._sums: Dict[Tuple[str, ...], float] = {}
        self._counts: Dict[Tuple[str, ...], int] = {}

    def observe(self, value: float, **label_values: str) -> None:
        """Record an observation."""
        key = self._label_key(label_values)
        now = time.time()
        with self._lock:
            if key not in self._observations:
                self._observations[key] = []
                self._sums[key] = 0.0
                self._counts[key] = 0
            self._observations[key].append((now, value))
            self._sums[key] += value
            self._counts[key] += 1

    @property
    def count(self) -> int:
        with self._lock:
            return self._counts.get((), 0)

    @property
    def sum(self) -> float:
        with self._lock:
            return self._sums.get((), 0.0)

    def get_quantiles(self, **label_values: str) -> List[Tuple[float, float]]:
        """Calculate current quantile values.

        Returns:
            List of (quantile, value) tuples.
        """
        key = self._label_key(label_values)
        now = time.time()
        with self._lock:
            obs = self._observations.get(key, [])
            # Filter to window
            values = sorted(
                v for t, v in obs if now - t <= self._max_age
            )
            if not values:
                return [(q, 0.0) for q in self._quantiles]
            result = []
            for q in self._quantiles:
                idx = max(0, min(int(q * len(values)), len(values) - 1))
                result.append((q, values[idx]))
            return result

    def _prune(self, key: Tuple[str, ...]) -> None:
        """Remove expired observations (call inside lock)."""
        now = time.time()
        self._observations[key] = [
            (t, v) for t, v in self._observations.get(key, [])
            if now - t <= self._max_age
        ]

    def reset(self) -> None:
        """Reset all observations."""
        with self._lock:
            self._observations.clear()
            self._sums.clear()
            self._counts.clear()

    def collect(self) -> List[MetricSample]:
        with self._lock:
            samples = []
            keys = list(self._counts.keys()) or [()]
            for key in keys:
                labels = dict(zip(self.label_names, key))
                now = time.time()
                obs = self._observations.get(key, [])
                values = sorted(
                    v for t, v in obs if now - t <= self._max_age
                )
                for q in self._quantiles:
                    if values:
                        idx = max(0, min(int(q * len(values)), len(values) - 1))
                        val = values[idx]
                    else:
                        val = 0.0
                    samples.append(MetricSample(
                        name=self.name,
                        labels={**labels, "quantile": str(q)},
                        value=val,
                    ))
                samples.append(MetricSample(
                    name=f"{self.name}_count",
                    labels=labels,
                    value=float(self._counts.get(key, 0)),
                ))
                samples.append(MetricSample(
                    name=f"{self.name}_sum",
                    labels=labels,
                    value=self._sums.get(key, 0.0),
                ))
            return samples

    def _label_key(self, label_values: Dict[str, str]) -> Tuple[str, ...]:
        if not label_values:
            return ()
        return tuple(label_values.get(k, "") for k in self.label_names)
