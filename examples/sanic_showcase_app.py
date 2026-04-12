"""
Sanic Showcase — Nitro Example Gallery & Launcher

A single-page index of all 19 Sanic + Nitro examples. Each card shows
the app name, description, port, patterns demonstrated, and a link to
launch it.  Serves as both a developer reference and a visual showcase
of Nitro's capabilities.

Run:
    cd nitro && python examples/sanic_showcase_app.py
    Then visit http://localhost:8000
"""

from sanic import Sanic, Request
from sanic.response import html

from nitro.html import Page
from rusty_tags import (
    Div, H1, H2, H3, P, Span, A, Ul, Li, Header, Main, Footer, Section,
)

# ---------------------------------------------------------------------------
# Example catalog
# ---------------------------------------------------------------------------

EXAMPLES = [
    {
        "name": "Counter",
        "port": 8001,
        "desc": "The canonical Nitro example — increment/decrement with SSE sync.",
        "tags": ["Beginner", "SSE", "Entity"],
        "color": "blue",
    },
    {
        "name": "Todo",
        "port": 8002,
        "desc": "Reactive CRUD with inline editing, completion toggle, and real-time sync.",
        "tags": ["CRUD", "SSE", "Entity"],
        "color": "green",
    },
    {
        "name": "Kanban",
        "port": 8003,
        "desc": "Drag-and-drop task board with columns, status cycling, and SSE.",
        "tags": ["Multi-Column", "State Machine", "SSE"],
        "color": "purple",
    },
    {
        "name": "Chat",
        "port": 8004,
        "desc": "Real-time multi-user chat with auto-scroll and presence indicators.",
        "tags": ["Real-time", "Multi-user", "SSE"],
        "color": "pink",
    },
    {
        "name": "Poll",
        "port": 8005,
        "desc": "Live voting with animated percentage bars and real-time results.",
        "tags": ["Voting", "Animation", "SSE"],
        "color": "amber",
    },
    {
        "name": "Notes",
        "port": 8006,
        "desc": "CRUD notes with edit-in-place, class-level save pattern, and SSE sync.",
        "tags": ["CRUD", "Edit-in-Place", "SSE"],
        "color": "teal",
    },
    {
        "name": "Dashboard",
        "port": 8007,
        "desc": "Real-time metrics with background auto-refresh — server push without user action.",
        "tags": ["Server Push", "Metrics", "Auto-refresh"],
        "color": "indigo",
    },
    {
        "name": "Tracker",
        "port": 8009,
        "desc": "Multi-entity project tracker with cross-entity relationships and cascading deletes.",
        "tags": ["Multi-Entity", "Relationships", "Layout"],
        "color": "orange",
    },
    {
        "name": "Budget",
        "port": 8010,
        "desc": "Expense tracker with computed aggregations, category budgets, and progress bars.",
        "tags": ["Aggregation", "Visualization", "Derived Data"],
        "color": "emerald",
    },
    {
        "name": "Contacts",
        "port": 8011,
        "desc": "Contacts/CRM with server-side search on keyup and tag-based filtering.",
        "tags": ["Search", "Filtering", "Multi-field"],
        "color": "cyan",
    },
    {
        "name": "Wizard",
        "port": 8012,
        "desc": "Multi-step form wizard with signal-driven navigation and review step.",
        "tags": ["Forms", "Client Signals", "data-show"],
        "color": "violet",
    },
    {
        "name": "Calendar",
        "port": 8013,
        "desc": "Month-grid calendar with event CRUD, color coding, and date filtering.",
        "tags": ["Calendar", "Grid", "Multi-region SSE"],
        "color": "rose",
    },
    {
        "name": "Pomodoro",
        "port": 8014,
        "desc": "Timer with per-second SSE countdown, state machine, and SVG progress ring.",
        "tags": ["Timer", "State Machine", "SVG"],
        "color": "red",
    },
    {
        "name": "Markdown",
        "port": 8015,
        "desc": "Editor with live preview via SSE, document switching, and server-side rendering.",
        "tags": ["Editor", "Preview", "Content Transform"],
        "color": "slate",
    },
    {
        "name": "Gallery",
        "port": 8016,
        "desc": "Image gallery with CSS grid, category + text search, and lightbox overlay.",
        "tags": ["Grid Layout", "Overlay", "Combined Filters"],
        "color": "fuchsia",
    },
    {
        "name": "Auth",
        "port": 8017,
        "desc": "Login & registration with sessions, auth-gated actions, and full-page swap.",
        "tags": ["Auth", "Sessions", "Page Swap"],
        "color": "sky",
    },
    {
        "name": "Data Table",
        "port": 8018,
        "desc": "Server-side sorting, pagination, search filtering — all working together.",
        "tags": ["Table", "Sort", "Pagination", "Search"],
        "color": "yellow",
    },
    {
        "name": "File Manager",
        "port": 8019,
        "desc": "Virtual file manager with folder navigation, breadcrumbs, and hierarchical CRUD.",
        "tags": ["Tree Structure", "Navigation", "Breadcrumbs", "Recursive"],
        "color": "lime",
    },
    {
        "name": "Notifications",
        "port": 8020,
        "desc": "Real-time notification center with type-coded alerts, read/unread state, and bulk ops.",
        "tags": ["Server Push", "State Toggle", "Bulk Ops", "Derived UI"],
        "color": "stone",
    },
]

