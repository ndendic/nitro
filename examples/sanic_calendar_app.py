"""
Sanic Calendar — Date Grid Navigation & Event Scheduling

Demonstrates:
  1. Calendar grid — 7-column month view with proper day alignment
  2. Month navigation — prev/next month via server-side state + SSE re-render
  3. Event CRUD — add events with title, date, time, color
  4. Date-based filtering — events shown on their calendar day cells
  5. Color-coded events — visual category distinction in grid cells

New patterns:
  - Python calendar module for grid computation
  - Server-side view state (current month/year) separate from domain data
  - Multi-region SSE updates (calendar grid + event list + nav header)
  - Dense grid layout with overflow handling

Run:
    cd nitro && python examples/sanic_calendar_app.py
    Then visit http://localhost:8013
"""
import uuid
import calendar
from datetime import date, datetime

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, H2, H3, P, Span, Button, Input, Select, Option

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

COLORS = {
    "blue": ("Blue", "bg-blue-500", "bg-blue-100 text-blue-700 border-blue-200"),
    "green": ("Green", "bg-green-500", "bg-green-100 text-green-700 border-green-200"),
    "red": ("Red", "bg-red-500", "bg-red-100 text-red-700 border-red-200"),
    "amber": ("Amber", "bg-amber-500", "bg-amber-100 text-amber-700 border-amber-200"),
    "violet": ("Violet", "bg-violet-500", "bg-violet-100 text-violet-700 border-violet-200"),
}

# Server-side view state
_view_year = date.today().year
_view_month = date.today().month


class CalendarEvent(Entity, table=True):
    """A calendar event with title, date, time, and color."""
    __tablename__ = "calendar_event"
    title: str = ""
    event_date: str = ""      # YYYY-MM-DD
    event_time: str = ""      # HH:MM (optional)
    color: str = "blue"

    @classmethod
    @post()
    def add(cls, title: str = "", event_date: str = "",
            event_time: str = "", color: str = "blue", request=None):
        """Add a new calendar event."""
        title = title.strip()
        if not title or not event_date:
            return {"error": "title and date required"}
        evt = cls(
            id=uuid.uuid4().hex[:8],
            title=title,
            event_date=event_date,
            event_time=event_time.strip(),
            color=color if color in COLORS else "blue",
        )
        evt.save()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({
            "add_title": "", "add_time": "", "add_color": "blue",
        }))
        return {"id": evt.id}

    @post()
    def remove(self, request=None):
        """Delete this event."""
        self.delete()
        _broadcast_all()
        return {"deleted": True}

    @classmethod
    @post()
    def nav(cls, direction: str = "next", request=None):
        """Navigate calendar: 'next', 'prev', or 'today'."""
        global _view_year, _view_month
        if direction == "next":
            if _view_month == 12:
                _view_month = 1
                _view_year += 1
            else:
                _view_month += 1
        elif direction == "prev":
            if _view_month == 1:
                _view_month = 12
                _view_year -= 1
            else:
                _view_month -= 1
        elif direction == "today":
            _view_year = date.today().year
            _view_month = date.today().month
        _broadcast_all()
        return {"year": _view_year, "month": _view_month}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _events_for_month(year: int, month: int) -> dict[str, list]:
    """Return {day_number: [events]} for the given month."""
    prefix = f"{year:04d}-{month:02d}-"
    all_events = CalendarEvent.all()
    by_day: dict[str, list] = {}
    for evt in all_events:
        if evt.event_date.startswith(prefix):
            day = evt.event_date[8:10]  # DD part
            by_day.setdefault(day, []).append(evt)
    # Sort each day's events by time
    for day in by_day:
        by_day[day].sort(key=lambda e: e.event_time or "99:99")
    return by_day


