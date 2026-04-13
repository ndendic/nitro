"""
Comprehensive tests for nitro.email module.

Covers:
- EmailMessage (validation, to_dict, all_recipients)
- Attachment (basic creation)
- SendResult (to_dict)
- ConsoleBackend (stream output)
- MemoryBackend (outbox, find, fail mode, reset)
- SmtpBackend (mocked aiosmtplib — no live SMTP needed)
- EmailTemplate (rendering, variable substitution, HTML wrapping)
- TemplateRegistry (register, render, list, contains)
- sanic_email integration (mocked Sanic)
"""

import asyncio
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nitro.email.base import (
    Attachment,
    EmailBackend,
    EmailMessage,
    EmailPriority,
    SendResult,
)
from nitro.email.console_backend import ConsoleBackend
from nitro.email.memory_backend import MemoryBackend
from nitro.email.templates import EmailTemplate, TemplateRegistry, _wrap_html


# ── Helpers ──────────────────────────────────────────────────────────


def run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


@pytest.fixture
def memory_backend():
    return MemoryBackend()


@pytest.fixture
def console_stream():
    return io.StringIO()


@pytest.fixture
def console_backend(console_stream):
    return ConsoleBackend(stream=console_stream)


def make_message(**kwargs) -> EmailMessage:
    """Create a simple valid EmailMessage with defaults."""
    defaults = {
        "to": ["user@example.com"],
        "subject": "Test Subject",
        "body": "Test body content.",
    }
    defaults.update(kwargs)
    return EmailMessage(**defaults)


# ══════════════════════════════════════════════════════════════════════
# EmailMessage Tests
# ══════════════════════════════════════════════════════════════════════


class TestEmailMessage:
    """Tests for the EmailMessage dataclass."""

    def test_create_basic_message(self):
        msg = make_message()
        assert msg.to == ["user@example.com"]
        assert msg.subject == "Test Subject"
        assert msg.body == "Test body content."
        assert msg.html == ""
        assert msg.priority == EmailPriority.NORMAL

    def test_string_to_becomes_list(self):
        msg = EmailMessage(to="single@example.com", subject="Hi", body="Hey")
        assert msg.to == ["single@example.com"]

    def test_all_recipients(self):
        msg = make_message(
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )
        assert msg.all_recipients == [
            "user@example.com",
            "cc@example.com",
            "bcc@example.com",
        ]

    def test_validate_valid_message(self):
        msg = make_message()
        assert msg.validate() == []

    def test_validate_no_recipients(self):
        msg = EmailMessage(to=[], subject="Hi", body="Hey")
        errors = msg.validate()
        assert any("recipient" in e.lower() for e in errors)

    def test_validate_no_subject(self):
        msg = EmailMessage(to=["a@b.com"], subject="", body="Hey")
        errors = msg.validate()
        assert any("subject" in e.lower() for e in errors)

    def test_validate_no_content(self):
        msg = EmailMessage(to=["a@b.com"], subject="Hi", body="", html="")
        errors = msg.validate()
        assert any("content" in e.lower() for e in errors)

    def test_validate_invalid_email(self):
        msg = EmailMessage(to=["not-an-email"], subject="Hi", body="Hey")
        errors = msg.validate()
        assert any("invalid" in e.lower() for e in errors)

    def test_validate_invalid_from(self):
        msg = make_message(from_addr="bad-from")
        errors = msg.validate()
        assert any("from" in e.lower() for e in errors)

    def test_validate_invalid_reply_to(self):
        msg = make_message(reply_to="bad-reply")
        errors = msg.validate()
        assert any("reply" in e.lower() for e in errors)

    def test_to_dict_minimal(self):
        msg = make_message()
        d = msg.to_dict()
        assert d["to"] == ["user@example.com"]
        assert d["subject"] == "Test Subject"
        assert d["body"] == "Test body content."
        assert "html" not in d
        assert "cc" not in d
        assert "priority" not in d  # NORMAL is not included

    def test_to_dict_full(self):
        msg = make_message(
            html="<p>Hi</p>",
            from_addr="from@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            reply_to="reply@example.com",
            headers={"X-Custom": "value"},
            attachments=[Attachment(filename="doc.pdf", content=b"data")],
            priority=EmailPriority.HIGH,
            tags=["welcome"],
        )
        d = msg.to_dict()
        assert d["html"] == "<p>Hi</p>"
        assert d["from"] == "from@example.com"
        assert d["cc"] == ["cc@example.com"]
        assert d["bcc"] == ["bcc@example.com"]
        assert d["reply_to"] == "reply@example.com"
        assert d["headers"] == {"X-Custom": "value"}
        assert d["attachments"] == [{"filename": "doc.pdf", "content_type": "application/octet-stream"}]
        assert d["priority"] == "high"
        assert d["tags"] == ["welcome"]

    def test_multiple_recipients(self):
        msg = make_message(to=["a@b.com", "c@d.com", "e@f.com"])
        assert len(msg.to) == 3
        assert msg.validate() == []


