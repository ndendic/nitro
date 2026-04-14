"""
Nitro Notifications — NotificationService.

Stateless service for creating, querying, and managing in-app notifications.
Respects per-recipient type preferences: if a preference row exists with
``enabled=False``, ``send()`` returns None without persisting a notification.

All data is persisted via Entity (SQLModel Active Record).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from .models import Notification, NotificationPreference


class NotificationService:
    """Manages creation, delivery, and lifecycle of in-app notifications.

    This service is intentionally stateless — all data lives in the
    database via Entity persistence. Instantiate it once and share the
    instance, or create a new one per request; behaviour is identical.

    Example::

        svc = NotificationService()

        # Send a notification
        notif = svc.send("user-42", "info", "Welcome!", "Thanks for joining.")

        # Check unread count
        count = svc.get_unread_count("user-42")

        # Mark all read
        svc.mark_all_read("user-42")

        # Manage preferences
        svc.set_preference("user-42", "marketing", enabled=False)
    """

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    def send(
        self,
        recipient_id: str,
        type: str,
        title: str,
        message: str,
        source: str = "",
        source_id: str = "",
    ) -> Optional[Notification]:
        """Create and persist a notification for a single recipient.

        Respects preferences: if the recipient has disabled this notification
        type, ``None`` is returned without creating any record.

        Args:
            recipient_id: The recipient's ID.
            type: Notification type (e.g. "info", "warning", "error").
            title: Short title for the notification.
            message: Body text.
            source: Optional — what generated this notification.
            source_id: Optional — ID of the source entity.

        Returns:
            The saved Notification, or None if suppressed by preferences.
        """
        pref = NotificationPreference.get_preference(recipient_id, type)
        if pref is not None and not pref.enabled:
            return None

        notif = Notification(
            recipient_id=recipient_id,
            type=type,
            title=title,
            message=message,
            source=source,
            source_id=source_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        notif.save()
        return notif

    def send_bulk(
        self,
        recipient_ids: List[str],
        type: str,
        title: str,
        message: str,
        source: str = "",
        source_id: str = "",
    ) -> List[Notification]:
        """Send a notification to multiple recipients.

        Preferences are respected per-recipient. Recipients whose preferences
        suppress this type are silently skipped.

        Args:
            recipient_ids: List of recipient IDs.
            type: Notification type.
            title: Short title.
            message: Body text.
            source: Optional source identifier.
            source_id: Optional source entity ID.

        Returns:
            List of successfully created Notification objects (suppressed
            recipients are excluded).
        """
        results: List[Notification] = []
        for recipient_id in recipient_ids:
            notif = self.send(
                recipient_id=recipient_id,
                type=type,
                title=title,
                message=message,
                source=source,
                source_id=source_id,
            )
            if notif is not None:
                results.append(notif)
        return results

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def get_notifications(
        self,
        recipient_id: str,
        include_dismissed: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """Retrieve notifications for a recipient, newest first.

        Args:
            recipient_id: The recipient's ID.
            include_dismissed: Include dismissed notifications (default False).
            limit: Maximum number of notifications to return (default 50).

        Returns:
            List of Notification objects sorted by ``created_at`` descending.
        """
        notifications = Notification.for_recipient(
            recipient_id, include_dismissed=include_dismissed
        )
        return notifications[:limit]

    def get_unread(self, recipient_id: str) -> List[Notification]:
        """Return all unread, non-dismissed notifications for a recipient.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            List of unread Notification objects, newest first.
        """
        return Notification.unread_for(recipient_id)

    def get_unread_count(self, recipient_id: str) -> int:
        """Return the count of unread, non-dismissed notifications.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            Integer count of unread notifications.
        """
        return Notification.unread_count(recipient_id)

    # ------------------------------------------------------------------
    # Read / dismiss
    # ------------------------------------------------------------------

    def mark_read(self, notification_id: str) -> bool:
        """Mark a single notification as read.

        Args:
            notification_id: The notification's ID.

        Returns:
            True if the notification was found and marked, False otherwise.
        """
        notif = Notification.get(notification_id)
        if not notif:
            return False
        notif.mark_read()
        return True

    def mark_all_read(self, recipient_id: str) -> int:
        """Mark all unread notifications for a recipient as read.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            Number of notifications newly marked as read.
        """
        unread = Notification.unread_for(recipient_id)
        count = 0
        for notif in unread:
            notif.mark_read()
            count += 1
        return count

    def dismiss(self, notification_id: str) -> bool:
        """Dismiss a single notification (hides from UI, does not delete).

        Args:
            notification_id: The notification's ID.

        Returns:
            True if the notification was found and dismissed, False otherwise.
        """
        notif = Notification.get(notification_id)
        if not notif:
            return False
        notif.dismiss()
        return True

    def dismiss_all(self, recipient_id: str) -> int:
        """Dismiss all non-dismissed notifications for a recipient.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            Number of notifications newly dismissed.
        """
        notifications = Notification.for_recipient(recipient_id, include_dismissed=False)
        count = 0
        for notif in notifications:
            notif.dismiss()
            count += 1
        return count

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def clear_old(self, recipient_id: str, days: int = 30) -> int:
        """Delete notifications older than ``days`` days for a recipient.

        Args:
            recipient_id: The recipient's ID.
            days: Age threshold in days (default 30).

        Returns:
            Number of notifications deleted.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        all_notifs = Notification.where(Notification.recipient_id == recipient_id)
        if not all_notifs:
            return 0

        count = 0
        for notif in all_notifs:
            if notif.created_at and notif.created_at < cutoff_iso:
                notif.delete()
                count += 1
        return count

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------

    def set_preference(
        self, recipient_id: str, type: str, enabled: bool
    ) -> NotificationPreference:
        """Create or update a notification preference for a recipient.

        Args:
            recipient_id: The recipient's ID.
            type: The notification type.
            enabled: True to allow, False to suppress.

        Returns:
            The created or updated NotificationPreference.
        """
        return NotificationPreference.set_preference(recipient_id, type, enabled)

    def get_preferences(self, recipient_id: str) -> List[NotificationPreference]:
        """Return all preference records for a recipient.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            List of NotificationPreference objects.
        """
        results = NotificationPreference.where(
            NotificationPreference.recipient_id == recipient_id
        )
        return results if results else []
