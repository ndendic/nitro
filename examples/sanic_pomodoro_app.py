"""
Sanic Pomodoro Timer — Server-Push Countdown via SSE

Demonstrates:
  1. Per-second SSE countdown — server ticks the timer and pushes every second
  2. State machine pattern — entity transitions: idle -> work -> break -> idle
  3. Conditional UI — buttons and display change based on current state
  4. Background async task — asyncio loop reads/writes entity state, broadcasts ticks
  5. Combined server-push + user actions — timer ticks automatically, user controls flow

New patterns vs. prior examples:
  - Dashboard pushes metrics every 3s; this pushes every 1s with countdown logic
  - State determines which actions are valid (can't pause when idle, can't start when running)
  - Visual state changes: color palette shifts with timer state

Run:
    cd nitro && python examples/sanic_pomodoro_app.py
    Then visit http://localhost:8014
"""
import uuid
import asyncio

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, H2, P, Span, Button, HtmlString

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

WORK_DURATION = 25 * 60   # 25 minutes in seconds
BREAK_DURATION = 5 * 60   # 5 minutes in seconds

class Pomodoro(Entity, table=True):
    """A pomodoro timer with state machine transitions."""
    __tablename__ = "pomodoro"

    state: str = "idle"           # idle | work | break | paused
    remaining: int = WORK_DURATION  # seconds left
    paused_from: str = ""         # which state was paused (work or break)
    completed_count: int = 0      # total completed work sessions

    @post()
    async def start_work(self, request=None):
        """Begin a work session."""
        self.state = "work"
        self.remaining = WORK_DURATION
        self.paused_from = ""
        self.save()
        _broadcast()
        return {"state": self.state}

    @post()
    async def start_break(self, request=None):
        """Begin a break session."""
        self.state = "break"
        self.remaining = BREAK_DURATION
        self.paused_from = ""
        self.save()
        _broadcast()
        return {"state": self.state}

    @post()
    async def pause(self, request=None):
        """Pause the current timer."""
        if self.state in ("work", "break"):
            self.paused_from = self.state
            self.state = "paused"
            self.save()
            _broadcast()
        return {"state": self.state}

    @post()
    async def resume(self, request=None):
        """Resume a paused timer."""
        if self.state == "paused" and self.paused_from:
            self.state = self.paused_from
            self.paused_from = ""
            self.save()
            _broadcast()
        return {"state": self.state}

    @post()
    async def reset(self, request=None):
        """Reset to idle."""
        self.state = "idle"
        self.remaining = WORK_DURATION
        self.paused_from = ""
        self.save()
        _broadcast()
        return {"state": self.state}


# ---------------------------------------------------------------------------
# Broadcast
# ---------------------------------------------------------------------------

def _broadcast():
    """Push all dynamic regions to connected clients."""
    timer = Pomodoro.get("main")
    publish_sync("sse", SSE.patch_elements(timer_display(timer), selector="#timer-display"))
    publish_sync("sse", SSE.patch_elements(timer_controls(timer), selector="#timer-controls"))
    publish_sync("sse", SSE.patch_elements(session_stats(timer), selector="#session-stats"))


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

STATE_COLORS = {
    "idle":   {"ring": "text-gray-300",   "bg": "from-gray-50 to-gray-100",  "accent": "text-gray-500"},
    "work":   {"ring": "text-rose-500",   "bg": "from-rose-50 to-orange-50", "accent": "text-rose-600"},
    "break":  {"ring": "text-emerald-500","bg": "from-emerald-50 to-teal-50","accent": "text-emerald-600"},
    "paused": {"ring": "text-amber-400",  "bg": "from-amber-50 to-yellow-50","accent": "text-amber-600"},
}

STATE_LABELS = {
    "idle": "Ready",
    "work": "Focus Time",
    "break": "Break Time",
    "paused": "Paused",
}


def format_time(seconds: int) -> str:
    """Format seconds as MM:SS."""
    m, s = divmod(max(0, seconds), 60)
    return f"{m:02d}:{s:02d}"


