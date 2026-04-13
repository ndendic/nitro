"""
SMTP email backend using aiosmtplib for async delivery.

Supports SMTP, SMTP+STARTTLS, and SMTPS (implicit TLS).

Example::

    from nitro.email import SmtpBackend

    backend = SmtpBackend(
        host="smtp.gmail.com",
        port=587,
        username="you@gmail.com",
        password="app-password",
        use_tls=True,
        default_from="you@gmail.com",
    )

    result = await backend.send(message)
"""

from __future__ import annotations

import uuid
from email.message import EmailMessage as StdEmailMessage
from email.utils import formataddr, formatdate
from typing import List, Optional, Sequence

from .base import Attachment, EmailBackend, EmailMessage, EmailPriority, SendResult


class SmtpBackend(EmailBackend):
    """Async SMTP backend.

    Args:
        host: SMTP server hostname.
        port: SMTP server port (25, 465, 587).
        username: SMTP auth username (optional).
        password: SMTP auth password (optional).
        use_tls: Use STARTTLS on connect (port 587).
        use_ssl: Use implicit SSL/TLS (port 465).
        timeout: Connection timeout in seconds.
        default_from: Default sender address.
    """

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 587,
        username: str = "",
        password: str = "",
        use_tls: bool = True,
        use_ssl: bool = False,
        timeout: float = 30.0,
        default_from: str = "",
    ):
        super().__init__(default_from=default_from)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.timeout = timeout

    def _build_mime(self, message: EmailMessage) -> StdEmailMessage:
        """Build a stdlib email.message.EmailMessage from an EmailMessage."""
        from_addr = self._resolve_from(message)

        msg = StdEmailMessage()
        msg["Subject"] = message.subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(message.to)
        if message.cc:
            msg["Cc"] = ", ".join(message.cc)
        if message.reply_to:
            msg["Reply-To"] = message.reply_to
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = f"<{uuid.uuid4().hex}@nitro>"

        # Priority header
        if message.priority == EmailPriority.HIGH:
            msg["X-Priority"] = "1"
            msg["Importance"] = "high"
        elif message.priority == EmailPriority.LOW:
            msg["X-Priority"] = "5"
            msg["Importance"] = "low"

        # Custom headers
        for key, value in message.headers.items():
            msg[key] = value

        # Body content
        if message.body and message.html:
            msg.set_content(message.body)
            msg.add_alternative(message.html, subtype="html")
        elif message.html:
            msg.set_content(message.html, subtype="html")
        else:
            msg.set_content(message.body)

        # Attachments
        for att in message.attachments:
            maintype, _, subtype = att.content_type.partition("/")
            msg.add_attachment(
                att.content,
                maintype=maintype or "application",
                subtype=subtype or "octet-stream",
                filename=att.filename,
            )

        return msg

    async def send(self, message: EmailMessage) -> SendResult:
        """Send an email via SMTP."""
        try:
            import aiosmtplib
        except ImportError:
            return SendResult(
                success=False,
                error="aiosmtplib is required for SmtpBackend (pip install aiosmtplib)",
                backend="smtp",
            )

        errors = message.validate()
        if errors:
            return SendResult(
                success=False,
                error="; ".join(errors),
                backend="smtp",
            )

        try:
            mime_msg = self._build_mime(message)
            recipients = message.all_recipients

            kwargs = {
                "hostname": self.host,
                "port": self.port,
                "timeout": self.timeout,
            }
            if self.use_ssl:
                kwargs["use_tls"] = True
            elif self.use_tls:
                kwargs["start_tls"] = True

            if self.username and self.password:
                kwargs["username"] = self.username
                kwargs["password"] = self.password

            await aiosmtplib.send(
                mime_msg,
                recipients=recipients,
                **kwargs,
            )

            message_id = mime_msg["Message-ID"] or ""
            return SendResult(
                success=True,
                message_id=message_id,
                backend="smtp",
            )
        except Exception as exc:
            return SendResult(
                success=False,
                error=str(exc),
                backend="smtp",
            )

    async def send_many(self, messages: Sequence[EmailMessage]) -> list[SendResult]:
        """Send multiple messages, reusing a single SMTP connection."""
        try:
            import aiosmtplib
        except ImportError:
            return [
                SendResult(
                    success=False,
                    error="aiosmtplib is required (pip install aiosmtplib)",
                    backend="smtp",
                )
                for _ in messages
            ]

        results: list[SendResult] = []
        try:
            smtp = aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                timeout=self.timeout,
                use_tls=self.use_ssl,
                start_tls=self.use_tls if not self.use_ssl else False,
            )
            await smtp.connect()
            if self.username and self.password:
                await smtp.login(self.username, self.password)

            for message in messages:
                errors = message.validate()
                if errors:
                    results.append(SendResult(
                        success=False, error="; ".join(errors), backend="smtp"
                    ))
                    continue
                try:
                    mime_msg = self._build_mime(message)
                    await smtp.send_message(mime_msg, recipients=message.all_recipients)
                    results.append(SendResult(
                        success=True,
                        message_id=mime_msg["Message-ID"] or "",
                        backend="smtp",
                    ))
                except Exception as exc:
                    results.append(SendResult(
                        success=False, error=str(exc), backend="smtp"
                    ))

            await smtp.quit()
        except Exception as exc:
            # Connection-level failure — mark remaining as failed
            remaining = len(messages) - len(results)
            for _ in range(remaining):
                results.append(SendResult(
                    success=False, error=f"Connection error: {exc}", backend="smtp"
                ))

        return results
