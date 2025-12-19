"""Label component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import Label

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Label("Email", html_for="email"),
        Input(type="email", id="email", placeholder="name@example.com", cls="input w-full"),
        cls="space-y-2"
    )


def example_required():
    return Div(
        Label("Password", html_for="password", required=True),
        Span(" *", cls="text-red-500"),
        Input(type="password", id="password", cls="input w-full"),
        cls="space-y-2"
    )


def example_disabled():
    return Div(
        Label("Disabled Field", html_for="disabled-input", disabled=True),
        Input(type="text", id="disabled-input", disabled=True, cls="input w-full"),
        cls="space-y-2"
    )


def example_with_icons():
    return Div(
        Label(LucideIcon("mail", cls="size-4"), " Email Address", html_for="email-icon"),
        Input(type="email", id="email-icon", placeholder="name@example.com", cls="input w-full"),
        cls="space-y-2"
    )


def example_form():
    return Form(
        Div(
            Label("First Name", html_for="first-name"),
            Input(type="text", id="first-name", cls="input w-full"),
            cls="space-y-2"
        ),
        Div(
            Label("Last Name", html_for="last-name"),
            Input(type="text", id="last-name", cls="input w-full"),
            cls="space-y-2"
        ),
        Div(
            Label("Email", html_for="form-email", required=True),
            Input(type="email", id="form-email", cls="input w-full"),
            cls="space-y-2"
        ),
        Div(
            Label("Message", html_for="message"),
            Textarea(id="message", rows="4", cls="textarea w-full"),
            cls="space-y-2"
        ),
        cls="space-y-4 max-w-md"
    )


page = Div(
        H1("Label Component"),
        P(
            "A text label associated with a form control, providing "
            "accessible naming for inputs."
        ),
        Section(
            "Design Philosophy",
            P("Labels are essential for form accessibility:"),
            Ul(
                Li("Uses the html_for attribute (maps to HTML 'for')"),
                Li("Clicking the label focuses the associated input"),
                Li("Screen readers announce the label for the input"),
                Li("Supports required and disabled visual states"),
            ),
        ),
        Section(
            "Basic Label",
            P("A simple label with an input:"),
            ComponentShowcase(example_basic),
        ),
        Section(
            "Required Field",
            P("Indicate required fields with the required prop:"),
            ComponentShowcase(example_required),
        ),
        Section(
            "Disabled State",
            P("Labels can indicate disabled fields:"),
            ComponentShowcase(example_disabled),
        ),
        Section(
            "With Icons",
            P("Labels can include icons:"),
            ComponentShowcase(example_with_icons),
        ),
        Section(
            "Form Example",
            P("Labels in a complete form:"),
            ComponentShowcase(example_form),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
def Label(
    *children,                              # Label content (text, icons, etc.)
    html_for: Optional[str] = None,         # ID of associated form element
    required: bool = False,                 # Show required indicator
    disabled: bool = False,                 # Apply disabled styling
    cls: str = "",                          # Additional CSS classes
    **attrs                                 # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/label")
@template(title="Label Component Documentation")
def label_page():
    return page

@on("page.label")
async def get_label(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.label")