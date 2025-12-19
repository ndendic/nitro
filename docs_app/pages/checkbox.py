"""Checkbox component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.events import on, emit_elements

from nitro.infrastructure.html.components import Checkbox, Label

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Checkbox("Accept terms and conditions", id="terms"),
        cls="flex flex-col gap-2"
    )


def example_with_binding():
    sigs = Signals(newsletter=False, updates=True)
    return Div(
        Div(
            Checkbox("Subscribe to newsletter", id="newsletter", bind=sigs.newsletter),
            cls="mb-2"
        ),
        Div(
            Checkbox("Receive product updates", id="updates", bind=sigs.updates),
            cls="mb-2"
        ),
        Div(
            P("Newsletter: ", Span(data_text="$newsletter ? 'Subscribed' : 'Not subscribed'")),
            P("Updates: ", Span(data_text="$updates ? 'Enabled' : 'Disabled'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="flex flex-col"
    )


def example_disabled():
    return Div(
        Checkbox("Enabled checkbox", id="enabled"),
        Checkbox("Disabled checkbox", id="disabled", disabled=True),
        Checkbox("Disabled checked", id="disabled-checked", disabled=True, checked=True),
        cls="flex flex-col gap-2"
    )


def example_in_field():
    sigs = Signals(remember=False)
    return Div(
        Div(
            Checkbox("Remember my preference", id="remember", bind=sigs.remember),
            P("This will save your settings for next time.", cls="text-muted-foreground text-sm mt-1"),
            cls="field"
        ),
        Div(
            P("Remember preference: ", Span(data_text="$remember")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
    )


def example_without_label():
    return Div(
        Div(
            Checkbox(id="standalone"),
            Label("Standalone checkbox (separate label)", html_for="standalone", cls="ml-2"),
            cls="flex items-center"
        ),
        cls="flex flex-col gap-2"
    )


page = Div(
        H1("Checkbox Component"),
        P(
            "Checkbox input with Datastar two-way binding. Uses Basecoat's context-based "
            "styling inside Field. When placed inside a .field container, the checkbox is "
            "automatically styled via Basecoat CSS."
        ),
        Section(
            "Basic Checkbox",
            P("A simple checkbox with integrated label:"),
            ComponentShowcase(example_basic),
        ),
        Section(
            "With Datastar Binding",
            P("Checkboxes with two-way binding showing live state:"),
            ComponentShowcase(example_with_binding),
        ),
        Section(
            "Disabled State",
            P("Checkboxes can be disabled:"),
            ComponentShowcase(example_disabled),
        ),
        Section(
            "In Field Context",
            P("Inside a .field container for form layout with description text:"),
            ComponentShowcase(example_in_field),
        ),
        Section(
            "Without Integrated Label",
            P("Checkbox without children returns just the input, allowing custom label placement:"),
            ComponentShowcase(example_without_label),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
def Checkbox(
    *children,                   # Label content (text, icons, etc.)
    id: str,                     # Unique identifier (required)
    bind: Signal = None,         # Datastar Signal for two-way binding
    checked: bool = False,       # Initial checked state (when no bind)
    disabled: bool = False,      # Whether checkbox is disabled
    required: bool = False,      # Whether checkbox is required
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Datastar Binding",
            CodeBlock(
                """
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.html.components import Checkbox

# Create signals
form = Signals(accepted=False, newsletter=True)

# Bind to signal
Checkbox("Accept terms", id="terms", bind=form.accepted)

# The checkbox state will sync with the signal
# Signal value: True when checked, False when unchecked
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/checkbox")
@template(title="Checkbox Component Documentation")
def checkbox_page():
    return page

@on("page.checkbox")
async def get_checkbox(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.checkbox")