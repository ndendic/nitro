"""Textarea component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import Label
from nitro.infrastructure.html.components.textarea import Textarea

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Textarea(
            id="message-basic",
            placeholder="Enter your message...",
        ),
        cls="flex flex-col gap-2"
    )


def example_with_binding():
    sigs = Signals(bio="", feedback="")
    return Div(
        Div(
            Label("Bio", html_for="bio"),
            Textarea(
                id="bio",
                bind=sigs.bio,
                placeholder="Tell us about yourself...",
                rows=4,
            ),
            cls="field mb-4"
        ),
        Div(
            Label("Feedback", html_for="feedback"),
            Textarea(
                id="feedback",
                bind=sigs.feedback,
                placeholder="What do you think?",
                rows=3,
            ),
            cls="field mb-4"
        ),
        Div(
            P("Bio (", Span(data_text="$bio.length"), " chars): ", Span(data_text="$bio")),
            P("Feedback (", Span(data_text="$feedback.length"), " chars): ", Span(data_text="$feedback")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="flex flex-col"
    )


def example_character_limit():
    sigs = Signals(tweet="")
    return Div(
        Div(
            Label("Tweet", html_for="tweet"),
            Textarea(
                id="tweet",
                bind=sigs.tweet,
                placeholder="What's happening?",
                rows=3,
                maxlength=280,
            ),
            Div(
                Span(data_text="$tweet.length"),
                "/280 characters",
                cls="text-sm text-muted-foreground mt-1"
            ),
            cls="field"
        ),
        signals=sigs,
    )


def example_row_sizes():
    return Div(
        Div(
            Label("Small (2 rows)", html_for="small"),
            Textarea(id="small", placeholder="Small textarea", rows=2),
            cls="field mb-4"
        ),
        Div(
            Label("Medium (4 rows)", html_for="medium"),
            Textarea(id="medium", placeholder="Medium textarea", rows=4),
            cls="field mb-4"
        ),
        Div(
            Label("Large (8 rows)", html_for="large"),
            Textarea(id="large", placeholder="Large textarea", rows=8),
            cls="field"
        ),
        cls="flex flex-col"
    )


def example_disabled():
    return Div(
        Div(
            Label("Enabled", html_for="enabled"),
            Textarea(id="enabled", placeholder="You can type here..."),
            cls="field mb-4"
        ),
        Div(
            Label("Disabled", html_for="disabled-ta"),
            Textarea(id="disabled-ta", placeholder="Cannot type here", disabled=True),
            cls="field mb-4"
        ),
        Div(
            Label("Read-only", html_for="readonly"),
            Textarea("This content is read-only and cannot be edited.", id="readonly", readonly=True),
            cls="field"
        ),
        cls="flex flex-col gap-2"
    )


page = Div(
        H1("Textarea Component"),
        P(
            "Textarea input with Datastar two-way binding. Uses Basecoat's context-based "
            "styling inside Field. When placed inside a .field container, the textarea is "
            "automatically styled via Basecoat CSS."
        ),
        Section(
            "Basic Textarea",
            P("A simple textarea with placeholder:"),
            ComponentShowcase(example_basic),
        ),
        Section(
            "With Datastar Binding",
            P("Textarea with two-way binding showing real-time character count:"),
            ComponentShowcase(example_with_binding),
        ),
        Section(
            "Character Limit",
            P("Textarea with maxlength and character counter:"),
            ComponentShowcase(example_character_limit),
        ),
        Section(
            "Row Sizes",
            P("Control textarea height with the rows attribute:"),
            ComponentShowcase(example_row_sizes),
        ),
        Section(
            "Disabled and Read-only States",
            P("Textarea can be disabled or set to read-only:"),
            ComponentShowcase(example_disabled),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
def Textarea(
    *children,                   # Default text content
    id: str = None,              # Unique identifier (optional)
    bind: Signal = None,         # Datastar Signal for two-way binding
    placeholder: str = "",       # Placeholder text
    rows: int = 3,               # Visible text lines
    cols: int = None,            # Visible width in characters
    disabled: bool = False,      # Whether textarea is disabled
    required: bool = False,      # Whether textarea is required
    readonly: bool = False,      # Whether textarea is read-only
    maxlength: int = None,       # Maximum character limit
    minlength: int = None,       # Minimum character limit
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Character Counter Pattern",
            CodeBlock(
                """
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.html.components.textarea import Textarea

# Create signal for text content
form = Signals(message="")

Div(
    Label("Message", html_for="message"),
    Textarea(
        id="message",
        bind=form.message,
        maxlength=500,
        rows=4,
    ),
    # Character counter using Datastar data_text
    Div(
        Span(data_text="$message.length"),
        "/500 characters",
        cls="text-sm text-muted-foreground"
    ),
    cls="field",
    signals=form,
)
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/textarea")
@template(title="Textarea Component Documentation")
def textarea_page():
    return page

@on("page.textarea")
async def get_textarea(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.textarea")