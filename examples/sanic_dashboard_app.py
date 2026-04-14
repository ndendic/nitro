"""
Sanic Dashboard — Real-time Metrics with Auto-Refresh via SSE

Demonstrates:
  1. Background task pattern — server pushes updates without user action
  2. Multi-widget SSE updates — several DOM regions patched independently
  3. Mixed interaction — auto-refresh stats + user-triggered actions
  4. publish_sync + SSE.patch_elements API (not deprecated emit_elements)
  5. Sanic background task integration with Nitro events
  6. Rich dashboard UI with stat cards, activity log, and controls

Run:
    cd nitro && python examples/sanic_dashboard_app.py
    Then visit http://localhost:8007
"""
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
from rusty_tags import Div, H1, H2, P, Span, Button

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

class Activity(Entity, table=True):
    """An activity log entry."""
    __tablename__ = "dashboard_activity"
    message: str = ""
    category: str = "system"  # system, deploy, alert
    timestamp: str = ""

    @classmethod
    @post()
    def trigger_deploy(cls, request=None):
        """Simulate a deploy event."""
        entry = cls(
            id=uuid.uuid4().hex[:8],
            message=f"Deploy #{random.randint(100, 999)} started",
            category="deploy",
            timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
        )
        entry.save()
        _broadcast_all()
        return {"id": entry.id}

    @classmethod
    @post()
    def clear_log(cls, request=None):
        """Clear all activity entries."""
        for a in cls.all():
            a.delete()
        _broadcast_all()
        return {"cleared": True}


# ---------------------------------------------------------------------------
# Simulated metrics (in-memory, no entity needed)
# ---------------------------------------------------------------------------

_metrics = {
    "cpu": 0.0,
    "memory": 0.0,
    "requests_per_sec": 0,
    "uptime_hours": 0.0,
    "error_rate": 0.0,
    "active_connections": 0,
}


def _update_metrics():
    """Simulate metric changes."""
    _metrics["cpu"] = round(random.uniform(15, 85), 1)
    _metrics["memory"] = round(random.uniform(40, 75), 1)
    _metrics["requests_per_sec"] = random.randint(120, 450)
    _metrics["uptime_hours"] += round(random.uniform(0.01, 0.03), 2)
    _metrics["error_rate"] = round(random.uniform(0.1, 2.5), 2)
    _metrics["active_connections"] = random.randint(8, 64)


# ---------------------------------------------------------------------------
# Broadcast helpers
# ---------------------------------------------------------------------------

def _broadcast_all():
    """Push all dashboard widgets to connected clients."""
    publish_sync("sse", SSE.patch_elements(stat_cards(), selector="#stat-cards"))
    publish_sync("sse", SSE.patch_elements(activity_log(), selector="#activity-log"))


def _broadcast_metrics():
    """Push only metric cards (for background updates)."""
    publish_sync("sse", SSE.patch_elements(stat_cards(), selector="#stat-cards"))


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

CARD_COLORS = {
    "cpu": ("from-blue-500 to-blue-600", "bg-blue-100 text-blue-600"),
    "memory": ("from-violet-500 to-purple-600", "bg-violet-100 text-violet-600"),
    "rps": ("from-emerald-500 to-teal-600", "bg-emerald-100 text-emerald-600"),
    "uptime": ("from-amber-500 to-orange-600", "bg-amber-100 text-amber-600"),
    "errors": ("from-rose-500 to-red-600", "bg-rose-100 text-rose-600"),
    "conns": ("from-cyan-500 to-sky-600", "bg-cyan-100 text-cyan-600"),
}