# Tailwind color map for badges and accents
COLOR_MAP = {
    "blue": ("bg-blue-50 text-blue-700 border-blue-200", "bg-blue-500", "text-blue-600"),
    "green": ("bg-green-50 text-green-700 border-green-200", "bg-green-500", "text-green-600"),
    "purple": ("bg-purple-50 text-purple-700 border-purple-200", "bg-purple-500", "text-purple-600"),
    "pink": ("bg-pink-50 text-pink-700 border-pink-200", "bg-pink-500", "text-pink-600"),
    "amber": ("bg-amber-50 text-amber-700 border-amber-200", "bg-amber-500", "text-amber-600"),
    "teal": ("bg-teal-50 text-teal-700 border-teal-200", "bg-teal-500", "text-teal-600"),
    "indigo": ("bg-indigo-50 text-indigo-700 border-indigo-200", "bg-indigo-500", "text-indigo-600"),
    "orange": ("bg-orange-50 text-orange-700 border-orange-200", "bg-orange-500", "text-orange-600"),
    "emerald": ("bg-emerald-50 text-emerald-700 border-emerald-200", "bg-emerald-500", "text-emerald-600"),
    "cyan": ("bg-cyan-50 text-cyan-700 border-cyan-200", "bg-cyan-500", "text-cyan-600"),
    "violet": ("bg-violet-50 text-violet-700 border-violet-200", "bg-violet-500", "text-violet-600"),
    "rose": ("bg-rose-50 text-rose-700 border-rose-200", "bg-rose-500", "text-rose-600"),
    "red": ("bg-red-50 text-red-700 border-red-200", "bg-red-500", "text-red-600"),
    "slate": ("bg-slate-50 text-slate-700 border-slate-200", "bg-slate-500", "text-slate-600"),
    "fuchsia": ("bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200", "bg-fuchsia-500", "text-fuchsia-600"),
    "sky": ("bg-sky-50 text-sky-700 border-sky-200", "bg-sky-500", "text-sky-600"),
    "yellow": ("bg-yellow-50 text-yellow-700 border-yellow-200", "bg-yellow-500", "text-yellow-600"),
    "lime": ("bg-lime-50 text-lime-700 border-lime-200", "bg-lime-500", "text-lime-600"),
    "stone": ("bg-stone-50 text-stone-700 border-stone-200", "bg-stone-500", "text-stone-600"),
}


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def tag_badge(tag: str, color: str):
    badge_cls, _, _ = COLOR_MAP.get(color, COLOR_MAP["blue"])
    return Span(
        tag,
        class_=f"text-xs px-2 py-0.5 rounded-full font-medium border {badge_cls}",
    )


