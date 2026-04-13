"""Comprehensive tests for nitro.metrics module.

Covers: Counter, Gauge, Histogram, Summary, MetricsRegistry,
decorators (timed, counted), Prometheus export, and middleware.
"""

import asyncio
import math
import threading
import time

import pytest

from nitro.metrics import (
    Counter,
    DEFAULT_BUCKETS,
    Gauge,
    Histogram,
    Metric,
    MetricSample,
    MetricType,
    MetricsRegistry,
    Summary,
    counted,
    timed,
    to_prometheus,
)


# ---------------------------------------------------------------------------
# MetricType enum
# ---------------------------------------------------------------------------

class TestMetricType:
    def test_values(self):
        assert MetricType.COUNTER == "counter"
        assert MetricType.GAUGE == "gauge"
        assert MetricType.HISTOGRAM == "histogram"
        assert MetricType.SUMMARY == "summary"

    def test_all_types_exist(self):
        assert len(MetricType) == 4


# ---------------------------------------------------------------------------
# MetricSample
# ---------------------------------------------------------------------------

class TestMetricSample:
    def test_creation(self):
        s = MetricSample(name="test", labels={"a": "1"}, value=42.0)
        assert s.name == "test"
        assert s.labels == {"a": "1"}
        assert s.value == 42.0
        assert s.timestamp is None

    def test_with_timestamp(self):
        s = MetricSample(name="test", labels={}, value=1.0, timestamp=1234567890.0)
        assert s.timestamp == 1234567890.0


# ---------------------------------------------------------------------------
# Counter
# ---------------------------------------------------------------------------

