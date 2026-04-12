"""
Sanic Poll — Live Voting with Animated Percentage Bars

Demonstrates:
  1. Multi-entity design — Poll + Option entities with relationships
  2. Percentage bar calculation via entity methods
  3. Real-time vote tally via SSE broadcast (no page reload)
  4. publish_sync + SSE.patch_elements API (not deprecated emit_elements)
  5. Multi-tab / multi-user live sync
  6. Seed data pattern — creates a default poll on first run

Run:
    cd nitro && python examples/sanic_poll_app.py
    Then visit http://localhost:8005
"""
import uuid

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, get, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, H2, P, Span, Button, Input

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

class Poll(Entity, table=True):
    """A poll with a question and multiple options."""
    __tablename__ = "poll"
    question: str = ""

    @classmethod
    @post()
    def create_poll(cls, question: str = "", options_text: str = "", request=None):
        """Create a new poll with comma-separated options."""
        question = question.strip()
        if not question:
            return {"error": "empty question"}
        poll = cls(id=uuid.uuid4().hex[:8], question=question)
        poll.save()
        # Parse comma-separated options
        for label in options_text.split(","):
            label = label.strip()
            if label:
                Option(
                    id=uuid.uuid4().hex[:8],
                    poll_id=poll.id,
                    label=label,
                    votes=0,
                ).save()
        _broadcast_polls()
        publish_sync("sse", SSE.patch_signals({"question": "", "options_text": ""}))
        return {"id": poll.id}


class Option(Entity, table=True):
    """A voteable option belonging to a poll."""
    __tablename__ = "poll_option"
    poll_id: str = ""
    label: str = ""
    votes: int = 0

    @post()
    def vote(self, request=None):
        """Cast a vote for this option."""
        self.votes += 1
        self.save()
        _broadcast_polls()
        return {"id": self.id, "votes": self.votes}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_poll_options(poll_id: str) -> list:
    """Get all options for a poll, sorted by creation order."""
    return sorted(
        [o for o in Option.all() if o.poll_id == poll_id],
        key=lambda o: o.id,
    )


