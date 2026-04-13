"""
Tests for nitro.middleware — pipeline, CORS, security, logging, timing.
"""

import logging
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from nitro.middleware import (
    CORSMiddleware,
    LoggingMiddleware,
    MiddlewareContext,
    MiddlewareInterface,
    Pipeline,
    SecurityMiddleware,
    TimingMiddleware,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_request(method="GET", path="/test", headers=None):
    """Create a minimal request-like object."""
    req = SimpleNamespace()
    req.method = method
    req.path = path
    req.headers = headers or {}
    return req


def _fake_request_dict(method="GET", path="/test", headers=None):
    """Request as a plain dict (for CORS header extraction fallback)."""
    return {"method": method, "path": path, "headers": headers or {}}


class _CounterMiddleware(MiddlewareInterface):
    """Middleware that counts calls for testing pipeline ordering."""

    def __init__(self, name: str, log: list):
        self.name = name
        self.log = log

    def before_request(self, ctx):
        self.log.append(f"before:{self.name}")
        return ctx

    def after_response(self, ctx):
        self.log.append(f"after:{self.name}")
        return ctx


class _AbortMiddleware(MiddlewareInterface):
    """Middleware that aborts the request."""

    def before_request(self, ctx):
        ctx.should_abort = True
        ctx.abort_status = 429
        ctx.abort_body = "Too many requests"
        return ctx


# ===========================================================================
# MiddlewareContext
# ===========================================================================


class TestMiddlewareContext:
    def test_defaults(self):
        ctx = MiddlewareContext(request=None)
        assert ctx.method == ""
        assert ctx.path == ""
        assert ctx.headers == {}
        assert ctx.state == {}
        assert ctx.should_abort is False
        assert ctx.abort_status == 403
        assert ctx.abort_body is None

    def test_mutable_state(self):
        ctx = MiddlewareContext(request=None)
        ctx.state["key"] = "value"
        ctx.headers["X-Custom"] = "yes"
        assert ctx.state["key"] == "value"
        assert ctx.headers["X-Custom"] == "yes"


# ===========================================================================
# Pipeline
# ===========================================================================


class TestPipeline:
    def test_empty_pipeline(self):
        pipeline = Pipeline()
        req = _fake_request()
        ctx = pipeline.before(req)
        assert ctx.method == "GET"
        assert ctx.path == "/test"
        ctx = pipeline.after(ctx)
        assert ctx.headers == {}

    def test_before_order_is_insertion_order(self):
        log = []
        pipeline = Pipeline(
            _CounterMiddleware("A", log),
            _CounterMiddleware("B", log),
            _CounterMiddleware("C", log),
        )
        pipeline.before(_fake_request())
        assert log == ["before:A", "before:B", "before:C"]

    def test_after_order_is_reversed(self):
        log = []
        pipeline = Pipeline(
            _CounterMiddleware("A", log),
            _CounterMiddleware("B", log),
            _CounterMiddleware("C", log),
        )
        ctx = pipeline.before(_fake_request())
        log.clear()
        pipeline.after(ctx)
        assert log == ["after:C", "after:B", "after:A"]

    def test_abort_stops_chain(self):
        log = []
        pipeline = Pipeline(
            _CounterMiddleware("A", log),
            _AbortMiddleware(),
            _CounterMiddleware("B", log),
        )
        ctx = pipeline.before(_fake_request())
        assert ctx.should_abort is True
        assert ctx.abort_status == 429
        # B's before_request should NOT have been called
        assert "before:B" not in log
        assert "before:A" in log

    def test_add_method(self):
        log = []
        pipeline = Pipeline()
        pipeline.add(_CounterMiddleware("X", log))
        assert len(pipeline) == 1
        pipeline.before(_fake_request())
        assert log == ["before:X"]

    def test_add_returns_self(self):
        pipeline = Pipeline()
        result = pipeline.add(_CounterMiddleware("X", []))
        assert result is pipeline

    def test_method_extraction_from_request(self):
        pipeline = Pipeline()
        req = _fake_request(method="POST", path="/submit")
        ctx = pipeline.before(req)
        assert ctx.method == "POST"
        assert ctx.path == "/submit"

    def test_explicit_method_overrides_request(self):
        pipeline = Pipeline()
        req = _fake_request(method="GET", path="/old")
        ctx = pipeline.before(req, method="PUT", path="/new")
        assert ctx.method == "PUT"
        assert ctx.path == "/new"

    def test_len(self):
        assert len(Pipeline()) == 0
        assert len(Pipeline(_CounterMiddleware("A", []))) == 1

    def test_repr(self):
        pipeline = Pipeline(
            CORSMiddleware(),
            SecurityMiddleware(),
        )
        r = repr(pipeline)
        assert "CORSMiddleware" in r
        assert "SecurityMiddleware" in r


# ===========================================================================
# CORSMiddleware
# ===========================================================================


class TestCORSMiddleware:
    def test_wildcard_origin(self):
        cors = CORSMiddleware(allow_origins=["*"])
        req = _fake_request(headers={"origin": "https://example.com"})
        ctx = Pipeline(cors).before(req)
        assert ctx.headers["Access-Control-Allow-Origin"] == "*"

    def test_specific_origin_allowed(self):
        cors = CORSMiddleware(allow_origins=["https://app.example.com"])
        req = _fake_request(headers={"origin": "https://app.example.com"})
        ctx = Pipeline(cors).before(req)
        assert ctx.headers["Access-Control-Allow-Origin"] == "https://app.example.com"

    def test_specific_origin_denied(self):
        cors = CORSMiddleware(allow_origins=["https://app.example.com"])
        req = _fake_request(headers={"origin": "https://evil.com"})
        ctx = Pipeline(cors).before(req)
        assert "Access-Control-Allow-Origin" not in ctx.headers

    def test_no_origin_header(self):
        cors = CORSMiddleware()
        req = _fake_request()
        ctx = Pipeline(cors).before(req)
        # No origin → no CORS headers
        assert "Access-Control-Allow-Origin" not in ctx.headers

    def test_credentials_reflect_origin(self):
        cors = CORSMiddleware(
            allow_origins=["https://app.example.com"],
            allow_credentials=True,
        )
        req = _fake_request(headers={"origin": "https://app.example.com"})
        ctx = Pipeline(cors).before(req)
        assert ctx.headers["Access-Control-Allow-Origin"] == "https://app.example.com"
        assert ctx.headers["Access-Control-Allow-Credentials"] == "true"

    def test_credentials_with_wildcard_reflects_origin(self):
        cors = CORSMiddleware(allow_origins=["*"], allow_credentials=True)
        req = _fake_request(headers={"origin": "https://any.com"})
        ctx = Pipeline(cors).before(req)
        # Must reflect origin, not "*", when credentials enabled
        assert ctx.headers["Access-Control-Allow-Origin"] == "https://any.com"

    def test_expose_headers(self):
        cors = CORSMiddleware(expose_headers=["X-Request-Id", "X-Total-Count"])
        req = _fake_request(headers={"origin": "https://example.com"})
        ctx = Pipeline(cors).before(req)
        assert "X-Request-Id" in ctx.headers["Access-Control-Expose-Headers"]

    def test_preflight_options(self):
        cors = CORSMiddleware(max_age=3600)
        req = _fake_request(method="OPTIONS", headers={"origin": "https://example.com"})
        ctx = Pipeline(cors).before(req)
        assert ctx.should_abort is True
        assert ctx.abort_status == 204
        assert "Access-Control-Allow-Methods" in ctx.headers
        assert ctx.headers["Access-Control-Max-Age"] == "3600"

    def test_preflight_no_origin_no_abort(self):
        cors = CORSMiddleware()
        req = _fake_request(method="OPTIONS")
        ctx = Pipeline(cors).before(req)
        assert ctx.should_abort is False

    def test_dict_request_origin_extraction(self):
        cors = CORSMiddleware()
        req = _fake_request_dict(headers={"origin": "https://dict.com"})
        ctx = Pipeline(cors).before(req, method="GET", path="/")
        assert ctx.headers["Access-Control-Allow-Origin"] == "*"


# ===========================================================================
# SecurityMiddleware
# ===========================================================================


class TestSecurityMiddleware:
    def test_default_headers(self):
        sec = SecurityMiddleware()
        ctx = MiddlewareContext(request=None)
        ctx = sec.after_response(ctx)

        assert ctx.headers["X-Frame-Options"] == "DENY"
        assert ctx.headers["X-Content-Type-Options"] == "nosniff"
        assert ctx.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert ctx.headers["X-XSS-Protection"] == "0"
        # Not set by default:
        assert "Content-Security-Policy" not in ctx.headers
        assert "Strict-Transport-Security" not in ctx.headers
        assert "Permissions-Policy" not in ctx.headers

    def test_custom_csp(self):
        sec = SecurityMiddleware(content_security_policy="default-src 'self'")
        ctx = sec.after_response(MiddlewareContext(request=None))
        assert ctx.headers["Content-Security-Policy"] == "default-src 'self'"

    def test_hsts(self):
        sec = SecurityMiddleware(strict_transport_security="max-age=31536000")
        ctx = sec.after_response(MiddlewareContext(request=None))
        assert ctx.headers["Strict-Transport-Security"] == "max-age=31536000"

    def test_disable_header_with_none(self):
        sec = SecurityMiddleware(x_frame_options=None, x_xss_protection=None)
        ctx = sec.after_response(MiddlewareContext(request=None))
        assert "X-Frame-Options" not in ctx.headers
        assert "X-XSS-Protection" not in ctx.headers

    def test_does_not_overwrite_existing(self):
        sec = SecurityMiddleware()
        ctx = MiddlewareContext(request=None)
        ctx.headers["X-Frame-Options"] = "SAMEORIGIN"  # Set by handler
        ctx = sec.after_response(ctx)
        assert ctx.headers["X-Frame-Options"] == "SAMEORIGIN"  # Preserved


# ===========================================================================
# LoggingMiddleware
# ===========================================================================


class TestLoggingMiddleware:
    def test_logs_request(self, caplog):
        mw = LoggingMiddleware(level=logging.INFO)
        pipeline = Pipeline(mw)

        with caplog.at_level(logging.INFO, logger="nitro.middleware.request"):
            ctx = pipeline.before(_fake_request(method="POST", path="/api/data"))
            pipeline.after(ctx)

        assert any("POST /api/data" in record.message for record in caplog.records)

    def test_slow_request_warning(self, caplog):
        mw = LoggingMiddleware(slow_threshold=0.0)  # Everything is "slow"
        pipeline = Pipeline(mw)

        with caplog.at_level(logging.DEBUG, logger="nitro.middleware.request"):
            ctx = pipeline.before(_fake_request())
            pipeline.after(ctx)

        slow_records = [r for r in caplog.records if "[SLOW]" in r.message]
        assert len(slow_records) >= 1
        assert slow_records[0].levelno == logging.WARNING

    def test_no_slow_when_threshold_none(self, caplog):
        mw = LoggingMiddleware(slow_threshold=None)
        pipeline = Pipeline(mw)

        with caplog.at_level(logging.DEBUG, logger="nitro.middleware.request"):
            ctx = pipeline.before(_fake_request())
            pipeline.after(ctx)

        assert not any("[SLOW]" in record.message for record in caplog.records)

    def test_custom_logger_name(self, caplog):
        mw = LoggingMiddleware(logger_name="custom.logger")
        pipeline = Pipeline(mw)

        with caplog.at_level(logging.INFO, logger="custom.logger"):
            ctx = pipeline.before(_fake_request())
            pipeline.after(ctx)

        assert any(record.name == "custom.logger" for record in caplog.records)


# ===========================================================================
# TimingMiddleware
# ===========================================================================


class TestTimingMiddleware:
    def test_adds_server_timing_header(self):
        mw = TimingMiddleware()
        pipeline = Pipeline(mw)
        ctx = pipeline.before(_fake_request())
        ctx = pipeline.after(ctx)

        assert "Server-Timing" in ctx.headers
        assert "total;dur=" in ctx.headers["Server-Timing"]

    def test_duration_in_state(self):
        mw = TimingMiddleware()
        pipeline = Pipeline(mw)
        ctx = pipeline.before(_fake_request())
        ctx = pipeline.after(ctx)

        assert "duration_ms" in ctx.state
        assert isinstance(ctx.state["duration_ms"], float)
        assert ctx.state["duration_ms"] >= 0

    def test_slow_detection(self):
        mw = TimingMiddleware(slow_threshold=0.0)
        pipeline = Pipeline(mw)
        ctx = pipeline.before(_fake_request())
        ctx = pipeline.after(ctx)
        assert ctx.state.get("is_slow") is True

    def test_not_slow_below_threshold(self):
        mw = TimingMiddleware(slow_threshold=999.0)
        pipeline = Pipeline(mw)
        ctx = pipeline.before(_fake_request())
        ctx = pipeline.after(ctx)
        assert ctx.state.get("is_slow") is False

    def test_no_slow_flag_when_threshold_none(self):
        mw = TimingMiddleware(slow_threshold=None)
        pipeline = Pipeline(mw)
        ctx = pipeline.before(_fake_request())
        ctx = pipeline.after(ctx)
        assert "is_slow" not in ctx.state

    def test_custom_header_name(self):
        mw = TimingMiddleware(header_name="X-Response-Time")
        pipeline = Pipeline(mw)
        ctx = pipeline.before(_fake_request())
        ctx = pipeline.after(ctx)
        assert "X-Response-Time" in ctx.headers
        assert "Server-Timing" not in ctx.headers

    def test_no_crash_without_before(self):
        """after_response should handle missing start time gracefully."""
        mw = TimingMiddleware()
        ctx = MiddlewareContext(request=None)
        ctx = mw.after_response(ctx)
        assert "duration_ms" not in ctx.state


# ===========================================================================
# Integration — full pipeline
# ===========================================================================


class TestFullPipeline:
    def test_cors_plus_security_plus_timing(self):
        pipeline = Pipeline(
            CORSMiddleware(allow_origins=["https://app.com"]),
            SecurityMiddleware(x_frame_options="SAMEORIGIN"),
            TimingMiddleware(),
        )
        req = _fake_request(headers={"origin": "https://app.com"})
        ctx = pipeline.before(req)
        ctx = pipeline.after(ctx)

        # CORS
        assert ctx.headers["Access-Control-Allow-Origin"] == "https://app.com"
        # Security
        assert ctx.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert ctx.headers["X-Content-Type-Options"] == "nosniff"
        # Timing
        assert "Server-Timing" in ctx.headers
        assert "duration_ms" in ctx.state

    def test_preflight_aborts_and_security_still_applies(self):
        pipeline = Pipeline(
            CORSMiddleware(),
            SecurityMiddleware(),
            TimingMiddleware(),
        )
        req = _fake_request(method="OPTIONS", headers={"origin": "https://example.com"})
        ctx = pipeline.before(req)
        assert ctx.should_abort is True

        # After still runs for all middleware (onion model)
        ctx = pipeline.after(ctx)
        assert "X-Frame-Options" in ctx.headers

    def test_logging_sees_timing_data(self, caplog):
        pipeline = Pipeline(
            TimingMiddleware(),
            LoggingMiddleware(level=logging.INFO),
        )
        with caplog.at_level(logging.INFO, logger="nitro.middleware.request"):
            ctx = pipeline.before(_fake_request())
            ctx = pipeline.after(ctx)

        # Both middleware ran successfully
        assert "duration_ms" in ctx.state
        assert len(caplog.records) >= 1