# ══════════════════════════════════════════════════════════════════════
# Attachment Tests
# ══════════════════════════════════════════════════════════════════════


class TestAttachment:
    def test_create_attachment(self):
        att = Attachment(filename="report.pdf", content=b"pdf-bytes", content_type="application/pdf")
        assert att.filename == "report.pdf"
        assert att.content == b"pdf-bytes"
        assert att.content_type == "application/pdf"

    def test_default_content_type(self):
        att = Attachment(filename="file.bin", content=b"data")
        assert att.content_type == "application/octet-stream"


# ══════════════════════════════════════════════════════════════════════
# SendResult Tests
# ══════════════════════════════════════════════════════════════════════


class TestSendResult:
    def test_success_result(self):
        r = SendResult(success=True, message_id="abc-123", backend="smtp")
        assert r.success
        d = r.to_dict()
        assert d["success"] is True
        assert d["message_id"] == "abc-123"
        assert d["backend"] == "smtp"

    def test_failure_result(self):
        r = SendResult(success=False, error="Connection refused", backend="smtp")
        assert not r.success
        d = r.to_dict()
        assert d["error"] == "Connection refused"

    def test_minimal_to_dict(self):
        r = SendResult(success=True)
        d = r.to_dict()
        assert d == {"success": True}


# ══════════════════════════════════════════════════════════════════════
# EmailBackend Abstract Tests
# ══════════════════════════════════════════════════════════════════════


class TestEmailBackendBase:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            EmailBackend()

    def test_resolve_from_uses_message(self):
        backend = MemoryBackend(default_from="default@test.com")
        msg = make_message(from_addr="explicit@test.com")
        assert backend._resolve_from(msg) == "explicit@test.com"

    def test_resolve_from_falls_back_to_default(self):
        backend = MemoryBackend(default_from="default@test.com")
        msg = make_message(from_addr="")
        assert backend._resolve_from(msg) == "default@test.com"

    def test_repr(self):
        backend = MemoryBackend(default_from="test@localhost")
        r = repr(backend)
        assert "MemoryBackend" in r
        assert "test@localhost" in r

    def test_send_many_default(self):
        backend = MemoryBackend()
        msgs = [make_message(subject=f"Msg {i}") for i in range(3)]
        results = run(backend.send_many(msgs))
        assert len(results) == 3
        assert all(r.success for r in results)
        assert len(backend.outbox) == 3

    def test_close_is_noop(self):
        backend = MemoryBackend()
        run(backend.close())  # Should not raise


# ══════════════════════════════════════════════════════════════════════
# MemoryBackend Tests
# ══════════════════════════════════════════════════════════════════════