def _broadcast_all():
    """Push all dynamic regions to connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(calendar_header(), selector="#calendar-header"))
    publish_sync("sse", SSE.patch_elements(calendar_grid(), selector="#calendar-grid"))
    publish_sync("sse", SSE.patch_elements(upcoming_events(), selector="#upcoming-events"))


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def calendar_header():
    """Month/year display with prev/next navigation — replaced by SSE."""
    today = date.today()
    is_current = _view_year == today.year and _view_month == today.month

    return Div(
        Div(
            Button(
                "\u2190",
                on_click="$direction = 'prev'; " + action(CalendarEvent.nav),
                class_=(
                    "w-9 h-9 rounded-lg flex items-center justify-center "
                    "text-gray-500 hover:bg-gray-100 hover:text-gray-700 "
                    "transition-all text-lg font-medium"
                ),
            ),
            Div(
                H2(
                    f"{MONTH_NAMES[_view_month]} {_view_year}",
                    class_="text-xl font-bold text-gray-900",
                ),
                class_="flex-1 text-center",
            ),
            Button(
                "\u2192",
                on_click="$direction = 'next'; " + action(CalendarEvent.nav),
                class_=(
                    "w-9 h-9 rounded-lg flex items-center justify-center "
                    "text-gray-500 hover:bg-gray-100 hover:text-gray-700 "
                    "transition-all text-lg font-medium"
                ),
            ),
            class_="flex items-center gap-2",
        ),
        # Today button (only shown if not viewing current month)
        Div(
            Button(
                "Today",
                on_click="$direction = 'today'; " + action(CalendarEvent.nav),
                class_=(
                    "px-3 py-1 rounded-lg text-xs font-semibold "
                    "bg-blue-50 text-blue-600 hover:bg-blue-100 transition-all"
                ),
            ),
            class_="flex justify-center mt-2",
        ) if not is_current else Span(""),
        id="calendar-header",
    )


def event_dot(evt):
    """A small event indicator inside a calendar day cell."""
    _, _, badge_cls = COLORS.get(evt.color, COLORS["blue"])
    time_str = evt.event_time if evt.event_time else ""
    label = f"{time_str} {evt.title}".strip()

    return Div(
        Span(label, class_="truncate text-[10px] leading-tight"),
        Button(
            "\u00d7",
            title="Delete event",
            on_click=action(evt.remove),
            class_=(
                "w-4 h-4 rounded text-[10px] leading-none shrink-0 "
                "opacity-0 group-hover/evt:opacity-100 "
                "hover:bg-red-200 hover:text-red-600 transition-all "
                "flex items-center justify-center"
            ),
        ),
        class_=f"group/evt flex items-center gap-0.5 px-1 py-0.5 rounded border {badge_cls} cursor-default",
    )


def day_cell(day_num: int, events: list, is_today: bool, is_current_month: bool):
    """A single day cell in the calendar grid."""
    today_ring = "ring-2 ring-blue-400 ring-inset" if is_today else ""
    text_color = "text-gray-900" if is_current_month else "text-gray-300"
    bg = "bg-blue-50/50" if is_today else "bg-white"

    event_dots = [event_dot(e) for e in events[:3]]
    overflow = len(events) - 3
    if overflow > 0:
        event_dots.append(
            Span(f"+{overflow} more", class_="text-[10px] text-gray-400 italic pl-1")
        )

    return Div(
        # Day number
        Span(
            str(day_num),
            class_=f"text-sm font-medium {text_color}",
        ),
        # Events
        Div(
            *event_dots,
            class_="flex flex-col gap-0.5 mt-1 min-h-0 overflow-hidden",
        ) if event_dots else Span(""),
        class_=(
            f"min-h-[5rem] p-1.5 border-b border-r border-gray-100 "
            f"{bg} {today_ring} hover:bg-gray-50/80 transition-colors"
        ),
    )


def empty_cell():
    """An empty cell for padding at the start/end of the month grid."""
    return Div(class_="min-h-[5rem] p-1.5 border-b border-r border-gray-100 bg-gray-50/30")


def calendar_grid():
    """The 7-column calendar grid for the current view month — replaced by SSE."""
    today = date.today()
    year, month = _view_year, _view_month

    # Get calendar data
    cal = calendar.monthcalendar(year, month)
    events_by_day = _events_for_month(year, month)

    # Weekday header
    header_cells = [
        Div(
            Span(day, class_="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
            class_="p-2 text-center border-b border-gray-200 bg-gray-50",
        )
        for day in WEEKDAYS
    ]

    # Day cells
    day_cells = []
    for week in cal:
        for day_num in week:
            if day_num == 0:
                day_cells.append(empty_cell())
            else:
                day_str = f"{day_num:02d}"
                day_events = events_by_day.get(day_str, [])
                is_today = (year == today.year and month == today.month and day_num == today.day)
                day_cells.append(day_cell(day_num, day_events, is_today, True))

    return Div(
        # Header row
        Div(
            *header_cells,
            class_="grid grid-cols-7",
        ),
        # Day grid
        Div(
            *day_cells,
            class_="grid grid-cols-7",
        ),
        id="calendar-grid",
        class_="border-t border-l border-gray-200 rounded-xl overflow-hidden bg-white shadow-sm",
    )


def upcoming_events():
    """Sidebar list of upcoming events — replaced by SSE."""
    today = date.today()
    all_events = CalendarEvent.all()

    # Get events from today onward, sorted by date+time
    upcoming = sorted(
        [e for e in all_events if e.event_date >= today.isoformat()],
        key=lambda e: (e.event_date, e.event_time or "99:99"),
    )[:8]

    if not upcoming:
        return Div(
            H3("Upcoming", class_="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3"),
            P("No upcoming events.", class_="text-sm text-gray-400 italic"),
            id="upcoming-events",
        )

    items = []
    for evt in upcoming:
        _, bar_color, badge_cls = COLORS.get(evt.color, COLORS["blue"])
        # Parse date for display
        try:
            d = date.fromisoformat(evt.event_date)
            date_str = d.strftime("%b %d")
        except ValueError:
            date_str = evt.event_date

        items.append(
            Div(
                # Color bar
                Div(class_=f"w-1 rounded-full shrink-0 self-stretch {bar_color}"),
                Div(
                    P(evt.title, class_="text-sm font-medium text-gray-800 truncate"),
                    Div(
                        Span(date_str, class_="text-xs text-gray-500"),
                        Span(evt.event_time, class_="text-xs text-gray-400") if evt.event_time else Span(""),
                        class_="flex items-center gap-2",
                    ),
                    class_="flex-1 min-w-0",
                ),
                Button(
                    "\u00d7",
                    title="Delete event",
                    on_click=action(evt.remove),
                    class_=(
                        "w-6 h-6 rounded text-gray-300 hover:text-red-500 "
                        "hover:bg-red-50 transition-all text-sm leading-none "
                        "flex items-center justify-center shrink-0 "
                        "opacity-0 group-hover:opacity-100"
                    ),
                ),
                class_="group flex items-center gap-3 py-2 px-1 rounded-lg hover:bg-gray-50 transition-colors",
            )
        )

    return Div(
        H3("Upcoming", class_="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3"),
        Div(*items, class_="flex flex-col"),
        id="upcoming-events",
    )


def add_event_form():
    """Compact form to add a new event."""
    today_str = date.today().isoformat()

    return Div(
        H3("New Event", class_="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3"),
        Div(
            Input(
                type="text",
                placeholder="Event title *",
                bind="add_title",
                class_=(
                    "w-full px-3 py-2 rounded-lg border border-gray-200 "
                    "bg-gray-50 focus:bg-white focus:border-blue-400 "
                    "focus:ring-2 focus:ring-blue-100 outline-none "
                    "transition-all text-sm text-gray-700 placeholder-gray-400"
                ),
            ),
            Div(
                Input(
                    type="date",
                    bind="add_date",
                    class_=(
                        "flex-1 px-3 py-2 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm text-gray-700"
                    ),
                ),
                Input(
                    type="time",
                    bind="add_time",
                    class_=(
                        "w-28 px-3 py-2 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm text-gray-700"
                    ),
                ),
                class_="flex gap-2",
            ),
            Div(
                Select(
                    *[Option(COLORS[c][0], value=c) for c in COLORS],
                    bind="add_color",
                    class_=(
                        "flex-1 px-3 py-2 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-sm text-gray-700"
                    ),
                ),
                Button(
                    "Add Event",
                    class_=(
                        "px-4 py-2 rounded-lg text-sm font-semibold text-white "
                        "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                        "transition-all shadow-sm shrink-0"
                    ),
                    on_click=action(CalendarEvent.add),
                ),
                class_="flex gap-2",
            ),
            class_="flex flex-col gap-2",
        ),
        class_="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm",
    )


def calendar_page():
    """Full page layout."""
    today_str = date.today().isoformat()

    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Calendar", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Month navigation, event scheduling, real-time sync",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Main layout: calendar + sidebar
            Div(
                # Left: calendar
                Div(
                    calendar_header(),
                    Div(class_="h-4"),
                    calendar_grid(),
                    class_="flex-1 min-w-0",
                ),

                # Right: sidebar
                Div(
                    add_event_form(),
                    Div(class_="h-4"),
                    Div(
                        upcoming_events(),
                        class_="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm",
                    ),
                    class_="w-72 shrink-0 flex flex-col",
                ),

                class_="flex gap-6",
            ),

            # Footer
            Div(
                P(
                    "Open in multiple tabs \u2014 events sync in real time",
                    class_="text-xs text-gray-400 text-center mt-8",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-6xl mx-auto px-6 py-12",
            data_signals=(
                "{ direction: 'next', "
                f"add_title: '', add_date: '{today_str}', add_time: '', add_color: 'blue' }}"
            ),
        ),
        title="Nitro Calendar",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroCalendar")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    CalendarEvent.repository().init_db()
    if not CalendarEvent.all():
        today = date.today()
        seed_events = [
            ("Team standup", today.isoformat(), "09:00", "blue"),
            ("Lunch with Alex", today.isoformat(), "12:30", "green"),
            ("Code review", today.isoformat(), "15:00", "violet"),
            ("Dentist appointment", date(today.year, today.month, min(today.day + 2, 28)).isoformat(), "10:00", "red"),
            ("Project deadline", date(today.year, today.month, min(today.day + 5, 28)).isoformat(), "", "amber"),
            ("Birthday party", date(today.year, today.month, min(today.day + 7, 28)).isoformat(), "18:00", "green"),
        ]
        for title, event_date, event_time, color in seed_events:
            CalendarEvent(
                id=uuid.uuid4().hex[:8],
                title=title,
                event_date=event_date,
                event_time=event_time,
                color=color,
            ).save()


@app.get("/")
async def homepage(request: Request):
    return html(str(calendar_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8013, debug=True, auto_reload=True)
