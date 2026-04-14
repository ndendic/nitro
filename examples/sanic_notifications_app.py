"""
Sanic Notifications — Real-time Notification Center

Demonstrates:
  1. Background server push — new notifications arrive without user action
  2. State toggling — read/unread per notification
  3. Bulk operations — mark all read, clear all
  4. Type-differentiated rendering — icons/colors per notification kind
  5. Computed UI state — unread badge count derived from entity data
  6. Multi-region SSE updates — header badge + notification list + empty state
  7. Time-relative display — "just now", "2m ago", etc.

New patterns vs. prior examples:
  - Unread badge counter computed from entity state (derived UI element)
  - Per-item state toggle via instance method (@post on instance)
  - Multiple notification types with distinct visual treatments
  - Background task generating varied notification content

Run:
    cd nitro && python examples/sanic_notifications_app.py
    Then visit http://localhost:8020
"""
import os
os.environ.setdefault("NITRO_DB_URL", "sqlite:///notifications.db")

import uuid
import random
import asyncio
from datetime import datetime, timezone

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import (
    Div, H1, H2, P, Span, Button, Header,
)

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

class Notification(Entity, table=True):
    """A notification with type, message, read state, and timestamp."""
    __tablename__ = "notifications"
    title: str = ""
    message: str = ""
    kind: str = "info"       # info, success, warning, error, mention
    is_read: bool = False
    created_at: str = ""     # ISO timestamp for ordering

    @post()
    def toggle_read(self, request=None):
        """Toggle read/unread state."""
        self.is_read = not self.is_read
        self.save()
        _broadcast_all()
        return {"id": self.id, "is_read": self.is_read}

    @post()
    def dismiss(self, request=None):
        """Remove this notification."""
        self.delete()
        _broadcast_all()
        return {"dismissed": self.id}

    @classmethod
    @post()
    def mark_all_read(cls, request=None):
        """Mark every notification as read."""
        for n in cls.all():
            if not n.is_read:
                n.is_read = True
                n.save()
        _broadcast_all()
        return {"marked": True}

    @classmethod
    @post()
    def clear_all(cls, request=None):
        """Delete all notifications."""
        for n in cls.all():
            n.delete()
        _broadcast_all()
        return {"cleared": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _time_ago(iso_str: str) -> str:
    """Convert ISO timestamp to relative time string."""
    try:
        then = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        diff = (datetime.now(timezone.utc) - then).total_seconds()
        if diff < 60:
            return "just now"
        elif diff < 3600:
            m = int(diff // 60)
            return f"{m}m ago"
        elif diff < 86400:
            h = int(diff // 3600)
            return f"{h}h ago"
        else:
            d = int(diff // 86400)
            return f"{d}d ago"
    except (ValueError, TypeError):
        return ""


def _unread_count() -> int:
    return sum(1 for n in Notification.all() if not n.is_read)


# ---------------------------------------------------------------------------
# Notification type config
# ---------------------------------------------------------------------------

KIND_CONFIG = {
    "info": {
        "icon": "i",
        "icon_cls": "bg-blue-100 text-blue-600",
        "border": "border-l-blue-400",
        "label": "Info",
    },
    "success": {
        "icon": "✓",
        "icon_cls": "bg-emerald-100 text-emerald-600",
        "border": "border-l-emerald-400",
        "label": "Success",
    },
    "warning": {
        "icon": "!",
        "icon_cls": "bg-amber-100 text-amber-600",
        "border": "border-l-amber-400",
        "label": "Warning",
    },
    "error": {
        "icon": "✕",
        "icon_cls": "bg-red-100 text-red-600",
        "border": "border-l-red-400",
        "label": "Error",
    },
    "mention": {
        "icon": "@",
        "icon_cls": "bg-violet-100 text-violet-600",
        "border": "border-l-violet-400",
        "label": "Mention",
    },
}


# ---------------------------------------------------------------------------
# Broadcast
# ---------------------------------------------------------------------------

def _broadcast_all():
    """Push header badge + notification list to all clients."""
    publish_sync("sse", SSE.patch_elements(unread_badge(), selector="#unread-badge"))
    publish_sync("sse", SSE.patch_elements(notification_list(), selector="#notification-list"))


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def unread_badge():
    """Badge showing unread count — replaced by SSE."""
    count = _unread_count()
    if count == 0:
        return Span(id="unread-badge")
    return Span(
        str(count),
        id="unread-badge",
        class_=(
            "inline-flex items-center justify-center w-6 h-6 rounded-full "
            "bg-red-500 text-white text-xs font-bold"
        ),
    )


def notification_item(n: Notification):
    """A single notification card."""
    cfg = KIND_CONFIG.get(n.kind, KIND_CONFIG["info"])
    read_cls = "opacity-60" if n.is_read else ""
    bg_cls = "bg-white" if not n.is_read else "bg-gray-50"

    return Div(
        # Icon
        Span(
            cfg["icon"],
            class_=(
                f"w-9 h-9 rounded-full {cfg['icon_cls']} "
                "text-sm font-bold flex items-center justify-center shrink-0"
            ),
        ),

        # Content
        Div(
            Div(
                Span(n.title, class_="text-sm font-semibold text-gray-900"),
                Span(
                    cfg["label"],
                    class_=f"text-[10px] px-1.5 py-0.5 rounded-full {cfg['icon_cls']} font-medium",
                ),
                class_="flex items-center gap-2",
            ),
            P(n.message, class_="text-sm text-gray-600 mt-0.5 leading-relaxed"),
            Span(_time_ago(n.created_at), class_="text-xs text-gray-400 mt-1 block"),
            class_="flex-1 min-w-0",
        ),

        # Actions
        Div(
            Button(
                "Mark read" if not n.is_read else "Unread",
                class_=(
                    "text-xs px-2.5 py-1 rounded-md font-medium transition-colors "
                    + ("text-blue-600 hover:bg-blue-50" if not n.is_read else "text-gray-500 hover:bg-gray-100")
                ),
                on_click=action(n.toggle_read),
            ),
            Button(
                "✕",
                class_=(
                    "text-xs w-7 h-7 rounded-md text-gray-400 hover:text-red-500 "
                    "hover:bg-red-50 transition-colors flex items-center justify-center"
                ),
                on_click=action(n.dismiss),
            ),
            class_="flex items-center gap-1 shrink-0",
        ),

        class_=(
            f"flex items-start gap-3 p-4 border-l-4 {cfg['border']} "
            f"{bg_cls} {read_cls} rounded-r-lg "
            "hover:shadow-sm transition-all"
        ),
    )


def notification_list():
    """Full notification list — replaced by SSE."""
    items = Notification.all()
    items.sort(key=lambda n: n.created_at, reverse=True)

    if not items:
        return Div(
            Div(
                Span(
                    "🔔",
                    class_="text-4xl block mb-3",
                ),
                P("No notifications", class_="text-gray-500 font-medium"),
                P(
                    "New notifications will appear here in real time",
                    class_="text-gray-400 text-sm mt-1",
                ),
                class_="text-center py-16",
            ),
            id="notification-list",
        )

    return Div(
        *[notification_item(n) for n in items],
        id="notification-list",
        class_="flex flex-col gap-2",
    )


def page_header():
    """Top bar with title, unread badge, and bulk actions."""
    return Div(
        Div(
            Div(
                H1("Notifications", class_="text-2xl font-bold text-gray-900"),
                unread_badge(),
                class_="flex items-center gap-3",
            ),
            P(
                "Real-time updates — new notifications arrive automatically via SSE",
                class_="text-sm text-gray-500 mt-1",
            ),
            class_="flex-1",
        ),
        Div(
            Button(
                "Mark all read",
                class_=(
                    "px-4 py-2 rounded-lg text-sm font-semibold text-blue-600 "
                    "bg-blue-50 hover:bg-blue-100 active:scale-95 transition-all"
                ),
                on_click=action(Notification.mark_all_read),
            ),
            Button(
                "Clear all",
                class_=(
                    "px-4 py-2 rounded-lg text-sm font-semibold text-gray-600 "
                    "bg-gray-100 hover:bg-gray-200 active:scale-95 transition-all"
                ),
                on_click=action(Notification.clear_all),
            ),
            class_="flex gap-2 items-start",
        ),
        class_="flex items-start justify-between gap-4 mb-6",
    )


def notifications_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            page_header(),

            # Notification list
            Div(
                notification_list(),
                class_=(
                    "bg-white rounded-2xl border border-gray-200 p-4 shadow-sm "
                    "min-h-[400px]"
                ),
            ),

            # Footer hint
            Div(
                P(
                    "New notifications generated every 5–10 seconds — "
                    "open multiple tabs to see real-time sync",
                    class_="text-xs text-gray-400 mt-6 text-center",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-2xl mx-auto px-6 py-12",
        ),
        title="Nitro Notifications",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

SEED_NOTIFICATIONS = [
    ("Deploy succeeded", "Production deploy #482 completed in 43s. All health checks passing.", "success"),
    ("New mention", "@nikola mentioned you in the Nitro roadmap discussion.", "mention"),
    ("High memory usage", "Server mem-03 at 92% — consider scaling or investigating leaks.", "warning"),
    ("Build failed", "CI pipeline for branch feat/sse-retry failed at test stage.", "error"),
    ("Welcome to Nitro", "This notification center demonstrates real-time SSE updates.", "info"),
]

# Background notification templates
BG_NOTIFICATIONS = [
    ("New comment", "Someone replied to your thread on component patterns.", "mention"),
    ("Disk space low", "Volume /data is at {pct}% capacity.", "warning"),
    ("Deploy started", "Staging deploy #{num} initiated by CI.", "info"),
    ("Test suite passed", "All {count} tests green on main branch.", "success"),
    ("Connection error", "Database replica db-{n} unreachable for {s}s.", "error"),
    ("PR approved", "Pull request #{num} approved — ready to merge.", "success"),
    ("Rate limit warning", "API rate limit at {pct}% for key ending ...{key}.", "warning"),
    ("New follower", "@user{n} started following the project.", "mention"),
    ("Scheduled backup", "Nightly backup completed — {size}MB archived.", "info"),
    ("Security alert", "Unusual login attempt from {ip}.", "error"),
]


def _create_seed():
    """Seed initial notifications."""
    base_ts = datetime.now(timezone.utc)
    for i, (title, msg, kind) in enumerate(SEED_NOTIFICATIONS):
        # Stagger creation times for realistic "time ago" display
        from datetime import timedelta
        ts = (base_ts - timedelta(minutes=i * 3)).strftime("%Y-%m-%dT%H:%M:%S")
        Notification(
            id=uuid.uuid4().hex[:8],
            title=title,
            message=msg,
            kind=kind,
            is_read=False,
            created_at=ts,
        ).save()


def _generate_random_notification():
    """Create a random notification from templates."""
    template = random.choice(BG_NOTIFICATIONS)
    title, msg_tmpl, kind = template

    msg = msg_tmpl.format(
        pct=random.randint(75, 98),
        num=random.randint(100, 999),
        count=random.randint(200, 600),
        n=random.randint(1, 50),
        s=random.randint(5, 30),
        key=uuid.uuid4().hex[:4],
        size=random.randint(50, 500),
        ip=f"{random.randint(100,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
    )

    Notification(
        id=uuid.uuid4().hex[:8],
        title=title,
        message=msg,
        kind=kind,
        is_read=False,
        created_at=_now_iso(),
    ).save()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroNotifications")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    Notification.repository().init_db()
    # Clear stale data and re-seed
    for n in Notification.all():
        n.delete()
    _create_seed()


@app.after_server_start
async def start_notification_loop(app):
    """Background task: generate random notifications every 5-10 seconds."""
    app.add_task(_notification_loop())


async def _notification_loop():
    """Periodically generate new notifications to demonstrate real-time push."""
    while True:
        await asyncio.sleep(random.uniform(5, 10))
        _generate_random_notification()
        _broadcast_all()


@app.get("/")
async def homepage(request: Request):
    return html(str(notifications_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8020, debug=True, auto_reload=True)
