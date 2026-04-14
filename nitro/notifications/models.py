"""
Nitro Notifications — Notification and NotificationPreference entities.

Provides an in-app notification system built on top of Nitro's Entity base
class. Notifications are persisted per-recipient with read/dismiss state.
NotificationPreference lets recipients opt out of specific notification types.

Design choices:
- Both entities use the ``notif_`` table prefix for clear schema isolation
- Timestamps are stored as ISO 8601 strings for portability
- Preference checks are opt-in blocking: if no preference row exists,
  notifications are delivered (default-allow)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from nitro.domain.entities.base_entity import Entity
from sqlmodel import Field


class Notification(Entity, table=True):
    """A single in-app notification for a recipient.

    Attributes:
        recipient_id: ID of the user or entity this notification is for.
        type: Notification type (e.g. "info", "warning", "error", "success", "system").
        title: Short human-readable title.
        message: Full body text of the notification.
        source: What generated this notification (e.g. module or class name).
        source_id: Optional ID referencing the source entity.
        is_read: Whether the recipient has read this notification.
        is_dismissed: Whether the recipient has dismissed (hidden) this notification.
        created_at: ISO 8601 timestamp of creation.
        read_at: ISO 8601 timestamp of when the notification was marked read.
    """

    __tablename__ = "notif_notifications"

    recipient_id: str = Field(index=True)
    type: str
    title: str
    message: str
    source: str = ""
    source_id: str = ""
    is_read: bool = Field(default=False, index=True)
    is_dismissed: bool = False
    created_at: str = ""
    read_at: str = ""

    def mark_read(self) -> "Notification":
        """Mark this notification as read and record the timestamp.

        Returns:
            Self (for chaining).
        """
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now(timezone.utc).isoformat()
            self.save()
        return self

    def mark_unread(self) -> "Notification":
        """Mark this notification as unread and clear the read timestamp.

        Returns:
            Self (for chaining).
        """
        if self.is_read:
            self.is_read = False
            self.read_at = ""
            self.save()
        return self

    def dismiss(self) -> "Notification":
        """Dismiss this notification (hidden from UI but not deleted).

        Returns:
            Self (for chaining).
        """
        if not self.is_dismissed:
            self.is_dismissed = True
            self.save()
        return self

    @classmethod
    def for_recipient(
        cls, recipient_id: str, include_dismissed: bool = False
    ) -> List["Notification"]:
        """Return all notifications for a recipient.

        Args:
            recipient_id: The recipient's ID.
            include_dismissed: If False (default), excludes dismissed notifications.

        Returns:
            List of Notification objects, newest first.
        """
        results = cls.where(cls.recipient_id == recipient_id)
        if not results:
            return []
        if not include_dismissed:
            results = [n for n in results if not n.is_dismissed]
        return sorted(results, key=lambda n: n.created_at, reverse=True)

    @classmethod
    def unread_for(cls, recipient_id: str) -> List["Notification"]:
        """Return all unread, non-dismissed notifications for a recipient.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            List of unread Notification objects, newest first.
        """
        results = cls.where(
            cls.recipient_id == recipient_id,
            cls.is_read == False,  # noqa: E712
        )
        if not results:
            return []
        results = [n for n in results if not n.is_dismissed]
        return sorted(results, key=lambda n: n.created_at, reverse=True)

    @classmethod
    def unread_count(cls, recipient_id: str) -> int:
        """Return the number of unread, non-dismissed notifications for a recipient.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            Count of unread notifications.
        """
        return len(cls.unread_for(recipient_id))

    def __repr__(self) -> str:
        return f"<Notification {self.type!r} for={self.recipient_id!r} read={self.is_read}>"


class NotificationPreference(Entity, table=True):
    """Per-recipient preference for a notification type.

    When a preference row exists with ``enabled=False``, notifications of
    that type are suppressed for that recipient. If no row exists, the
    default is to allow delivery.

    Attributes:
        recipient_id: The recipient's ID.
        type: The notification type this preference governs.
        enabled: If False, notifications of this type are suppressed.
    """

    __tablename__ = "notif_preferences"

    recipient_id: str = Field(index=True)
    type: str
    enabled: bool = True

    @classmethod
    def get_preference(
        cls, recipient_id: str, type: str
    ) -> Optional["NotificationPreference"]:
        """Look up a preference for a specific recipient and type.

        Args:
            recipient_id: The recipient's ID.
            type: The notification type.

        Returns:
            The NotificationPreference if found, or None.
        """
        results = cls.find_by(recipient_id=recipient_id, type=type)
        if not results:
            return None
        return results[0] if isinstance(results, list) else results

    @classmethod
    def set_preference(
        cls, recipient_id: str, type: str, enabled: bool
    ) -> "NotificationPreference":
        """Create or update a preference for a recipient/type pair.

        Args:
            recipient_id: The recipient's ID.
            type: The notification type.
            enabled: Whether to allow notifications of this type.

        Returns:
            The created or updated NotificationPreference.
        """
        existing = cls.get_preference(recipient_id, type)
        if existing:
            if existing.enabled != enabled:
                existing.enabled = enabled
                existing.save()
            return existing
        pref = cls(recipient_id=recipient_id, type=type, enabled=enabled)
        pref.save()
        return pref

    def __repr__(self) -> str:
        return (
            f"<NotificationPreference recipient={self.recipient_id!r} "
            f"type={self.type!r} enabled={self.enabled}>"
        )
