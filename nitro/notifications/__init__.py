"""
nitro.notifications — In-app notification system for Nitro.

Provides per-recipient notifications with read/dismiss state, preference-based
filtering, and a stateless service layer for sending and querying notifications.

Quick start::

    from nitro.notifications import Notification, NotificationPreference, NotificationService

    svc = NotificationService()

    # Send a notification to a user
    notif = svc.send(
        recipient_id="user-42",
        type="info",
        title="New message",
        message="You have a new message from Alice.",
        source="messaging",
        source_id="msg-99",
    )

    # Bulk send to multiple recipients
    sent = svc.send_bulk(
        recipient_ids=["user-1", "user-2", "user-3"],
        type="system",
        title="Maintenance window",
        message="Scheduled downtime on Saturday 02:00 UTC.",
    )

    # Retrieve notifications (newest first, excludes dismissed by default)
    notifications = svc.get_notifications("user-42", limit=20)

    # Check unread count
    count = svc.get_unread_count("user-42")  # → int

    # Mark a single notification read
    svc.mark_read(notif.id)

    # Mark everything read for a recipient
    marked = svc.mark_all_read("user-42")  # → count of newly marked

    # Dismiss (hide from UI without deleting)
    svc.dismiss(notif.id)
    svc.dismiss_all("user-42")

    # Delete notifications older than 30 days
    deleted = svc.clear_old("user-42", days=30)

    # Opt a recipient out of a notification type
    svc.set_preference("user-42", "marketing", enabled=False)

    # Attempting to send a suppressed type returns None
    result = svc.send("user-42", "marketing", "Sale!", "50% off today.")
    assert result is None

    # Inspect all preferences for a recipient
    prefs = svc.get_preferences("user-42")
"""

from .models import Notification, NotificationPreference
from .service import NotificationService

__all__ = [
    "Notification",
    "NotificationPreference",
    "NotificationService",
]
