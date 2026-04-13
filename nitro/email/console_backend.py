"""
Console email backend — prints emails to stdout for development.

Useful during development when you want to see email output without
configuring a real SMTP server.

Example::

    from nitro.email import ConsoleBackend

    backend = ConsoleBackend()
    await backend.send(message)
    # Prints formatted email to stdout
"""

from __future__ import annotations

import sys
from typing import TextIO

from .base import EmailBackend, EmailMessage, SendResult


class ConsoleBackend(EmailBackend):
    """Development backend that prints emails to a stream (default: stdout).

    Args:
        stream: Output stream (default ``sys.stdout``).
        default_from: Default sender address.
    """

    def __init__(
        self,
        *,
        stream: TextIO | None = None,
        default_from: str = "console@localhost",
    ):
        super().__init__(default_from=default_from)
        self.stream = stream or sys.stdout

    async def send(self, message: EmailMessage) -> SendResult:
        from_addr = self._resolve_from(message)
        separator = "=" * 60

        lines = [
            separator,
            f"From:     {from_addr}",
            f"To:       {', '.join(message.to)}",
        ]
        if message.cc:
            lines.append(f"Cc:       {', '.join(message.cc)}")
        if message.bcc:
            lines.append(f"Bcc:      {', '.join(message.bcc)}")
        if message.reply_to:
            lines.append(f"Reply-To: {message.reply_to}")
        lines.append(f"Subject:  {message.subject}")
        if message.headers:
            for k, v in message.headers.items():
                lines.append(f"{k}: {v}")
        if message.attachments:
            names = ", ".join(a.filename for a in message.attachments)
            lines.append(f"Attachments: {names}")
        lines.append("-" * 60)
        if message.body:
            lines.append(message.body)
        if message.html:
            lines.append("-" * 60 + " [HTML]")
            lines.append(message.html)
        lines.append(separator)

        self.stream.write("\n".join(lines) + "\n")
        self.stream.flush()

        return SendResult(
            success=True,
            message_id=f"console-{id(message)}",
            backend="console",
        )