def timer_display(timer: Pomodoro):
    """The circular timer display — replaced by SSE every second."""
    colors = STATE_COLORS[timer.state]
    progress = 0.0
    total = WORK_DURATION if timer.state in ("work", "paused") and timer.paused_from != "break" else BREAK_DURATION
    if timer.state == "paused":
        total = WORK_DURATION if timer.paused_from == "work" else BREAK_DURATION
    if timer.state != "idle":
        progress = 1.0 - (timer.remaining / total)

    # SVG circular progress ring
    radius = 90
    circumference = 2 * 3.14159 * radius
    offset = circumference * (1.0 - progress)

    svg = (
        f'<svg viewBox="0 0 200 200" class="w-64 h-64">'
        f'<circle cx="100" cy="100" r="{radius}" fill="none" '
        f'stroke="currentColor" stroke-width="6" class="text-gray-200" />'
        f'<circle cx="100" cy="100" r="{radius}" fill="none" '
        f'stroke="currentColor" stroke-width="6" class="{colors["ring"]}" '
        f'stroke-dasharray="{circumference}" stroke-dashoffset="{offset:.1f}" '
        f'stroke-linecap="round" transform="rotate(-90 100 100)" '
        f'style="transition: stroke-dashoffset 0.5s ease" />'
        f'</svg>'
    )

    return Div(
        # Timer ring with time overlay
        Div(
            HtmlString(svg),
            Div(
                Span(
                    format_time(timer.remaining),
                    class_=f"text-5xl font-bold tabular-nums tracking-tight {colors['accent']}",
                ),
                Span(
                    STATE_LABELS[timer.state],
                    class_=f"text-sm font-medium uppercase tracking-widest mt-1 {colors['accent']}",
                ),
                class_="absolute inset-0 flex flex-col items-center justify-center",
            ),
            class_="relative inline-block",
        ),
        id="timer-display",
        class_="flex items-center justify-center py-6",
    )


def timer_controls(timer: Pomodoro):
    """Action buttons — change based on current state."""
    buttons = []

    if timer.state == "idle":
        buttons.append(
            Button(
                "Start Focus",
                class_=(
                    "px-8 py-3 rounded-xl font-semibold text-white "
                    "bg-rose-500 hover:bg-rose-600 active:scale-95 "
                    "transition-all shadow-md shadow-rose-200"
                ),
                on_click=action(timer.start_work),
            )
        )
    elif timer.state in ("work", "break"):
        buttons.append(
            Button(
                "Pause",
                class_=(
                    "px-6 py-3 rounded-xl font-semibold text-amber-700 "
                    "bg-amber-100 hover:bg-amber-200 active:scale-95 "
                    "transition-all"
                ),
                on_click=action(timer.pause),
            )
        )
    elif timer.state == "paused":
        buttons.append(
            Button(
                "Resume",
                class_=(
                    "px-6 py-3 rounded-xl font-semibold text-white "
                    "bg-emerald-500 hover:bg-emerald-600 active:scale-95 "
                    "transition-all shadow-md shadow-emerald-200"
                ),
                on_click=action(timer.resume),
            )
        )

    # Always show reset unless idle
    if timer.state != "idle":
        buttons.append(
            Button(
                "Reset",
                class_=(
                    "px-6 py-3 rounded-xl font-semibold text-gray-600 "
                    "bg-gray-100 hover:bg-gray-200 active:scale-95 "
                    "transition-all"
                ),
                on_click=action(timer.reset),
            )
        )

    # Quick start break (only when idle and have completed at least one session)
    if timer.state == "idle" and timer.completed_count > 0:
        buttons.append(
            Button(
                "Take Break",
                class_=(
                    "px-6 py-3 rounded-xl font-semibold text-emerald-700 "
                    "bg-emerald-100 hover:bg-emerald-200 active:scale-95 "
                    "transition-all"
                ),
                on_click=action(timer.start_break),
            )
        )

    return Div(
        *buttons,
        id="timer-controls",
        class_="flex items-center justify-center gap-3",
    )


