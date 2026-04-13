"""
Sanic integration for the Nitro email system.

Attaches an email backend to the Sanic app context so handlers can
send emails via ``request.app.ctx.email``.

Example::

    from sanic import Sanic
    from nitro.email import SmtpBackend, sanic_email

    app = Sanic("MyApp")
    backend = SmtpBackend(
        host="smtp.gmail.com", port=587,
        username="you@gmail.com", password="app-password",
        use_tls=True, default_from="you@gmail.com",
    )
    sanic_email(app, backend)

    # In handlers:
    @app.post("/send-welcome")
    async def send_welcome(request):
        email = request.app.ctx.email
        result = await email.send(EmailMessage(
            to="new-user@example.com",
            subject="Welcome!",
            body="Thanks for signing up.",
        ))
        return json(result.to_dict())
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sanic import Sanic

    from .base import EmailBackend


def sanic_email(
    app: "Sanic",
    backend: "EmailBackend",
) -> None:
    """Attach an email backend to a Sanic app.

    The backend is available as ``app.ctx.email`` in handlers.

    Args:
        app: The Sanic application instance.
        backend: A configured email backend.
    """

    @app.before_server_start
    async def attach_email(app, loop):
        app.ctx.email = backend

    @app.after_server_stop
    async def cleanup_email(app, loop):
        await backend.close()
