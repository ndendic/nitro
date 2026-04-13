"""
Abstract base interface and data types for the Nitro email system.

All email backends must subclass ``EmailBackend`` and implement
``send()`` / ``send_many()``. This ensures backends are interchangeable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union


class EmailPriority(str, Enum):
    """Email priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class Attachment:
    """An email attachment.

    Attributes:
        filename: Name of the attached file.
        content: Raw bytes of the file.
        content_type: MIME type (e.g. ``"application/pdf"``).
    """

    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class EmailMessage:
    """An email message ready to be sent via a backend.

    Attributes:
        to: Recipient address(es).
        subject: Email subject line.
        body: Plain-text body.
        html: Optional HTML body (sent as multipart/alternative).
        from_addr: Sender address. Falls back to backend default if omitted.
        cc: Carbon-copy recipients.
        bcc: Blind carbon-copy recipients.
        reply_to: Reply-to address.
        headers: Arbitrary extra headers.
        attachments: File attachments.
        priority: Message priority level.
        tags: Arbitrary tags for tracking / analytics.
    """

    to: List[str]
    subject: str
    body: str = ""
    html: str = ""
    from_addr: str = ""
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    reply_to: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    attachments: List[Attachment] = field(default_factory=list)
    priority: EmailPriority = EmailPriority.NORMAL
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        # Normalise single-string `to` into a list
        if isinstance(self.to, str):
            self.to = [self.to]

    @property
    def all_recipients(self) -> List[str]:
        """All recipients (to + cc + bcc)."""
        return self.to + self.cc + self.bcc

    def validate(self) -> List[str]:
        """Validate the message and return a list of errors (empty = valid)."""
        errors: List[str] = []
        if not self.to:
            errors.append("At least one recipient is required")
        if not self.subject:
            errors.append("Subject is required")
        if not self.body and not self.html:
            errors.append("Either body or html content is required")
        for addr in self.all_recipients:
            if "@" not in addr:
                errors.append(f"Invalid email address: {addr!r}")
        if self.from_addr and "@" not in self.from_addr:
            errors.append(f"Invalid from address: {self.from_addr!r}")
        if self.reply_to and "@" not in self.reply_to:
            errors.append(f"Invalid reply-to address: {self.reply_to!r}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict (useful for logging / queuing)."""
        d: Dict[str, Any] = {
            "to": self.to,
            "subject": self.subject,
        }
        if self.body:
            d["body"] = self.body
        if self.html:
            d["html"] = self.html
        if self.from_addr:
            d["from"] = self.from_addr
        if self.cc:
            d["cc"] = self.cc
        if self.bcc:
            d["bcc"] = self.bcc
        if self.reply_to:
            d["reply_to"] = self.reply_to
        if self.headers:
            d["headers"] = self.headers
        if self.attachments:
            d["attachments"] = [
                {"filename": a.filename, "content_type": a.content_type}
                for a in self.attachments
            ]
        if self.priority != EmailPriority.NORMAL:
            d["priority"] = self.priority.value
        if self.tags:
            d["tags"] = self.tags
        return d


@dataclass
class SendResult:
    """Result of sending a single email message.

    Attributes:
        success: Whether the send succeeded.
        message_id: Backend-assigned message ID (if available).
        error: Error description on failure.
        backend: Name of the backend that handled it.
    """

    success: bool
    message_id: str = ""
    error: str = ""
    backend: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.message_id:
            d["message_id"] = self.message_id
        if self.error:
            d["error"] = self.error
        if self.backend:
            d["backend"] = self.backend
        return d


class EmailBackend(ABC):
    """Abstract base class for email delivery backends.

    Subclass this and implement ``send()`` to create a custom backend.

    Args:
        default_from: Default sender address used when ``EmailMessage.from_addr``
            is empty.
    """

    def __init__(self, *, default_from: str = ""):
        self.default_from = default_from

    @abstractmethod
    async def send(self, message: EmailMessage) -> SendResult:
        """Send a single email message.

        Implementations must return a ``SendResult`` — never raise on
        delivery failure; capture the error in the result instead.
        """

    async def send_many(self, messages: Sequence[EmailMessage]) -> List[SendResult]:
        """Send multiple messages. Default: sequential send().

        Backends may override for batch-optimised delivery.
        """
        results: List[SendResult] = []
        for msg in messages:
            results.append(await self.send(msg))
        return results

    async def close(self) -> None:
        """Clean up resources (connections, pools). Default: no-op."""

    def _resolve_from(self, message: EmailMessage) -> str:
        """Return the sender address, falling back to default_from."""
        return message.from_addr or self.default_from

    def __repr__(self) -> str:
        return f"{type(self).__name__}(default_from={self.default_from!r})"
