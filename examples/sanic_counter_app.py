"""
Sanic Counter — The Canonical Nitro Example

Demonstrates the full Nitro stack on Sanic:
  1. Entity with @post/@get decorated methods (auto-routing)
  2. configure_nitro(app) — 5 catch-all routes, zero boilerplate
  3. SSE streaming — real-time server-push via PubSub + Datastar
  4. publish_sync + SSE.patch_elements — server re-renders HTML, pushes patches to the DOM

The result: a reactive counter that updates instantly across all
connected browsers, with zero client-side JavaScript frameworks.

Run:
    cd nitro && python examples/sanic_counter_app.py
    Then visit http://localhost:8001
"""
import uuid

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, get, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, Span, Button, P

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

class Counter(Entity, table=True):
    """A simple counter with event-driven routing."""
    __tablename__ = "counter"
    value: int = 0

    @post()
    async def increment(self, request=None, amount: int = 1):
        self.value += amount
        self.save()
        publish_sync("sse", SSE.patch_elements(counter_display(self), selector="#counter-display"))
        return {"value": self.value}

    @post()
    async def decrement(self, request=None, amount: int = 1):
        self.value -= amount
        self.save()
        publish_sync("sse", SSE.patch_elements(counter_display(self), selector="#counter-display"))
        return {"value": self.value}

    @post()
    async def reset(self, request=None):
        self.value = 0
        self.save()
        publish_sync("sse", SSE.patch_elements(counter_display(self), selector="#counter-display"))
        return {"value": self.value}

    @get()
    def status(self):
        return {"id": self.id, "value": self.value}


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

def counter_display(counter: Counter):
    """The part of the UI that updates reactively."""
    return Div(
        Span(
            str(counter.value),
            class_="text-7xl font-bold tabular-nums tracking-tight "
                   "text-transparent bg-clip-text bg-gradient-to-r "
                   "from-blue-600 to-violet-600",
        ),
        id="counter-display",
        class_="flex items-center justify-center py-8",
    )


def counter_page(counter: Counter):
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1(
                    "Nitro Counter",
                    class_="text-3xl font-bold text-gray-900",
                ),
                P(
                    "Real-time server-push — no JavaScript frameworks",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Counter display (replaced by SSE patches)
            counter_display(counter),

            # Buttons
            Div(
                Button(
                    "- 1",
                    class_="px-6 py-3 rounded-xl font-semibold text-white "
                           "bg-red-500 hover:bg-red-600 active:scale-95 "
                           "transition-all shadow-sm",
                    on_click=action(counter.decrement),
                ),
                Button(
                    "Reset",
                    class_="px-6 py-3 rounded-xl font-semibold text-gray-700 "
                           "bg-gray-100 hover:bg-gray-200 active:scale-95 "
                           "transition-all",
                    on_click=action(counter.reset),
                ),
                Button(
                    "+ 1",
                    class_="px-6 py-3 rounded-xl font-semibold text-white "
                           "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                           "transition-all shadow-sm",
                    on_click=action(counter.increment),
                ),
                class_="flex items-center justify-center gap-4",
            ),

            # Info footer
            Div(
                P(f"Entity ID: {counter.id}", class_="text-xs text-gray-400"),
                P(
                    "Open in multiple tabs — they all sync",
                    class_="text-xs text-gray-400 mt-1",
                ),
                class_="text-center mt-10",
            ),

            # SSE connection — opens once when Datastar initializes
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-md mx-auto px-6 py-12",
        ),
        title="Nitro Counter",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroCounter")
configure_nitro(app)


@app.before_server_start
async def setup(app, loop=None):
    Counter.repository().init_db()
    if not Counter.get("main"):
        Counter(id="main", value=0).save()


@app.get("/")
async def homepage(request: Request):
    counter = Counter.get("main")
    return html(str(counter_page(counter)))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True, auto_reload=True)