def _broadcast_polls():
    """Push updated polls HTML to all connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(polls_container(), selector="#polls"))
    publish_sync("sse", SSE.patch_elements(global_stats(), selector="#global-stats"))


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

def percentage_bar(option: Option, total_votes: int):
    """A single option with vote button and animated percentage bar."""
    pct = round(option.votes / total_votes * 100) if total_votes > 0 else 0
    bar_width = max(pct, 2)  # minimum visible width

    # Color gradient based on ranking
    bar_color = "bg-gradient-to-r from-violet-500 to-purple-600"

    return Div(
        # Label row: option name + vote count
        Div(
            Span(option.label, class_="text-sm font-semibold text-gray-800"),
            Span(
                f"{option.votes} vote{'s' if option.votes != 1 else ''} ({pct}%)",
                class_="text-xs text-gray-500 tabular-nums",
            ),
            class_="flex items-center justify-between mb-1.5",
        ),
        # Bar + vote button row
        Div(
            # Bar track
            Div(
                # Bar fill
                Div(
                    class_=f"{bar_color} h-full rounded-full transition-all duration-500",
                    style=f"width: {bar_width}%",
                ),
                class_="flex-1 h-8 bg-gray-100 rounded-full overflow-hidden",
            ),
            # Vote button
            Button(
                "Vote",
                class_=(
                    "px-4 py-1.5 rounded-lg text-sm font-semibold text-white "
                    "bg-violet-500 hover:bg-violet-600 active:scale-95 "
                    "transition-all shadow-sm shrink-0"
                ),
                on_click=action(option.vote),
            ),
            class_="flex items-center gap-3",
        ),
        class_="mb-3",
    )


def poll_card(poll: Poll):
    """A single poll with its question and option bars."""
    options = get_poll_options(poll.id)
    total_votes = sum(o.votes for o in options)

    return Div(
        # Poll question
        H2(poll.question, class_="text-lg font-bold text-gray-900 mb-4"),
        # Options with bars
        *(percentage_bar(o, total_votes) for o in options),
        # Vote total
        Div(
            Span(
                f"{total_votes} total vote{'s' if total_votes != 1 else ''}",
                class_="text-xs text-gray-400",
            ),
            class_="text-right mt-2 pt-2 border-t border-gray-100",
        ),
        class_=(
            "bg-white rounded-2xl border border-gray-200 p-6 "
            "shadow-sm hover:shadow-md transition-shadow"
        ),
    )


def polls_container():
    """All polls — replaced by SSE on every vote."""
    polls = Poll.all()
    polls.sort(key=lambda p: p.id)

    if not polls:
        return Div(
            P(
                "No polls yet. Create one below!",
                class_="text-gray-400 text-center text-sm italic py-12",
            ),
            id="polls",
            class_="flex flex-col gap-6",
        )

    return Div(
        *(poll_card(p) for p in polls),
        id="polls",
        class_="flex flex-col gap-6",
    )


def global_stats():
    """Global stats — replaced by SSE on every vote."""
    polls = Poll.all()
    total_polls = len(polls)
    total_votes = sum(o.votes for o in Option.all())

    if total_polls == 0:
        return Div(id="global-stats")

    return Div(
        Span(f"{total_polls} poll{'s' if total_polls != 1 else ''}", class_="text-sm text-gray-500"),
        Span("\u00b7", class_="text-gray-300 mx-2"),
        Span(f"{total_votes} total vote{'s' if total_votes != 1 else ''}", class_="text-sm text-violet-500"),
        id="global-stats",
        class_="flex items-center justify-center py-3",
    )


def poll_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Poll", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Live voting with real-time percentage bars \u2014 open in multiple tabs to see sync",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Polls area (replaced by SSE)
            polls_container(),

            # Global stats (replaced by SSE)
            global_stats(),

            # Create new poll form
            Div(
                H2("Create a Poll", class_="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4"),
                Div(
                    # Question
                    Div(
                        Span("Question", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Input(
                            type="text",
                            placeholder="What should we decide?",
                            bind="question",
                            class_=(
                                "w-full px-4 py-3 rounded-xl border border-gray-200 "
                                "bg-gray-50 focus:bg-white focus:border-violet-400 "
                                "focus:ring-2 focus:ring-violet-100 outline-none "
                                "transition-all text-gray-700 placeholder-gray-400"
                            ),
                        ),
                        class_="flex flex-col gap-1",
                    ),
                    # Options
                    Div(
                        Span("Options", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Input(
                            type="text",
                            placeholder="Option A, Option B, Option C",
                            bind="options_text",
                            on_keys_enter=action(Poll.create_poll),
                            class_=(
                                "w-full px-4 py-3 rounded-xl border border-gray-200 "
                                "bg-gray-50 focus:bg-white focus:border-violet-400 "
                                "focus:ring-2 focus:ring-violet-100 outline-none "
                                "transition-all text-gray-700 placeholder-gray-400"
                            ),
                        ),
                        class_="flex flex-col gap-1",
                    ),
                    # Submit
                    Button(
                        "Create Poll",
                        class_=(
                            "px-6 py-3 rounded-xl font-semibold text-white "
                            "bg-violet-500 hover:bg-violet-600 active:scale-95 "
                            "transition-all shadow-sm self-end"
                        ),
                        on_click=action(Poll.create_poll),
                    ),
                    class_="flex flex-col gap-4",
                    data_signals="{question: '', options_text: ''}",
                ),
                class_="bg-gray-50 rounded-2xl border border-gray-200 p-6 mt-8",
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-2xl mx-auto px-6 py-12",
        ),
        title="Nitro Poll",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroPoll")
configure_nitro(app)


@app.before_server_start
async def setup(app, loop=None):
    Poll.repository().init_db()
    Option.repository().init_db()
    # Seed a default poll if none exists
    if not Poll.all():
        poll = Poll(id="default", question="What's the best Python web framework philosophy?")
        poll.save()
        for i, label in enumerate(["Batteries included", "Micro & composable", "Event-driven", "Convention over config"]):
            Option(id=f"opt{i}", poll_id="default", label=label, votes=0).save()


@app.get("/")
async def homepage(request: Request):
    return html(str(poll_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8005, debug=True, auto_reload=True)
