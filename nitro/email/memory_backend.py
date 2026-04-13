"""
In-memory email backend for testing.

Captures all sent messages in a list for assertion in tests.

Example::

    from nitro.email import MemoryBackend, EmailMessage

    backend = MemoryBackend()
    await backend.send(EmailMessage(to="test@example.com", subject="Hi", body="Hello"))

    assert len(backend.outbox) == 1
    assert backend.outbox[0].subject == "Hi"
"""

from __future__ import annotations

from typing import List

from .base import EmailBackend, EmailMessage, SendResult


class MemoryBackend(EmailBackend):
    """Testing backend that stores all messages in memory.

    Attributes:
        outbox: List of sent ``EmailMessage`` objects.
        results: List of ``SendResult`` objects (one per send call).
        fail_on_send: If True, all sends return failure (for testing error paths).
        fail_error: Error message when ``fail_on_send`` is True.
    """

    def __init__(
        self,
        *,
        default_from: str = "test@localhost",
        fail_on_send: bool = False,
        fail_error: str = "Simulated send failure",
    ):
        super().__init__(default_from=default_from)
        self.outbox: List[EmailMessage] = []
        self.results: List[SendResult] = []
        self.fail_on_send = fail_on_send
        self.fail_error = fail_error

    async def send(self, message: EmailMessage) -> SendResult:
        if self.fail_on_send:
            result = SendResult(
                success=False,
                error=self.fail_error,
                backend="memory",
            )
            self.results.append(result)
            return result

        errors = message.validate()
        if errors:
            result = SendResult(
                success=False,
                error="; ".join(errors),
                backend="memory",
            )
            self.results.append(result)
            return result

        self.outbox.append(message)
        result = SendResult(
            success=True,
            message_id=f"mem-{len(self.outbox)}",
            backend="memory",
        )
        self.results.append(result)
        return result

    def reset(self) -> None:
        """Clear outbox and results."""
        self.outbox.clear()
        self.results.clear()

    @property
    def last_message(self) -> EmailMessage | None:
        """Most recently sent message, or None."""
        return self.outbox[-1] if self.outbox else None

    def find(self, *, to: str = "", subject: str = "") -> List[EmailMessage]:
        """Find messages matching criteria.

        Args:
            to: Filter by recipient (substring match).
            subject: Filter by subject (substring match).
        """
        results: List[EmailMessage] = []
        for msg in self.outbox:
            if to and not any(to in r for r in msg.to):
                continue
            if subject and subject not in msg.subject:
                continue
            results.append(msg)
        return results