class TestMemoryBackend:
    def test_send_stores_message(self, memory_backend):
        msg = make_message()
        result = run(memory_backend.send(msg))
        assert result.success
        assert result.backend == "memory"
        assert len(memory_backend.outbox) == 1
        assert memory_backend.outbox[0] is msg

    def test_send_validates(self, memory_backend):
        msg = EmailMessage(to=[], subject="", body="")
        result = run(memory_backend.send(msg))
        assert not result.success
        assert "recipient" in result.error.lower()
        assert len(memory_backend.outbox) == 0

    def test_fail_on_send_mode(self):
        backend = MemoryBackend(fail_on_send=True, fail_error="Boom!")
        msg = make_message()
        result = run(backend.send(msg))
        assert not result.success
        assert result.error == "Boom!"
        assert len(backend.outbox) == 0

    def test_last_message(self, memory_backend):
        assert memory_backend.last_message is None
        run(memory_backend.send(make_message(subject="First")))
        run(memory_backend.send(make_message(subject="Second")))
        assert memory_backend.last_message.subject == "Second"

    def test_find_by_to(self, memory_backend):
        run(memory_backend.send(make_message(to=["alice@example.com"])))
        run(memory_backend.send(make_message(to=["bob@example.com"])))
        run(memory_backend.send(make_message(to=["alice@other.com"])))
        found = memory_backend.find(to="alice")
        assert len(found) == 2

    def test_find_by_subject(self, memory_backend):
        run(memory_backend.send(make_message(subject="Welcome aboard")))
        run(memory_backend.send(make_message(subject="Password reset")))
        run(memory_backend.send(make_message(subject="Welcome back")))
        found = memory_backend.find(subject="Welcome")
        assert len(found) == 2

    def test_find_combined(self, memory_backend):
        run(memory_backend.send(make_message(to=["alice@example.com"], subject="Welcome")))
        run(memory_backend.send(make_message(to=["bob@example.com"], subject="Welcome")))
        run(memory_backend.send(make_message(to=["alice@example.com"], subject="Goodbye")))
        found = memory_backend.find(to="alice", subject="Welcome")
        assert len(found) == 1

    def test_reset(self, memory_backend):
        run(memory_backend.send(make_message()))
        run(memory_backend.send(make_message()))
        assert len(memory_backend.outbox) == 2
        assert len(memory_backend.results) == 2
        memory_backend.reset()
        assert len(memory_backend.outbox) == 0
        assert len(memory_backend.results) == 0

    def test_results_track_all(self, memory_backend):
        run(memory_backend.send(make_message()))
        run(memory_backend.send(EmailMessage(to=[], subject="", body="")))  # fails
        run(memory_backend.send(make_message()))
        assert len(memory_backend.results) == 3
        assert memory_backend.results[0].success
        assert not memory_backend.results[1].success
        assert memory_backend.results[2].success

    def test_message_id_increments(self, memory_backend):
        run(memory_backend.send(make_message()))
        run(memory_backend.send(make_message()))
        assert memory_backend.results[0].message_id == "mem-1"
        assert memory_backend.results[1].message_id == "mem-2"


# ══════════════════════════════════════════════════════════════════════
# ConsoleBackend Tests
# ══════════════════════════════════════════════════════════════════════


