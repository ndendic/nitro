"""Comprehensive tests for the nitro.logging module.

Coverage: RequestContext, correlation-ID propagation, formatters, filters,
middleware, decorators, configure_logging / get_logger, and integration paths.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_record(
    msg: str = "test message",
    name: str = "nitro.test",
    level: int = logging.INFO,
    exc_info=None,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    return record


def _reset_logging_module():
    """Reset the _configured flag so each test starts fresh."""
    import nitro.logging.config as cfg_mod
    cfg_mod._configured = False
    logger = logging.getLogger("nitro")
    logger.handlers.clear()
    logger.propagate = True


# ===========================================================================
# RequestContext
# ===========================================================================

class TestRequestContext:
    def test_create_with_required_fields(self):
        from nitro.logging.context import RequestContext
        ctx = RequestContext(request_id="abc", method="GET", path="/")
        assert ctx.request_id == "abc"
        assert ctx.method == "GET"
        assert ctx.path == "/"

    def test_create_with_all_fields(self):
        from nitro.logging.context import RequestContext
        ctx = RequestContext(
            request_id="xyz",
            method="POST",
            path="/users",
            user_id="u1",
            started_at=1234567890.0,
            extra={"tenant": "acme"},
        )
        assert ctx.user_id == "u1"
        assert ctx.started_at == 1234567890.0
        assert ctx.extra["tenant"] == "acme"

    def test_request_id_is_required(self):
        from nitro.logging.context import RequestContext
        import pydantic
        with pytest.raises((TypeError, pydantic.ValidationError)):
            RequestContext(method="GET", path="/")

    def test_extra_dict_works(self):
        from nitro.logging.context import RequestContext
        ctx = RequestContext(request_id="r1", method="DELETE", path="/items/1")
        ctx.extra["key"] = "value"
        assert ctx.extra["key"] == "value"

    def test_serialization_to_dict(self):
        from nitro.logging.context import RequestContext
        ctx = RequestContext(request_id="r1", method="GET", path="/ping")
        d = ctx.model_dump()
        assert d["request_id"] == "r1"
        assert "method" in d
        assert "path" in d

    def test_user_id_optional(self):
        from nitro.logging.context import RequestContext
        ctx = RequestContext(request_id="r2", method="GET", path="/")
        assert ctx.user_id is None

    def test_started_at_defaults_to_zero(self):
        from nitro.logging.context import RequestContext
        ctx = RequestContext(request_id="r3", method="GET", path="/")
        assert ctx.started_at == 0.0

    def test_extra_defaults_to_empty_dict(self):
        from nitro.logging.context import RequestContext
        ctx = RequestContext(request_id="r4", method="GET", path="/")
        assert ctx.extra == {}


# ===========================================================================
# Correlation ID
# ===========================================================================

class TestCorrelationId:
    def setup_method(self):
        from nitro.logging.context import clear_context
        clear_context()

    def test_default_generates_12_char_hex(self):
        from nitro.logging.context import correlation_id
        cid = correlation_id()
        assert len(cid) == 12
        int(cid, 16)  # raises ValueError if not hex

    def test_set_and_get(self):
        from nitro.logging.context import correlation_id, set_correlation_id
        set_correlation_id("deadbeef1234")
        assert correlation_id() == "deadbeef1234"

    def test_set_stores_value(self):
        from nitro.logging.context import correlation_id, set_correlation_id
        set_correlation_id("cafebabe0000")
        assert correlation_id() == "cafebabe0000"

    def test_clear_context_resets(self):
        from nitro.logging.context import clear_context, correlation_id, set_correlation_id
        set_correlation_id("aaaaaaaaaaaa")
        clear_context()
        cid = correlation_id()
        assert cid != "aaaaaaaaaaaa"

    def test_cleared_id_is_12_chars(self):
        from nitro.logging.context import clear_context, correlation_id
        clear_context()
        assert len(correlation_id()) == 12

    def test_context_isolation_between_tasks(self):
        from nitro.logging.context import clear_context, correlation_id, set_correlation_id

        results = {}

        async def task_a():
            clear_context()
            set_correlation_id("aaaaaaaaaaaa")
            await asyncio.sleep(0)
            results["a"] = correlation_id()

        async def task_b():
            clear_context()
            set_correlation_id("bbbbbbbbbbb0")
            await asyncio.sleep(0)
            results["b"] = correlation_id()

        async def run():
            await asyncio.gather(task_a(), task_b())

        asyncio.run(run())
        assert results["a"] == "aaaaaaaaaaaa"
        assert results["b"] == "bbbbbbbbbbb0"

    def test_two_calls_without_set_return_same_id(self):
        """Once generated, the same ID is returned in the same context."""
        from nitro.logging.context import clear_context, correlation_id
        clear_context()
        id1 = correlation_id()
        id2 = correlation_id()
        assert id1 == id2


# ===========================================================================
# JsonFormatter
# ===========================================================================

class TestJsonFormatter:
    def setup_method(self):
        from nitro.logging.context import clear_context, set_correlation_id
        clear_context()
        set_correlation_id("testcid12345")

    def test_output_is_valid_json(self):
        from nitro.logging.formatters import JsonFormatter
        fmt = JsonFormatter()
        record = _make_record("hello")
        output = fmt.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_includes_timestamp_iso_format(self):
        from nitro.logging.formatters import JsonFormatter
        fmt = JsonFormatter()
        parsed = json.loads(fmt.format(_make_record()))
        assert "ts" in parsed
        # ISO 8601 — contains a T separator
        assert "T" in parsed["ts"]

    def test_includes_correlation_id_from_context(self):
        from nitro.logging.formatters import JsonFormatter
        fmt = JsonFormatter()
        parsed = json.loads(fmt.format(_make_record()))
        assert parsed["correlation_id"] == "testcid12345"

    def test_includes_level(self):
        from nitro.logging.formatters import JsonFormatter
        fmt = JsonFormatter()
        parsed = json.loads(fmt.format(_make_record(level=logging.WARNING)))
        assert parsed["level"] == "WARNING"

    def test_includes_logger_name(self):
        from nitro.logging.formatters import JsonFormatter
        fmt = JsonFormatter()
        parsed = json.loads(fmt.format(_make_record(name="nitro.auth")))
        assert parsed["logger"] == "nitro.auth"

    def test_includes_message(self):
        from nitro.logging.formatters import JsonFormatter
        fmt = JsonFormatter()
        parsed = json.loads(fmt.format(_make_record("User logged in")))
        assert parsed["msg"] == "User logged in"

    def test_includes_exception_traceback(self):
        from nitro.logging.formatters import JsonFormatter
        fmt = JsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = _make_record(exc_info=exc_info)
        parsed = json.loads(fmt.format(record))
        assert "exc" in parsed
        assert "ValueError" in parsed["exc"]

    def test_handles_extra_fields_on_record(self):
        from nitro.logging.formatters import JsonFormatter
        fmt = JsonFormatter()
        record = _make_record()
        record.custom_field = "custom_value"
        parsed = json.loads(fmt.format(record))
        assert parsed.get("custom_field") == "custom_value"

    def test_record_with_correlation_id_attribute_uses_it(self):
        from nitro.logging.formatters import JsonFormatter
        fmt = JsonFormatter()
        record = _make_record()
        record.correlation_id = "overridden123"
        parsed = json.loads(fmt.format(record))
        assert parsed["correlation_id"] == "overridden123"

    def test_no_exc_key_when_no_exception(self):
        from nitro.logging.formatters import JsonFormatter
        fmt = JsonFormatter()
        parsed = json.loads(fmt.format(_make_record()))
        assert "exc" not in parsed


# ===========================================================================
# PrettyFormatter
# ===========================================================================

class TestPrettyFormatter:
    def setup_method(self):
        from nitro.logging.context import clear_context, set_correlation_id
        clear_context()
        set_correlation_id("prettyid1234")

    def test_format_contains_brackets_and_level(self):
        from nitro.logging.formatters import PrettyFormatter
        fmt = PrettyFormatter()
        output = fmt.format(_make_record("msg", level=logging.INFO))
        assert "[" in output
        assert "INFO" in output

    def test_includes_correlation_id(self):
        from nitro.logging.formatters import PrettyFormatter
        fmt = PrettyFormatter()
        output = fmt.format(_make_record())
        assert "prettyid1234" in output

    def test_includes_logger_name_and_message(self):
        from nitro.logging.formatters import PrettyFormatter
        fmt = PrettyFormatter()
        output = fmt.format(_make_record("Hello world", name="nitro.auth"))
        assert "nitro.auth" in output
        assert "Hello world" in output

    def test_handles_missing_correlation_id_gracefully(self):
        from nitro.logging.context import clear_context
        from nitro.logging.formatters import PrettyFormatter
        clear_context()
        fmt = PrettyFormatter()
        # Should not raise even when the context is empty
        output = fmt.format(_make_record())
        assert isinstance(output, str)
        assert len(output) > 0

    def test_includes_exception_info(self):
        from nitro.logging.formatters import PrettyFormatter
        fmt = PrettyFormatter()
        try:
            raise RuntimeError("test error")
        except RuntimeError:
            import sys
            exc_info = sys.exc_info()
        record = _make_record(exc_info=exc_info)
        output = fmt.format(record)
        assert "RuntimeError" in output

    def test_timestamp_in_output(self):
        from nitro.logging.formatters import PrettyFormatter
        fmt = PrettyFormatter()
        output = fmt.format(_make_record())
        # Expect a date portion like 2026-
        assert "202" in output


# ===========================================================================
# CorrelationFilter
# ===========================================================================

class TestCorrelationFilter:
    def setup_method(self):
        from nitro.logging.context import clear_context, set_correlation_id
        clear_context()
        set_correlation_id("filterid1234")

    def test_adds_correlation_id_to_record(self):
        from nitro.logging.filters import CorrelationFilter
        f = CorrelationFilter()
        record = _make_record()
        f.filter(record)
        assert record.correlation_id == "filterid1234"

    def test_always_returns_true(self):
        from nitro.logging.filters import CorrelationFilter
        f = CorrelationFilter()
        assert f.filter(_make_record()) is True

    def test_uses_current_context_value(self):
        from nitro.logging.context import set_correlation_id
        from nitro.logging.filters import CorrelationFilter
        set_correlation_id("newvalue12ab")
        f = CorrelationFilter()
        record = _make_record()
        f.filter(record)
        assert record.correlation_id == "newvalue12ab"

    def test_generates_new_id_if_none_set(self):
        from nitro.logging.context import clear_context
        from nitro.logging.filters import CorrelationFilter
        clear_context()
        f = CorrelationFilter()
        record = _make_record()
        f.filter(record)
        assert hasattr(record, "correlation_id")
        assert len(record.correlation_id) == 12


# ===========================================================================
# LoggingMiddleware
# ===========================================================================

def _make_request(path: str = "/test", method: str = "GET", headers: dict | None = None):
    req = MagicMock()
    req.method = method
    req.path = path
    req.headers = headers or {}
    req.ctx = MagicMock()
    req.ctx.nitro_start = None
    req.ctx.nitro_correlation_id = None
    return req


def _make_response(status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.headers = {}
    return resp


class TestLoggingMiddleware:
    def setup_method(self):
        from nitro.logging.context import clear_context
        clear_context()

    def test_extracts_request_id_from_header(self):
        from nitro.logging.middleware import LoggingMiddleware
        mw = LoggingMiddleware()
        req = _make_request(headers={"X-Request-ID": "headerid12ab"})
        asyncio.run(mw.on_request(req))
        assert req.ctx.nitro_correlation_id == "headerid12ab"

    def test_generates_id_when_no_header(self):
        from nitro.logging.middleware import LoggingMiddleware
        mw = LoggingMiddleware()
        req = _make_request()
        asyncio.run(mw.on_request(req))
        assert req.ctx.nitro_correlation_id is not None
        assert len(req.ctx.nitro_correlation_id) == 12

    def test_sets_request_id_on_response(self):
        from nitro.logging.middleware import LoggingMiddleware
        mw = LoggingMiddleware()
        req = _make_request()
        resp = _make_response()
        asyncio.run(mw.on_request(req))
        asyncio.run(mw.on_response(req, resp))
        assert "X-Request-ID" in resp.headers

    def test_logs_request_start(self):
        from nitro.logging.middleware import LoggingMiddleware
        mock_logger = MagicMock()
        mw = LoggingMiddleware(logger=mock_logger)
        req = _make_request()
        asyncio.run(mw.on_request(req))
        assert mock_logger.info.called

    def test_logs_request_completion_with_status_and_duration(self):
        from nitro.logging.middleware import LoggingMiddleware
        mock_logger = MagicMock()
        mw = LoggingMiddleware(logger=mock_logger)
        req = _make_request()
        resp = _make_response(status=201)
        asyncio.run(mw.on_request(req))
        asyncio.run(mw.on_response(req, resp))
        call_kwargs = mock_logger.info.call_args_list[-1][1]
        extra = call_kwargs.get("extra", {})
        assert extra.get("status") == 201
        assert "duration_ms" in extra

    def test_on_error_logs_error_level(self):
        from nitro.logging.middleware import LoggingMiddleware
        mock_logger = MagicMock()
        mw = LoggingMiddleware(logger=mock_logger)
        req = _make_request()
        asyncio.run(mw.on_error(req, ValueError("oops")))
        assert mock_logger.error.called

    def test_response_returns_response_object(self):
        from nitro.logging.middleware import LoggingMiddleware
        mw = LoggingMiddleware()
        req = _make_request()
        resp = _make_response()
        asyncio.run(mw.on_request(req))
        result = asyncio.run(mw.on_response(req, resp))
        assert result is resp


# ===========================================================================
# request_logging_middleware
# ===========================================================================

class TestRequestLoggingMiddlewareFn:
    def test_attaches_middleware_to_app(self):
        from nitro.logging.middleware import request_logging_middleware
        app = MagicMock()
        app.middleware = MagicMock(return_value=lambda f: f)
        request_logging_middleware(app)
        # middleware() should have been called twice (request + response)
        assert app.middleware.call_count == 2

    def test_returns_middleware_instance(self):
        from nitro.logging.middleware import LoggingMiddleware, request_logging_middleware
        app = MagicMock()
        app.middleware = MagicMock(return_value=lambda f: f)
        mw = request_logging_middleware(app)
        assert isinstance(mw, LoggingMiddleware)

    def test_creates_both_request_and_response_hooks(self):
        from nitro.logging.middleware import request_logging_middleware
        app = MagicMock()
        calls = []
        app.middleware = MagicMock(side_effect=lambda kind: (calls.append(kind) or (lambda f: f)))
        request_logging_middleware(app)
        assert "request" in calls
        assert "response" in calls


# ===========================================================================
# log_action decorator
# ===========================================================================

class TestLogAction:
    def setup_method(self):
        from nitro.logging.context import clear_context, set_correlation_id
        clear_context()
        set_correlation_id("decoratorcid1")

    def test_logs_entry_on_call(self):
        from nitro.logging.decorators import log_action
        with patch("logging.Logger.log") as mock_log:
            @log_action()
            def my_func():
                return 42

            my_func()
            assert mock_log.called

    def test_logs_completion_with_duration(self):
        from nitro.logging.decorators import log_action
        logged = []
        with patch("logging.Logger.log", side_effect=lambda *a, **kw: logged.append((a, kw))):
            @log_action()
            def my_func():
                return 99

            my_func()

        # At least one "Completed" entry
        completion = [e for e in logged if "Completed" in str(e)]
        assert completion

    def test_logs_errors_with_exc_info(self):
        from nitro.logging.decorators import log_action
        errors = []
        with patch("logging.Logger.error", side_effect=lambda *a, **kw: errors.append((a, kw))):
            @log_action()
            def failing():
                raise RuntimeError("deliberate")

            with pytest.raises(RuntimeError):
                failing()

        assert errors
        assert errors[0][1].get("exc_info") is not None

    def test_works_with_sync_functions(self):
        from nitro.logging.decorators import log_action

        @log_action()
        def sync_fn(x):
            return x * 2

        assert sync_fn(5) == 10

    def test_works_with_async_functions(self):
        from nitro.logging.decorators import log_action

        @log_action()
        async def async_fn(x):
            return x + 1

        result = asyncio.run(async_fn(3))
        assert result == 4

    def test_include_args_true_logs_arguments(self):
        from nitro.logging.decorators import log_action
        logged = []
        with patch("logging.Logger.log", side_effect=lambda *a, **kw: logged.append((a, kw))):
            @log_action(include_args=True)
            def fn_with_args(a, b):
                return a + b

            fn_with_args(1, 2)

        # The first log call (entry) should have args in extra
        first_extra = logged[0][1].get("extra", {})
        assert "args" in first_extra or "kwargs" in first_extra

    def test_include_args_false_omits_arguments(self):
        from nitro.logging.decorators import log_action
        logged = []
        with patch("logging.Logger.log", side_effect=lambda *a, **kw: logged.append((a, kw))):
            @log_action(include_args=False)
            def fn_no_args(a, b):
                return a + b

            fn_no_args(1, 2)

        first_extra = logged[0][1].get("extra", {})
        assert "args" not in first_extra

    def test_custom_log_level(self):
        from nitro.logging.decorators import log_action
        logged_levels = []
        with patch("logging.Logger.log", side_effect=lambda lvl, *a, **kw: logged_levels.append(lvl)):
            @log_action(level="DEBUG")
            def debug_fn():
                pass

            debug_fn()

        assert logging.DEBUG in logged_levels

    def test_preserves_function_metadata(self):
        from nitro.logging.decorators import log_action

        @log_action()
        def documented_fn():
            """My docstring."""
            pass

        assert documented_fn.__name__ == "documented_fn"
        assert documented_fn.__doc__ == "My docstring."

    def test_async_error_is_reraised(self):
        from nitro.logging.decorators import log_action

        @log_action()
        async def async_failing():
            raise ValueError("async boom")

        with pytest.raises(ValueError, match="async boom"):
            asyncio.run(async_failing())


# ===========================================================================
# configure_logging / get_logger
# ===========================================================================

class TestConfigureLogging:
    def setup_method(self):
        _reset_logging_module()

    def teardown_method(self):
        _reset_logging_module()

    def test_returns_logger(self):
        from nitro.logging.config import configure_logging
        result = configure_logging()
        assert isinstance(result, logging.Logger)

    def test_sets_info_level_by_default(self):
        from nitro.logging.config import configure_logging
        logger = configure_logging()
        assert logger.level == logging.INFO

    def test_custom_level_works(self):
        from nitro.logging.config import configure_logging
        logger = configure_logging(level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_json_output_uses_json_formatter(self):
        from nitro.logging.config import configure_logging
        from nitro.logging.formatters import JsonFormatter
        logger = configure_logging(json_output=True)
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, JsonFormatter)

    def test_pretty_uses_pretty_formatter(self):
        from nitro.logging.config import configure_logging
        from nitro.logging.formatters import PrettyFormatter
        logger = configure_logging(pretty=True)
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, PrettyFormatter)

    def test_pretty_overrides_json_output(self):
        from nitro.logging.config import configure_logging
        from nitro.logging.formatters import JsonFormatter, PrettyFormatter
        logger = configure_logging(json_output=True, pretty=True)
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, PrettyFormatter)
        assert not isinstance(handler.formatter, JsonFormatter)

    def test_adds_correlation_filter(self):
        from nitro.logging.config import configure_logging
        from nitro.logging.filters import CorrelationFilter
        logger = configure_logging()
        handler = logger.handlers[0]
        filters = handler.filters
        assert any(isinstance(f, CorrelationFilter) for f in filters)

    def test_get_logger_returns_child_logger(self):
        from nitro.logging.config import configure_logging, get_logger
        configure_logging()
        child = get_logger("auth")
        assert child.name == "nitro.auth"

    def test_get_logger_auto_configures_if_not_called(self):
        from nitro.logging.config import get_logger
        # No configure_logging() call — get_logger should self-configure
        child = get_logger("events")
        assert child.name == "nitro.events"

    def test_reconfigure_clears_old_handlers(self):
        from nitro.logging.config import configure_logging
        configure_logging()
        configure_logging()
        logger = logging.getLogger("nitro")
        assert len(logger.handlers) == 1


# ===========================================================================
# Integration tests
# ===========================================================================

class TestIntegration:
    def setup_method(self):
        _reset_logging_module()
        from nitro.logging.context import clear_context
        clear_context()

    def teardown_method(self):
        _reset_logging_module()

    def test_full_flow_correlation_in_json_output(self):
        """Configure, set a correlation ID, emit a log, verify JSON contains it."""
        import io
        from nitro.logging.config import configure_logging
        from nitro.logging.context import set_correlation_id

        set_correlation_id("integration123")
        logger = configure_logging(json_output=True)

        # Redirect handler to an in-memory stream
        buf = io.StringIO()
        handler = logger.handlers[0]
        handler.stream = buf

        logger.info("Integration test")

        output = buf.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["correlation_id"] == "integration123"
        assert parsed["msg"] == "Integration test"

    def test_middleware_and_formatter_integration(self):
        """Middleware sets correlation ID on the request context and logs it."""
        import io
        from nitro.logging.config import configure_logging
        from nitro.logging.middleware import LoggingMiddleware

        logger = configure_logging(json_output=True)
        buf = io.StringIO()
        handler = logger.handlers[0]
        handler.stream = buf

        mw = LoggingMiddleware(logger=logger)
        req = _make_request(headers={"X-Request-ID": "mwintegration12"})

        asyncio.run(mw.on_request(req))

        # Middleware stores the chosen ID on the request context object
        assert req.ctx.nitro_correlation_id == "mwintegration12"

        # The on_request call emits at least one INFO log containing the ID
        output = buf.getvalue()
        assert output  # something was logged
        first_line = output.strip().split("\n")[0]
        parsed = json.loads(first_line)
        assert parsed["correlation_id"] == "mwintegration12"

    def test_log_action_decorator_with_configured_logger(self):
        """log_action should produce log records that can be captured."""
        import io
        from nitro.logging.config import configure_logging
        from nitro.logging.decorators import log_action

        logger = configure_logging(json_output=True)
        buf = io.StringIO()
        logger.handlers[0].stream = buf

        @log_action(level="INFO")
        def greet(name):
            return f"Hello, {name}"

        greet("World")

        output = buf.getvalue()
        assert output  # something was logged