def example_card(ex: dict, index: int):
    _, accent, title_color = COLOR_MAP.get(ex["color"], COLOR_MAP["blue"])
    port = ex["port"]
    url = f"http://localhost:{port}"

    return Div(
        # Top accent bar
        Div(class_=f"h-1 {accent} rounded-t-xl"),

        Div(
            # Header: number + name
            Div(
                Span(
                    f"#{index + 1:02d}",
                    class_="text-xs font-bold text-gray-400 tracking-wider",
                ),
                H3(
                    ex["name"],
                    class_=f"text-lg font-bold {title_color}",
                ),
                class_="flex items-center gap-2",
            ),

            # Description
            P(
                ex["desc"],
                class_="text-sm text-gray-600 mt-2 leading-relaxed",
            ),

            # Tags
            Div(
                *[tag_badge(t, ex["color"]) for t in ex["tags"]],
                class_="flex flex-wrap gap-1.5 mt-3",
            ),

            # Footer: port + link
            Div(
                Span(
                    f":{port}",
                    class_="text-xs font-mono text-gray-400",
                ),
                A(
                    "Open →",
                    href=url,
                    target="_blank",
                    class_=(
                        "text-xs font-semibold text-white px-3 py-1.5 rounded-lg "
                        f"{accent} hover:opacity-90 transition-opacity"
                    ),
                ),
                class_="flex items-center justify-between mt-4 pt-3 border-t border-gray-100",
            ),

            class_="p-5",
        ),

        class_=(
            "bg-white rounded-xl border border-gray-200 shadow-sm "
            "hover:shadow-md hover:border-gray-300 transition-all duration-200"
        ),
    )


def hero():
    return Div(
        Div(
            H1(
                "Nitro Examples",
                class_="text-4xl font-bold text-gray-900",
            ),
            P(
                "19 real-world apps built with Nitro + Sanic + Datastar",
                class_="text-lg text-gray-500 mt-2",
            ),
            P(
                "Each example is a standalone single-file app. Run any example, "
                "then click its card to open it in a new tab.",
                class_="text-sm text-gray-400 mt-1",
            ),
            class_="text-center",
        ),

        # Stats bar
        Div(
            stat_pill("19", "Examples"),
            stat_pill("Sanic", "Framework"),
            stat_pill("SSE", "Real-time"),
            stat_pill("Tailwind", "Styling"),
            class_="flex justify-center gap-3 mt-6 flex-wrap",
        ),

        class_="pt-16 pb-10",
    )


def stat_pill(value: str, label: str):
    return Div(
        Span(value, class_="font-bold text-gray-900 text-sm"),
        Span(label, class_="text-gray-500 text-xs"),
        class_=(
            "flex items-center gap-1.5 px-3 py-1.5 "
            "bg-white rounded-full border border-gray-200 shadow-sm"
        ),
    )


def showcase_page():
    return Page(
        Div(
            hero(),

            # Card grid
            Div(
                *[example_card(ex, i) for i, ex in enumerate(EXAMPLES)],
                class_=(
                    "grid gap-5 px-6 pb-16 "
                    "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 "
                    "max-w-7xl mx-auto"
                ),
            ),

            # Footer
            Div(
                P(
                    "Built with Nitro — Python web development made simple.",
                    class_="text-xs text-gray-400 text-center py-8",
                ),
            ),

            class_="min-h-screen bg-gray-50/50",
        ),
        title="Nitro Examples — Showcase",
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroShowcase")


@app.get("/")
async def homepage(request: Request):
    return html(str(showcase_page()))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True, auto_reload=True)