class TestCounter:
    def test_default_value_is_zero(self):
        c = Counter("test_counter")
        assert c.value == 0.0

    def test_increment_default(self):
        c = Counter("test_counter")
        c.inc()
        assert c.value == 1.0

    def test_increment_by_amount(self):
        c = Counter("test_counter")
        c.inc(5)
        assert c.value == 5.0

    def test_increment_multiple(self):
        c = Counter("test_counter")
        c.inc(2)
        c.inc(3)
        assert c.value == 5.0

    def test_increment_negative_raises(self):
        c = Counter("test_counter")
        with pytest.raises(ValueError, match="must be >= 0"):
            c.inc(-1)

    def test_increment_zero_allowed(self):
        c = Counter("test_counter")
        c.inc(0)
        assert c.value == 0.0

    def test_increment_float(self):
        c = Counter("test_counter")
        c.inc(0.5)
        c.inc(0.3)
        assert abs(c.value - 0.8) < 1e-9

    def test_labels(self):
        c = Counter("requests", labels=["method", "status"])
        c.inc(method="GET", status="200")
        c.inc(method="GET", status="200")
        c.inc(method="POST", status="201")
        assert c.get(method="GET", status="200") == 2.0
        assert c.get(method="POST", status="201") == 1.0
        assert c.get(method="DELETE", status="404") == 0.0

    def test_reset(self):
        c = Counter("test_counter")
        c.inc(10)
        c.reset()
        assert c.value == 0.0

    def test_collect_empty(self):
        c = Counter("test_counter")
        samples = c.collect()
        assert len(samples) == 1
        assert samples[0].name == "test_counter_total"
        assert samples[0].value == 0.0

    def test_collect_with_values(self):
        c = Counter("requests", labels=["method"])
        c.inc(method="GET")
        c.inc(2, method="POST")
        samples = c.collect()
        assert len(samples) == 2
        by_label = {tuple(s.labels.items()): s.value for s in samples}
        assert by_label[(("method", "GET"),)] == 1.0
        assert by_label[(("method", "POST"),)] == 2.0

    def test_to_dict(self):
        c = Counter("test_counter", "A test counter")
        c.inc(5)
        d = c.to_dict()
        assert d["name"] == "test_counter"
        assert d["type"] == "counter"
        assert d["description"] == "A test counter"
        assert len(d["samples"]) == 1
        assert d["samples"][0]["value"] == 5.0

    def test_metric_type(self):
        c = Counter("test")
        assert c.metric_type == MetricType.COUNTER

    def test_thread_safety(self):
        c = Counter("threaded")
        def inc_many():
            for _ in range(1000):
                c.inc()
        threads = [threading.Thread(target=inc_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert c.value == 10000.0


# ---------------------------------------------------------------------------
# Gauge
# ---------------------------------------------------------------------------

class TestGauge:
    def test_default_value_is_zero(self):
        g = Gauge("test_gauge")
        assert g.value == 0.0

    def test_set(self):
        g = Gauge("test_gauge")
        g.set(42)
        assert g.value == 42.0

    def test_set_negative(self):
        g = Gauge("test_gauge")
        g.set(-5)
        assert g.value == -5.0

    def test_inc(self):
        g = Gauge("test_gauge")
        g.inc()
        assert g.value == 1.0

    def test_inc_amount(self):
        g = Gauge("test_gauge")
        g.inc(5)
        assert g.value == 5.0

    def test_dec(self):
        g = Gauge("test_gauge")
        g.set(10)
        g.dec()
        assert g.value == 9.0

    def test_dec_amount(self):
        g = Gauge("test_gauge")
        g.set(10)
        g.dec(3)
        assert g.value == 7.0

    def test_inc_and_dec(self):
        g = Gauge("test_gauge")
        g.inc(5)
        g.dec(2)
        g.inc(1)
        assert g.value == 4.0

    def test_set_to_current_time(self):
        g = Gauge("test_gauge")
        before = time.time()
        g.set_to_current_time()
        after = time.time()
        assert before <= g.value <= after

    def test_labels(self):
        g = Gauge("connections", labels=["host"])
        g.set(10, host="alpha")
        g.set(20, host="beta")
        assert g.get(host="alpha") == 10.0
        assert g.get(host="beta") == 20.0

    def test_reset(self):
        g = Gauge("test_gauge")
        g.set(42)
        g.reset()
        assert g.value == 0.0

    def test_collect_empty(self):
        g = Gauge("test_gauge")
        samples = g.collect()
        assert len(samples) == 1
        assert samples[0].name == "test_gauge"
        assert samples[0].value == 0.0

    def test_collect_with_labels(self):
        g = Gauge("connections", labels=["host"])
        g.set(10, host="a")
        g.set(20, host="b")
        samples = g.collect()
        assert len(samples) == 2

    def test_metric_type(self):
        g = Gauge("test")
        assert g.metric_type == MetricType.GAUGE

    def test_thread_safety(self):
        g = Gauge("threaded")
        g.set(0)
        def inc_many():
            for _ in range(1000):
                g.inc()
        def dec_many():
            for _ in range(1000):
                g.dec()
        threads = (
            [threading.Thread(target=inc_many) for _ in range(5)]
            + [threading.Thread(target=dec_many) for _ in range(5)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert g.value == 0.0


# ---------------------------------------------------------------------------
# Histogram
# ---------------------------------------------------------------------------

class TestHistogram:
    def test_default_buckets(self):
        h = Histogram("test_histogram")
        assert h.buckets == DEFAULT_BUCKETS

    def test_custom_buckets_sorted(self):
        h = Histogram("test", buckets=[1.0, 0.5, 0.1])
        assert h.buckets == (0.1, 0.5, 1.0, float("inf"))

    def test_inf_added_if_missing(self):
        h = Histogram("test", buckets=[1.0, 2.0])
        assert h.buckets[-1] == float("inf")

    def test_inf_not_duplicated(self):
        h = Histogram("test", buckets=[1.0, float("inf")])
        assert h.buckets.count(float("inf")) == 1

    def test_observe(self):
        h = Histogram("test")
        h.observe(0.5)
        assert h.count == 1
        assert h.sum == 0.5

    def test_observe_multiple(self):
        h = Histogram("test")
        h.observe(0.1)
        h.observe(0.2)
        h.observe(0.3)
        assert h.count == 3
        assert abs(h.sum - 0.6) < 1e-9

    def test_bucket_counts(self):
        h = Histogram("test", buckets=[0.1, 0.5, 1.0])
        h.observe(0.05)   # bucket 0.1
        h.observe(0.3)    # bucket 0.5
        h.observe(0.8)    # bucket 1.0
        h.observe(5.0)    # bucket +Inf
        counts = h.get_bucket_counts()
        # cumulative: 0.1→1, 0.5→2, 1.0→3, +Inf→4
        assert counts[0] == (0.1, 1)
        assert counts[1] == (0.5, 2)
        assert counts[2] == (1.0, 3)
        assert counts[3] == (float("inf"), 4)

    def test_observe_exact_boundary(self):
        h = Histogram("test", buckets=[0.1, 0.5, 1.0])
        h.observe(0.5)
        counts = h.get_bucket_counts()
        assert counts[0] == (0.1, 0)   # 0.5 > 0.1
        assert counts[1] == (0.5, 1)   # 0.5 <= 0.5
        assert counts[2] == (1.0, 1)   # cumulative

    def test_observe_zero(self):
        h = Histogram("test", buckets=[0.1, 0.5])
        h.observe(0.0)
        assert h.count == 1
        counts = h.get_bucket_counts()
        assert counts[0] == (0.1, 1)

    def test_observe_negative(self):
        h = Histogram("test", buckets=[0.1, 0.5])
        h.observe(-1.0)
        assert h.count == 1
        # Negative value is less than all buckets
        counts = h.get_bucket_counts()
        assert counts[0] == (0.1, 1)

    def test_labels(self):
        h = Histogram("duration", labels=["method"], buckets=[0.1, 0.5, 1.0])
        h.observe(0.05, method="GET")
        h.observe(0.8, method="POST")
        get_counts = h.get_bucket_counts(method="GET")
        post_counts = h.get_bucket_counts(method="POST")
        assert get_counts[0] == (0.1, 1)
        assert post_counts[2] == (1.0, 1)

    def test_reset(self):
        h = Histogram("test")
        h.observe(1.0)
        h.observe(2.0)
        h.reset()
        assert h.count == 0
        assert h.sum == 0.0

    def test_collect(self):
        h = Histogram("test", buckets=[0.5, 1.0])
        h.observe(0.3)
        samples = h.collect()
        # 3 buckets (0.5, 1.0, +Inf) + _count + _sum = 5
        assert len(samples) == 5
        names = [s.name for s in samples]
        assert "test_bucket" in names
        assert "test_count" in names
        assert "test_sum" in names

    def test_metric_type(self):
        h = Histogram("test")
        assert h.metric_type == MetricType.HISTOGRAM

    def test_thread_safety(self):
        h = Histogram("threaded", buckets=[1.0, 5.0, 10.0])
        def observe_many():
            for i in range(100):
                h.observe(i * 0.1)
        threads = [threading.Thread(target=observe_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert h.count == 1000


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class TestSummary:
    def test_observe(self):
        s = Summary("test_summary", quantiles=(0.5, 0.9))
        for v in [0.1, 0.2, 0.3, 0.4, 0.5]:
            s.observe(v)
        assert s.count == 5
        assert abs(s.sum - 1.5) < 1e-9

    def test_quantiles(self):
        s = Summary("test_summary", quantiles=(0.5, 0.9, 0.99))
        for v in range(1, 101):
            s.observe(float(v))
        quantiles = s.get_quantiles()
        # p50 should be around 50, p90 around 90
        assert len(quantiles) == 3
        assert quantiles[0][0] == 0.5
        assert 45 <= quantiles[0][1] <= 55
        assert quantiles[1][0] == 0.9
        assert 85 <= quantiles[1][1] <= 95

    def test_empty_quantiles(self):
        s = Summary("test_summary", quantiles=(0.5,))
        quantiles = s.get_quantiles()
        assert quantiles == [(0.5, 0.0)]

    def test_labels(self):
        s = Summary("latency", labels=["endpoint"], quantiles=(0.5,))
        for v in [0.1, 0.2, 0.3]:
            s.observe(v, endpoint="index")
        for v in [1.0, 2.0, 3.0]:
            s.observe(v, endpoint="api")
        q_index = s.get_quantiles(endpoint="index")
        q_api = s.get_quantiles(endpoint="api")
        assert q_index[0][1] < q_api[0][1]

    def test_reset(self):
        s = Summary("test_summary")
        s.observe(1.0)
        s.reset()
        assert s.count == 0
        assert s.sum == 0.0

    def test_max_age(self):
        s = Summary("test_summary", quantiles=(0.5,), max_age_seconds=0.0)
        s.observe(100.0)
        # With max_age=0, observations expire immediately
        quantiles = s.get_quantiles()
        assert quantiles == [(0.5, 0.0)]

    def test_collect(self):
        s = Summary("test", quantiles=(0.5, 0.99))
        s.observe(1.0)
        samples = s.collect()
        # 2 quantiles + _count + _sum = 4
        assert len(samples) == 4
        names = [sa.name for sa in samples]
        assert "test" in names
        assert "test_count" in names
        assert "test_sum" in names

    def test_metric_type(self):
        s = Summary("test")
        assert s.metric_type == MetricType.SUMMARY


# ---------------------------------------------------------------------------
# MetricsRegistry
# ---------------------------------------------------------------------------

class TestMetricsRegistry:
    def test_create_counter(self):
        r = MetricsRegistry()
        c = r.counter("requests_total", "Total requests")
        assert isinstance(c, Counter)
        assert c.name == "requests_total"

    def test_create_gauge(self):
        r = MetricsRegistry()
        g = r.gauge("connections", "Active connections")
        assert isinstance(g, Gauge)

    def test_create_histogram(self):
        r = MetricsRegistry()
        h = r.histogram("duration", "Duration", buckets=[0.5, 1.0])
        assert isinstance(h, Histogram)

    def test_create_summary(self):
        r = MetricsRegistry()
        s = r.summary("latency", "Latency", quantiles=(0.5,))
        assert isinstance(s, Summary)

    def test_prefix(self):
        r = MetricsRegistry(prefix="myapp")
        c = r.counter("requests_total")
        assert c.name == "myapp_requests_total"

    def test_duplicate_name_raises(self):
        r = MetricsRegistry()
        r.counter("test")
        with pytest.raises(ValueError, match="already registered"):
            r.counter("test")

    def test_get(self):
        r = MetricsRegistry()
        c = r.counter("test")
        assert r.get("test") is c
        assert r.get("nonexistent") is None

    def test_metric_names(self):
        r = MetricsRegistry()
        r.counter("a")
        r.gauge("b")
        r.histogram("c")
        names = r.metric_names
        assert sorted(names) == ["a", "b", "c"]

    def test_unregister(self):
        r = MetricsRegistry()
        r.counter("test")
        assert r.unregister("test") is True
        assert r.get("test") is None
        assert r.unregister("test") is False

    def test_register_external_metric(self):
        r = MetricsRegistry()
        c = Counter("external")
        r.register(c)
        assert r.get("external") is c

    def test_collect(self):
        r = MetricsRegistry()
        c = r.counter("requests")
        c.inc(5)
        g = r.gauge("connections")
        g.set(42)
        samples = r.collect()
        assert len(samples) >= 2
        names = {s.name for s in samples}
        assert "requests_total" in names
        assert "connections" in names

    def test_collect_json(self):
        r = MetricsRegistry()
        c = r.counter("requests", "Total requests")
        c.inc(3)
        json_list = r.collect_json()
        assert len(json_list) == 1
        assert json_list[0]["name"] == "requests"
        assert json_list[0]["type"] == "counter"

    def test_reset_all(self):
        r = MetricsRegistry()
        c = r.counter("requests")
        c.inc(10)
        g = r.gauge("connections")
        g.set(42)
        r.reset_all()
        assert c.value == 0.0
        assert g.value == 0.0


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

class TestTimedDecorator:
    def test_sync_function(self):
        h = Histogram("test_duration", buckets=[0.01, 0.1, 1.0])

        @timed(h)
        def slow():
            time.sleep(0.02)
            return "done"

        result = slow()
        assert result == "done"
        assert h.count == 1
        assert h.sum >= 0.02

    def test_async_function(self):
        h = Histogram("test_duration", buckets=[0.01, 0.1, 1.0])

        @timed(h)
        async def slow():
            await asyncio.sleep(0.02)
            return "async_done"

        result = asyncio.run(slow())
        assert result == "async_done"
        assert h.count == 1
        assert h.sum >= 0.02

    def test_with_labels(self):
        h = Histogram("duration", labels=["handler"], buckets=[1.0])

        @timed(h, handler="index")
        def index():
            return "ok"

        index()
        counts = h.get_bucket_counts(handler="index")
        assert counts[0][1] == 1  # one observation in first bucket

    def test_preserves_function_name(self):
        h = Histogram("test")

        @timed(h)
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    def test_exception_still_records(self):
        h = Histogram("test", buckets=[1.0])

        @timed(h)
        def failing():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            failing()
        assert h.count == 1  # timing recorded even on failure


class TestCountedDecorator:
    def test_sync_function(self):
        c = Counter("calls")

        @counted(c)
        def my_func():
            return "result"

        assert my_func() == "result"
        assert my_func() == "result"
        assert c.value == 2.0

    def test_async_function(self):
        c = Counter("calls")

        @counted(c)
        async def my_func():
            return "async_result"

        result = asyncio.run(my_func())
        assert result == "async_result"
        assert c.value == 1.0

    def test_with_labels(self):
        c = Counter("calls", labels=["handler"])

        @counted(c, handler="index")
        def index():
            pass

        index()
        index()
        assert c.get(handler="index") == 2.0

    def test_preserves_function_name(self):
        c = Counter("test")

        @counted(c)
        def my_function():
            pass

        assert my_function.__name__ == "my_function"


# ---------------------------------------------------------------------------
# Prometheus Export
# ---------------------------------------------------------------------------

class TestPrometheusExport:
    def test_counter_export(self):
        r = MetricsRegistry()
        c = r.counter("http_requests_total", "Total HTTP requests")
        c.inc(42)
        output = to_prometheus(r)
        assert "# HELP http_requests_total Total HTTP requests" in output
        assert "# TYPE http_requests_total counter" in output
        assert "http_requests_total_total 42" in output

    def test_gauge_export(self):
        r = MetricsRegistry()
        g = r.gauge("temperature", "Current temperature")
        g.set(23.5)
        output = to_prometheus(r)
        assert "# TYPE temperature gauge" in output
        assert "temperature 23.5" in output

    def test_histogram_export(self):
        r = MetricsRegistry()
        h = r.histogram("duration", "Duration", buckets=[0.1, 0.5])
        h.observe(0.3)
        output = to_prometheus(r)
        assert "# TYPE duration histogram" in output
        assert 'duration_bucket{le="0.1"}' in output
        assert 'duration_bucket{le="0.5"}' in output
        assert 'duration_bucket{le="+Inf"}' in output
        assert "duration_count" in output
        assert "duration_sum" in output

    def test_labeled_counter_export(self):
        r = MetricsRegistry()
        c = r.counter("requests", "Requests", labels=["method"])
        c.inc(method="GET")
        output = to_prometheus(r)
        assert 'requests_total{method="GET"} 1' in output

    def test_empty_registry(self):
        r = MetricsRegistry()
        output = to_prometheus(r)
        assert output == "\n"

    def test_multiple_metrics(self):
        r = MetricsRegistry()
        r.counter("a", "A metric")
        r.gauge("b", "B metric")
        output = to_prometheus(r)
        assert "# HELP a" in output
        assert "# HELP b" in output


# ---------------------------------------------------------------------------
# Metric base class
# ---------------------------------------------------------------------------

class TestMetricBase:
    def test_collect_not_implemented(self):
        m = Metric("test")
        with pytest.raises(NotImplementedError):
            m.collect()

    def test_attributes(self):
        m = Metric("test_metric", "A description", labels=["a", "b"])
        assert m.name == "test_metric"
        assert m.description == "A description"
        assert m.label_names == ("a", "b")


# ---------------------------------------------------------------------------
# Edge cases and integration
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_counter_many_labels(self):
        c = Counter("test", labels=["a", "b", "c", "d"])
        c.inc(a="1", b="2", c="3", d="4")
        assert c.get(a="1", b="2", c="3", d="4") == 1.0

    def test_gauge_can_go_very_negative(self):
        g = Gauge("test")
        g.set(-1_000_000)
        assert g.value == -1_000_000.0

    def test_histogram_single_bucket(self):
        h = Histogram("test", buckets=[1.0])
        h.observe(0.5)
        h.observe(1.5)
        counts = h.get_bucket_counts()
        assert counts[0] == (1.0, 1)
        assert counts[1] == (float("inf"), 2)

    def test_histogram_large_values(self):
        h = Histogram("test", buckets=[100.0])
        h.observe(1e10)
        assert h.count == 1
        assert h.sum == 1e10

    def test_registry_thread_safety(self):
        r = MetricsRegistry()
        errors = []
        def create_metrics(prefix):
            try:
                for i in range(50):
                    r.counter(f"{prefix}_{i}")
            except ValueError:
                pass  # duplicate names from races are OK
            except Exception as e:
                errors.append(e)
        threads = [
            threading.Thread(target=create_metrics, args=(f"t{t}",))
            for t in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors

    def test_full_pipeline(self):
        """End-to-end: create registry, add metrics, collect, export."""
        reg = MetricsRegistry(prefix="app")
        reqs = reg.counter("requests_total", "Total requests", labels=["method"])
        conns = reg.gauge("connections", "Active connections")
        dur = reg.histogram("duration_seconds", "Duration", buckets=[0.1, 0.5, 1.0])

        reqs.inc(method="GET")
        reqs.inc(method="GET")
        reqs.inc(method="POST")
        conns.set(42)
        dur.observe(0.05)
        dur.observe(0.3)
        dur.observe(0.8)

        # collect_json
        json_data = reg.collect_json()
        assert len(json_data) == 3

        # prometheus
        prom = to_prometheus(reg)
        assert "app_requests_total" in prom
        assert "app_connections" in prom
        assert "app_duration_seconds" in prom

        # reset
        reg.reset_all()
        assert reqs.value == 0.0
        assert conns.value == 0.0
        assert dur.count == 0
