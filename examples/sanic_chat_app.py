"""
Sanic Chat — Real-time multi-user chat with Nitro + Datastar SSE

Demonstrates:
  1. Per-user identity with nickname signals
  2. Message entity with timestamp + author
  3. Append-only message list via SSE broadcast
  4. publish_sync + SSE.patch_elements API (not deprecated emit_elements)
  5. Real-time multi-tab/multi-user sync
  6. Signal-driven input with Enter key submit + auto-clear

Run:
    cd nitro && python examples/sanic_chat_app.py
    Then visit http://localhost:8004
"""
import uuid
from datetime import datetime, timezone

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

class Message(Entity, table=True):
    """A chat message with author and timestamp."""
    __tablename__ = "chat_message"
    author: str = "Anonymous"
    body: str = ""
    sent_at: str = ""  # ISO timestamp string

    @classmethod
    @post()
    def send(cls, body: str = "", nickname: str = "", request=None):
        """Post a new message to the chat."""
        body = body.strip()
        if not body:
            return {"error": "empty"}
        author = nickname.strip() or "Anonymous"
        msg = cls(
            id=uuid.uuid4().hex[:8],
            author=author,
            body=body,
            sent_at=datetime.now(timezone.utc).strftime("%H:%M"),
        )
        msg.save()
        _broadcast_messages()
        # Clear the input field
        publish_sync("sse", SSE.patch_signals({"body": ""}))
        return {"id": msg.id}


# ---------------------------------------------------------------------------
# Broadcast helper — new API
# ---------------------------------------------------------------------------

def _broadcast_messages():
    """Push updated message list + stats to all connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(message_list(), selector="#messages"))
    publish_sync("sse", SSE.patch_elements(chat_stats(), selector="#chat-stats"))


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

def message_bubble(msg: Message):
    """A single chat message bubble."""
    return Div(
        # Author + time header
        Div(
            Span(msg.author, class_="text-xs font-semibold text-indigo-600"),
            Span(msg.sent_at, class_="text-xs text-gray-400"),
            class_="flex items-center gap-2 mb-1",
        ),
        # Message body
        P(msg.body, class_="text-sm text-gray-800 leading-relaxed"),
        class_=(
            "bg-white rounded-xl px-4 py-3 shadow-sm border border-gray-100 "
            "hover:shadow-md transition-shadow"
        ),
    )


def message_list():
    """All messages — replaced by SSE on every new message."""
    messages = Message.all()
    # Sort by id (creation order) since all are uuid-based with same length
    messages.sort(key=lambda m: m.id)

    if not messages:
        return Div(
            P(
                "No messages yet. Say something!",
                class_="text-gray-400 text-center text-sm italic py-12",
            ),
            id="messages",
            class_="flex flex-col gap-3 min-h-[200px] max-h-[500px] overflow-y-auto px-1 py-2",
        )

    return Div(
        *(message_bubble(m) for m in messages),
        id="messages",
        class_="flex flex-col gap-3 min-h-[200px] max-h-[500px] overflow-y-auto px-1 py-2",
    )


def chat_stats():
    """Message count — replaced by SSE on every change."""
    messages = Message.all()
    total = len(messages)
    authors = len(set(m.author for m in messages))

    if total == 0:
        return Div(id="chat-stats")

    return Div(
        Span(f"{total} message{'s' if total != 1 else ''}", class_="text-sm text-gray-500"),
        Span("\u00b7", class_="text-gray-300 mx-2"),
        Span(f"{authors} participant{'s' if authors != 1 else ''}", class_="text-sm text-indigo-400"),
        id="chat-stats",
        class_="flex items-center justify-center py-2",
    )


def chat_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Chat", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Real-time multi-user chat \u2014 open in multiple tabs to see live sync",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Nickname + message input area
            Div(
                # Nickname field
                Div(
                    Span("Nickname", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
                    Input(
                        type="text",
                        placeholder="Your name...",
                        bind="nickname",
                        class_=(
                            "w-full px-3 py-2 rounded-lg border border-gray-200 "
                            "bg-gray-50 focus:bg-white focus:border-indigo-400 "
                            "focus:ring-2 focus:ring-indigo-100 outline-none "
                            "transition-all text-sm text-gray-700 placeholder-gray-400"
                        ),
                    ),
                    class_="flex flex-col gap-1",
                ),

                # Message input + send button
                Div(
                    Span("Message", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
                    Div(
                        Input(
                            type="text",
                            placeholder="Type a message...",
                            bind="body",
                            on_keys_enter=action(Message.send),
                            class_=(
                                "flex-1 px-4 py-3 rounded-xl border border-gray-200 "
                                "bg-gray-50 focus:bg-white focus:border-indigo-400 "
                                "focus:ring-2 focus:ring-indigo-100 outline-none "
                                "transition-all text-gray-700 placeholder-gray-400"
                            ),
                        ),
                        Button(
                            "Send",
                            class_=(
                                "px-6 py-3 rounded-xl font-semibold text-white "
                                "bg-indigo-500 hover:bg-indigo-600 active:scale-95 "
                                "transition-all shadow-sm"
                            ),
                            on_click=action(Message.send),
                        ),
                        class_="flex gap-3",
                    ),
                    class_="flex flex-col gap-1 flex-1",
                ),

                class_="flex gap-4 mb-6 items-end",
                data_signals="{nickname: '', body: ''}",
            ),

            # Chat area
            Div(
                H2("Chat", class_="text-sm font-bold uppercase tracking-wider text-gray-400 mb-3"),
                message_list(),
                class_=(
                    "bg-gray-50 rounded-2xl border border-gray-200 p-5"
                ),
            ),

            # Stats
            chat_stats(),

            # Multi-tab notice
            Div(
                P(
                    "Open in multiple tabs with different nicknames \u2014 messages sync in real time",
                    class_="text-xs text-gray-400 mt-4 text-center",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-2xl mx-auto px-6 py-12",
        ),
        title="Nitro Chat",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroChat")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    Message.repository().init_db()


@app.get("/")
async def homepage(request: Request):
    return html(str(chat_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8004, debug=True, auto_reload=True)