def stat_card(label: str, value: str, unit: str, key: str):
    """A single metric card with colored accent."""
    _, badge_cls = CARD_COLORS.get(key, CARD_COLORS["cpu"])

    return Div(
        Div(
            Span(label, class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
            Span(unit, class_=f"text-xs px-2 py-0.5 rounded-full {badge_cls} font-medium"),
            class_="flex items-center justify-between mb-2",
        ),
        Span(
            value,
            class_="text-3xl font-bold tabular-nums text-gray-900",
        ),
        class_=(
            "bg-white rounded-xl border border-gray-200 p-5 "
            "shadow-sm hover:shadow-md transition-shadow"
        ),
    )


def stat_cards():
    """All metric cards — replaced by SSE on every update."""
    return Div(
        stat_card("CPU Usage", f"{_metrics['cpu']}%", "cpu", "cpu"),
        stat_card("Memory", f"{_metrics['memory']}%", "mem", "memory"),
        stat_card("Requests/sec", str(_metrics["requests_per_sec"]), "rps", "rps"),
        stat_card("Uptime", f"{_metrics['uptime_hours']:.1f}h", "hrs", "uptime"),
        stat_card("Error Rate", f"{_metrics['error_rate']}%", "err", "errors"),
        stat_card("Connections", str(_metrics["active_connections"]), "tcp", "conns"),
        id="stat-cards",
        class_="grid grid-cols-2 md:grid-cols-3 gap-4",
    )


def activity_entry(entry: Activity):
    """A single activity log row."""
    icon_map = {"system": "S", "deploy": "D", "alert": "!"}
    color_map = {
        "system": "bg-gray-100 text-gray-500",
        "deploy": "bg-blue-100 text-blue-600",
        "alert": "bg-red-100 text-red-600",
    }
    icon = icon_map.get(entry.category, "?")
    color = color_map.get(entry.category, "bg-gray-100 text-gray-500")

    return Div(
        Span(
            icon,
            class_=f"w-7 h-7 rounded-full {color} text-xs font-bold flex items-center justify-center shrink-0",
        ),
        Div(
            P(entry.message, class_="text-sm text-gray-800"),
            Span(entry.timestamp, class_="text-xs text-gray-400"),
            class_="flex-1",
        ),
        class_="flex items-center gap-3 py-2",
    )


def activity_log():
    """Activity log — replaced by SSE on changes."""
    entries = Activity.all()
    entries.sort(key=lambda a: a.id, reverse=True)
    entries = entries[:15]  # show last 15

    if not entries:
        return Div(
            P(
                "No activity yet. Metrics will auto-update.",
                class_="text-gray-400 text-center text-sm italic py-8",
            ),
            id="activity-log",
        )

    return Div(
        *[activity_entry(e) for e in entries],
        id="activity-log",
        class_="divide-y divide-gray-100",
    )


def dashboard_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Dashboard", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Real-time metrics — auto-refreshes every 3 seconds via SSE",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Stat cards (replaced by SSE)
            stat_cards(),

            # Controls + Activity section
            Div(
                # Section header + controls
                Div(
                    H2(
                        "Activity Log",
                        class_="text-sm font-bold uppercase tracking-wider text-gray-400",
                    ),
                    Div(
                        Button(
                            "Trigger Deploy",
                            class_=(
                                "px-4 py-2 rounded-lg text-sm font-semibold text-white "
                                "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                                "transition-all shadow-sm"
                            ),
                            on_click=action(Activity.trigger_deploy),
                        ),
                        Button(
                            "Clear Log",
                            class_=(
                                "px-4 py-2 rounded-lg text-sm font-semibold text-gray-600 "
                                "bg-gray-100 hover:bg-gray-200 active:scale-95 "
                                "transition-all"
                            ),
                            on_click=action(Activity.clear_log),
                        ),
                        class_="flex gap-2",
                    ),
                    class_="flex items-center justify-between mb-4",
                ),

                # Activity list (replaced by SSE)
                activity_log(),

                class_="mt-8 bg-white rounded-2xl border border-gray-200 p-6 shadow-sm",
            ),

            # Footer
            Div(
                P(
                    "Metrics update automatically — open in multiple tabs to see sync",
                    class_="text-xs text-gray-400 mt-6 text-center",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-4xl mx-auto px-6 py-12",
        ),
        title="Nitro Dashboard",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroDashboard")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    Activity.repository().init_db()
    _update_metrics()


@app.after_server_start
async def start_metrics_loop(app):
    """Background task: update metrics and broadcast every 3 seconds."""
    app.add_task(_metrics_loop())


async def _metrics_loop():
    """Continuously update simulated metrics."""
    while True:
        await asyncio.sleep(3)
        _update_metrics()
        # Log occasional system events
        if random.random() < 0.15:
            Activity(
                id=uuid.uuid4().hex[:8],
                message=random.choice([
                    f"CPU spike detected: {_metrics['cpu']}%",
                    f"New connection from 10.0.{random.randint(1,255)}.{random.randint(1,255)}",
                    f"Cache hit ratio: {random.randint(85, 99)}%",
                    f"GC pause: {random.randint(5, 50)}ms",
                    f"Request queue depth: {random.randint(0, 12)}",
                ]),
                category=random.choice(["system", "system", "alert"]),
                timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            ).save()
            _broadcast_all()
        else:
            _broadcast_metrics()


@app.get("/")
async def homepage(request: Request):
    return html(str(dashboard_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8007, debug=True, auto_reload=True)