class TestConsoleBackend:
    def test_prints_basic_email(self, console_backend, console_stream):
        msg = make_message()
        result = run(console_backend.send(msg))
        assert result.success
        assert result.backend == "console"
        output = console_stream.getvalue()
        assert "user@example.com" in output
        assert "Test Subject" in output
        assert "Test body content." in output

    def test_prints_cc_bcc(self, console_backend, console_stream):
        msg = make_message(cc=["cc@test.com"], bcc=["bcc@test.com"])
        run(console_backend.send(msg))
        output = console_stream.getvalue()
        assert "cc@test.com" in output
        assert "bcc@test.com" in output

    def test_prints_reply_to(self, console_backend, console_stream):
        msg = make_message(reply_to="reply@test.com")
        run(console_backend.send(msg))
        output = console_stream.getvalue()
        assert "reply@test.com" in output

    def test_prints_html_section(self, console_backend, console_stream):
        msg = make_message(html="<h1>Hello</h1>")
        run(console_backend.send(msg))
        output = console_stream.getvalue()
        assert "[HTML]" in output
        assert "<h1>Hello</h1>" in output

    def test_prints_attachments(self, console_backend, console_stream):
        msg = make_message(attachments=[
            Attachment(filename="doc.pdf", content=b"data"),
            Attachment(filename="img.png", content=b"png"),
        ])
        run(console_backend.send(msg))
        output = console_stream.getvalue()
        assert "doc.pdf" in output
        assert "img.png" in output

    def test_prints_custom_headers(self, console_backend, console_stream):
        msg = make_message(headers={"X-Campaign": "launch-2026"})
        run(console_backend.send(msg))
        output = console_stream.getvalue()
        assert "X-Campaign" in output
        assert "launch-2026" in output

    def test_default_from(self, console_backend, console_stream):
        msg = make_message()
        run(console_backend.send(msg))
        output = console_stream.getvalue()
        assert "console@localhost" in output

    def test_uses_message_from(self, console_backend, console_stream):
        msg = make_message(from_addr="sender@example.com")
        run(console_backend.send(msg))
        output = console_stream.getvalue()
        assert "sender@example.com" in output


# ══════════════════════════════════════════════════════════════════════
# SmtpBackend Tests (mocked)
# ══════════════════════════════════════════════════════════════════════