def session_stats(timer: Pomodoro):
    """Completed session counter."""
    tomatoes = []
    for i in range(min(timer.completed_count, 8)):
        tomatoes.append(
            Span(
                class_="w-3 h-3 rounded-full bg-rose-400 inline-block",
            )
        )
    # Empty slots for remaining (show up to 8)
    for i in range(min(timer.completed_count, 8), 8):
        tomatoes.append(
            Span(
                class_="w-3 h-3 rounded-full bg-gray-200 inline-block",
            )
        )

    count_text = f"{timer.completed_count} session{'s' if timer.completed_count != 1 else ''} completed"

    return Div(
        Div(
            *tomatoes,
            class_="flex items-center gap-1.5",
        ),
        P(count_text, class_="text-xs text-gray-400 mt-1.5"),
        id="session-stats",
        class_="flex flex-col items-center mt-6",
    )


def pomodoro_page(timer: Pomodoro):
    """Full page layout."""
    colors = STATE_COLORS[timer.state]

    return Page(
        Div(
            # Header
            Div(
                H1(
                    "Pomodoro Timer",
                    class_="text-3xl font-bold text-gray-900",
                ),
                P(
                    "Server-push countdown — timer ticks via SSE every second",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-6",
            ),

            # Timer card
            Div(
                timer_display(timer),
                timer_controls(timer),
                session_stats(timer),
                class_=(
                    f"bg-gradient-to-b {colors['bg']} "
                    "rounded-3xl border border-gray-200 p-8 "
                    "shadow-sm transition-colors duration-500"
                ),
            ),

            # Settings info
            Div(
                Div(
                    _setting_pill("Focus", "25 min"),
                    _setting_pill("Break", "5 min"),
                    _setting_pill("Goal", "8 sessions"),
                    class_="flex items-center justify-center gap-3",
                ),
                class_="mt-6",
            ),

            # Footer
            Div(
                P(
                    "Open in multiple tabs — timer syncs across all browsers",
                    class_="text-xs text-gray-400 mt-8 text-center",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-md mx-auto px-6 py-12",
        ),
        title="Pomodoro Timer",
        datastar=True,
        tailwind4=True,
    )


def _setting_pill(label: str, value: str):
    """Small info pill for settings display."""
    return Span(
        f"{label}: {value}",
        class_=(
            "text-xs px-3 py-1 rounded-full "
            "bg-white border border-gray-200 text-gray-500 font-medium"
        ),
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroPomodoro")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    Pomodoro.repository().init_db()
    if not Pomodoro.get("main"):
        Pomodoro(id="main", state="idle", remaining=WORK_DURATION).save()


@app.after_server_start
async def start_ticker(app):
    """Background task: tick the timer every second when active."""
    app.add_task(_tick_loop())


async def _tick_loop():
    """Countdown loop — ticks every second when timer is running."""
    while True:
        await asyncio.sleep(1)
        timer = Pomodoro.get("main")
        if not timer or timer.state not in ("work", "break"):
            continue

        timer.remaining -= 1

        if timer.remaining <= 0:
            # Timer expired — transition state
            if timer.state == "work":
                timer.completed_count += 1
                timer.state = "break"
                timer.remaining = BREAK_DURATION
            elif timer.state == "break":
                timer.state = "idle"
                timer.remaining = WORK_DURATION

            timer.paused_from = ""
            timer.save()
            _broadcast()
        else:
            timer.save()
            # Only push the timer display (not controls) for efficiency
            publish_sync("sse", SSE.patch_elements(
                timer_display(timer), selector="#timer-display"
            ))


@app.get("/")
async def homepage(request: Request):
    timer = Pomodoro.get("main")
    return html(str(pomodoro_page(timer)))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8014, debug=True, auto_reload=True)
