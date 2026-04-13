"""
nitro.email — Framework-agnostic email service for the Nitro framework.

Provides:
- EmailMessage      : Structured email message with validation
- EmailBackend      : Abstract base for delivery backends
- SendResult        : Result of a send operation
- ConsoleBackend    : Prints emails to stdout (development)
- MemoryBackend     : Stores emails in-memory (testing)
- EmailTemplate     : Reusable templates with $variable substitution
- TemplateRegistry  : Named template lookup

Optional backends (requires extra dependencies):
- SmtpBackend       : SMTP/STARTTLS/SSL delivery (pip install aiosmtplib)

Sanic integration:
- sanic_email       : Attach email backend to app context

Quick start::

    from nitro.email import MemoryBackend, EmailMessage

    backend = MemoryBackend()
    result = await backend.send(EmailMessage(
        to="user@example.com",
        subject="Hello",
        body="Welcome to Nitro!",
    ))
    assert result.success

Development (console output)::

    from nitro.email import ConsoleBackend, EmailMessage

    backend = ConsoleBackend()
    await backend.send(EmailMessage(
        to="dev@localhost",
        subject="Test",
        body="This prints to stdout.",
    ))

Templates::

    from nitro.email import EmailTemplate

    welcome = EmailTemplate(
        subject="Welcome, $name!",
        body="Hello $name, your account ($email) is ready.",
    )
    msg = welcome.render(to="alice@example.com", name="Alice", email="alice@example.com")

SMTP (production)::

    from nitro.email.smtp_backend import SmtpBackend

    backend = SmtpBackend(
        host="smtp.gmail.com", port=587,
        username="you@gmail.com", password="app-password",
        use_tls=True, default_from="you@gmail.com",
    )

Sanic integration::

    from sanic import Sanic
    from nitro.email import ConsoleBackend, sanic_email

    app = Sanic("MyApp")
    sanic_email(app, ConsoleBackend())

    # In handlers: request.app.ctx.email
"""

from .base import (
    Attachment,
    EmailBackend,
    EmailMessage,
    EmailPriority,
    SendResult,
)
from .console_backend import ConsoleBackend
from .memory_backend import MemoryBackend
from .sanic_integration import sanic_email
from .templates import EmailTemplate, TemplateRegistry

__all__ = [
    "Attachment",
    "EmailBackend",
    "EmailMessage",
    "EmailPriority",
    "SendResult",
    "ConsoleBackend",
    "MemoryBackend",
    "EmailTemplate",
    "TemplateRegistry",
    "sanic_email",
]

# SmtpBackend is imported lazily to avoid hard dependency on aiosmtplib.
# Import it explicitly when needed:
#
#   from nitro.email.smtp_backend import SmtpBackend