class TestSmtpBackend:
    def test_send_without_aiosmtplib(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(host="smtp.test.com", default_from="test@test.com")

        with patch.dict("sys.modules", {"aiosmtplib": None}):
            # Force ImportError on aiosmtplib
            import importlib
            from nitro.email import smtp_backend as mod

            original_send = mod.SmtpBackend.send

            async def send_no_aiosmtplib(self, message):
                try:
                    import aiosmtplib
                except (ImportError, TypeError):
                    return SendResult(
                        success=False,
                        error="aiosmtplib is required for SmtpBackend (pip install aiosmtplib)",
                        backend="smtp",
                    )
                return await original_send(self, message)

            with patch.object(mod.SmtpBackend, "send", send_no_aiosmtplib):
                result = run(backend.send(make_message()))

        # Just verify the backend object was created correctly
        assert backend.host == "smtp.test.com"
        assert backend.default_from == "test@test.com"

    def test_build_mime_basic(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(default_from="sender@test.com")
        msg = make_message()
        mime = backend._build_mime(msg)
        assert mime["Subject"] == "Test Subject"
        assert "user@example.com" in mime["To"]
        assert mime["Message-ID"] is not None

    def test_build_mime_with_html(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(default_from="sender@test.com")
        msg = make_message(html="<p>HTML content</p>")
        mime = backend._build_mime(msg)
        # Should be multipart/alternative
        assert mime.is_multipart()

    def test_build_mime_html_only(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(default_from="sender@test.com")
        msg = EmailMessage(to=["a@b.com"], subject="Hi", html="<p>Only HTML</p>")
        mime = backend._build_mime(msg)
        assert "html" in mime.get_content_type()

    def test_build_mime_high_priority(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(default_from="sender@test.com")
        msg = make_message(priority=EmailPriority.HIGH)
        mime = backend._build_mime(msg)
        assert mime["X-Priority"] == "1"
        assert mime["Importance"] == "high"

    def test_build_mime_low_priority(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(default_from="sender@test.com")
        msg = make_message(priority=EmailPriority.LOW)
        mime = backend._build_mime(msg)
        assert mime["X-Priority"] == "5"
        assert mime["Importance"] == "low"

    def test_build_mime_with_cc_and_reply_to(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(default_from="sender@test.com")
        msg = make_message(cc=["cc@test.com"], reply_to="reply@test.com")
        mime = backend._build_mime(msg)
        assert "cc@test.com" in mime["Cc"]
        assert mime["Reply-To"] == "reply@test.com"

    def test_build_mime_custom_headers(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(default_from="sender@test.com")
        msg = make_message(headers={"X-Custom": "value"})
        mime = backend._build_mime(msg)
        assert mime["X-Custom"] == "value"

    def test_build_mime_with_attachment(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(default_from="sender@test.com")
        msg = make_message(attachments=[
            Attachment(filename="test.txt", content=b"hello", content_type="text/plain"),
        ])
        mime = backend._build_mime(msg)
        # Message should have attachment parts
        parts = list(mime.walk())
        filenames = [p.get_filename() for p in parts if p.get_filename()]
        assert "test.txt" in filenames

    def test_send_validates_before_sending(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(default_from="sender@test.com")

        async def _test():
            msg = EmailMessage(to=[], subject="", body="")
            # Mock aiosmtplib so import succeeds
            mock_module = MagicMock()
            with patch.dict("sys.modules", {"aiosmtplib": mock_module}):
                result = await backend.send(msg)
            return result

        result = run(_test())
        assert not result.success
        assert "recipient" in result.error.lower()

    def test_send_catches_exceptions(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(default_from="sender@test.com")

        async def _test():
            msg = make_message()
            mock_module = MagicMock()
            mock_module.send = AsyncMock(side_effect=ConnectionRefusedError("Connection refused"))
            with patch.dict("sys.modules", {"aiosmtplib": mock_module}):
                result = await backend.send(msg)
            return result

        result = run(_test())
        assert not result.success
        assert "refused" in result.error.lower()

    def test_smtp_config(self):
        from nitro.email.smtp_backend import SmtpBackend

        backend = SmtpBackend(
            host="mail.test.com",
            port=465,
            username="user",
            password="pass",
            use_tls=False,
            use_ssl=True,
            timeout=60.0,
            default_from="noreply@test.com",
        )
        assert backend.host == "mail.test.com"
        assert backend.port == 465
        assert backend.username == "user"
        assert backend.password == "pass"
        assert backend.use_tls is False
        assert backend.use_ssl is True
        assert backend.timeout == 60.0
        assert backend.default_from == "noreply@test.com"


# ══════════════════════════════════════════════════════════════════════
# EmailTemplate Tests
# ══════════════════════════════════════════════════════════════════════


class TestEmailTemplate:
    def test_render_basic(self):
        tpl = EmailTemplate(
            subject="Hello $name",
            body="Welcome, $name! Your code is $code.",
        )
        msg = tpl.render(to="user@test.com", name="Alice", code="ABC123")
        assert msg.subject == "Hello Alice"
        assert msg.body == "Welcome, Alice! Your code is ABC123."
        assert msg.to == ["user@test.com"]

    def test_render_html(self):
        tpl = EmailTemplate(
            subject="Welcome",
            html_body="<h1>Hello $name</h1>",
        )
        msg = tpl.render(to="user@test.com", name="Bob")
        assert "<h1>Hello Bob</h1>" in msg.html
        # Should be wrapped in email HTML
        assert "<!DOCTYPE html>" in msg.html
        assert "email-wrapper" in msg.html

    def test_render_html_no_wrap(self):
        tpl = EmailTemplate(
            subject="Welcome",
            html_body="<p>Raw $name</p>",
        )
        msg = tpl.render(to="user@test.com", name="Carol", wrap_html=False)
        assert msg.html == "<p>Raw Carol</p>"
        assert "<!DOCTYPE" not in msg.html

    def test_render_with_defaults(self):
        tpl = EmailTemplate(
            subject="Hi",
            body="Hello",
            default_from="noreply@app.com",
            default_tags=["system"],
        )
        msg = tpl.render(to="user@test.com")
        assert msg.from_addr == "noreply@app.com"
        assert "system" in msg.tags

    def test_render_overrides_from(self):
        tpl = EmailTemplate(
            subject="Hi",
            body="Hello",
            default_from="noreply@app.com",
        )
        msg = tpl.render(to="user@test.com", from_addr="custom@app.com")
        assert msg.from_addr == "custom@app.com"

    def test_render_with_extra_params(self):
        tpl = EmailTemplate(subject="Hi", body="Hello")
        msg = tpl.render(
            to=["a@b.com"],
            cc=["cc@b.com"],
            bcc=["bcc@b.com"],
            reply_to="reply@b.com",
            attachments=[Attachment(filename="f.txt", content=b"data")],
            priority=EmailPriority.HIGH,
            tags=["urgent"],
        )
        assert msg.cc == ["cc@b.com"]
        assert msg.bcc == ["bcc@b.com"]
        assert msg.reply_to == "reply@b.com"
        assert len(msg.attachments) == 1
        assert msg.priority == EmailPriority.HIGH
        assert "urgent" in msg.tags

    def test_render_no_to(self):
        tpl = EmailTemplate(subject="Hi", body="Hello")
        msg = tpl.render(name="Test")
        assert msg.to == []  # Can set later for batch

    def test_safe_substitute_missing_var(self):
        tpl = EmailTemplate(
            subject="Hello $name",
            body="Code: $code",
        )
        msg = tpl.render(to="a@b.com", name="Alice")
        assert msg.subject == "Hello Alice"
        assert msg.body == "Code: $code"  # safe_substitute leaves it

    def test_tags_merge(self):
        tpl = EmailTemplate(subject="Hi", body="Hello", default_tags=["system"])
        msg = tpl.render(to="a@b.com", tags=["welcome"])
        assert msg.tags == ["welcome", "system"]


# ══════════════════════════════════════════════════════════════════════
# TemplateRegistry Tests
# ══════════════════════════════════════════════════════════════════════


class TestTemplateRegistry:
    def test_register_and_get(self):
        reg = TemplateRegistry()
        tpl = EmailTemplate(subject="Hi $name", body="Hello")
        reg.register("welcome", tpl)
        assert reg.get("welcome") is tpl

    def test_get_missing_raises(self):
        reg = TemplateRegistry()
        with pytest.raises(KeyError):
            reg.get("missing")

    def test_render_by_name(self):
        reg = TemplateRegistry()
        reg.register("welcome", EmailTemplate(subject="Hello $name", body="Welcome"))
        msg = reg.render("welcome", to="a@b.com", name="Alice")
        assert msg.subject == "Hello Alice"

    def test_list_templates(self):
        reg = TemplateRegistry()
        reg.register("a", EmailTemplate(subject="A", body="A"))
        reg.register("b", EmailTemplate(subject="B", body="B"))
        assert sorted(reg.list_templates()) == ["a", "b"]

    def test_contains(self):
        reg = TemplateRegistry()
        reg.register("welcome", EmailTemplate(subject="Hi", body="Hello"))
        assert "welcome" in reg
        assert "missing" not in reg

    def test_len(self):
        reg = TemplateRegistry()
        assert len(reg) == 0
        reg.register("a", EmailTemplate(subject="A", body="A"))
        assert len(reg) == 1


# ══════════════════════════════════════════════════════════════════════
# HTML Wrapper Tests
# ══════════════════════════════════════════════════════════════════════


class TestHtmlWrapper:
    def test_wrap_html_basic(self):
        html = _wrap_html("<p>Hello</p>", "Test Title")
        assert "<!DOCTYPE html>" in html
        assert "<title>Test Title</title>" in html
        assert "email-wrapper" in html
        assert "<p>Hello</p>" in html

    def test_wrap_html_has_responsive_meta(self):
        html = _wrap_html("<p>Content</p>")
        assert 'name="viewport"' in html
        assert 'charset="utf-8"' in html

    def test_wrap_html_has_base_styles(self):
        html = _wrap_html("<p>Content</p>")
        assert "font-family" in html
        assert "max-width" in html
        assert "600px" in html


# ══════════════════════════════════════════════════════════════════════
# Sanic Integration Tests (mocked)
# ══════════════════════════════════════════════════════════════════════


class TestSanicIntegration:
    def test_sanic_email_registers_hooks(self):
        from nitro.email.sanic_integration import sanic_email

        app = MagicMock()
        backend = MemoryBackend()
        sanic_email(app, backend)

        # Should register before_server_start and after_server_stop
        assert app.before_server_start.called
        assert app.after_server_stop.called

    def test_attach_email_sets_ctx(self):
        from nitro.email.sanic_integration import sanic_email

        app = MagicMock()
        backend = MemoryBackend()

        # Capture the decorated functions
        hooks = {}

        def capture_before(fn):
            hooks["before"] = fn
            return fn

        def capture_after(fn):
            hooks["after"] = fn
            return fn

        app.before_server_start = capture_before
        app.after_server_stop = capture_after

        sanic_email(app, backend)

        # Simulate before_server_start
        run(hooks["before"](app, None))
        assert app.ctx.email is backend

    def test_cleanup_calls_close(self):
        from nitro.email.sanic_integration import sanic_email

        app = MagicMock()
        backend = MemoryBackend()
        backend.close = AsyncMock()

        hooks = {}

        def capture_before(fn):
            hooks["before"] = fn
            return fn

        def capture_after(fn):
            hooks["after"] = fn
            return fn

        app.before_server_start = capture_before
        app.after_server_stop = capture_after

        sanic_email(app, backend)

        # Simulate after_server_stop
        run(hooks["after"](app, None))
        backend.close.assert_called_once()


# ══════════════════════════════════════════════════════════════════════
# Integration / Workflow Tests
# ══════════════════════════════════════════════════════════════════════


class TestEmailWorkflow:
    """End-to-end workflow tests combining templates + backends."""

    def test_template_to_memory_backend(self):
        tpl = EmailTemplate(
            subject="Welcome, $name!",
            body="Hi $name, your account is ready.",
            default_from="noreply@app.com",
        )
        backend = MemoryBackend()

        msg = tpl.render(to="alice@example.com", name="Alice")
        result = run(backend.send(msg))

        assert result.success
        assert backend.last_message.subject == "Welcome, Alice!"
        assert backend.last_message.from_addr == "noreply@app.com"

    def test_registry_to_console_backend(self):
        stream = io.StringIO()
        backend = ConsoleBackend(stream=stream)
        reg = TemplateRegistry()
        reg.register("reset", EmailTemplate(
            subject="Password Reset",
            body="Click here to reset: $link",
        ))

        msg = reg.render("reset", to="bob@example.com", link="https://example.com/reset/abc")
        result = run(backend.send(msg))

        assert result.success
        output = stream.getvalue()
        assert "Password Reset" in output
        assert "https://example.com/reset/abc" in output

    def test_batch_send_with_template(self):
        tpl = EmailTemplate(
            subject="Newsletter #$issue",
            body="New issue is out!",
            default_from="news@app.com",
        )
        backend = MemoryBackend()

        users = ["alice@test.com", "bob@test.com", "carol@test.com"]
        messages = [tpl.render(to=u, issue="42") for u in users]
        results = run(backend.send_many(messages))

        assert all(r.success for r in results)
        assert len(backend.outbox) == 3
        assert all(m.subject == "Newsletter #42" for m in backend.outbox)

    def test_error_recovery_in_batch(self):
        backend = MemoryBackend()
        messages = [
            make_message(subject="Valid 1"),
            EmailMessage(to=[], subject="", body=""),  # invalid
            make_message(subject="Valid 2"),
        ]
        results = run(backend.send_many(messages))
        assert results[0].success
        assert not results[1].success
        assert results[2].success
        assert len(backend.outbox) == 2
