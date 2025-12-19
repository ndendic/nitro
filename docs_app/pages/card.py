"""Card component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import (
    Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
    Button
)


router: APIRouter = APIRouter()


def example_basic():
    return Card(
        CardHeader(
            CardTitle("Card Title"),
            CardDescription("Card description goes here"),
        ),
        CardContent(
            P("This is the main content area of the card. You can put any content here."),
        ),
        CardFooter(
            Button("Cancel", variant="outline"),
            Button("Save", variant="primary"),
            cls="flex gap-2 justify-end"
        ),
    )


def example_simple():
    return Card(
        CardContent(
            P("A simple card with just content, no header or footer."),
        ),
    )



def example_login_form():
    return Card(
        CardHeader(
            CardTitle("Login"),
            CardDescription("Enter your credentials to access your account"),
        ),
        CardContent(
            Form(
                Div(
                    Input(label="Email", type="email", id="email", placeholder="name@example.com", cls="input w-full"),
                    cls="space-y-2"
                ),
                Div(
                    Input(label="Password", type="password", id="password", cls="input w-full"),
                    cls="space-y-2 mt-4"
                ),
                cls="space-y-4"
            ),
        ),
        CardFooter(
            Button("Sign In", variant="primary", cls="w-full"),
        ),
        cls="w-full max-w-sm"
    )


def example_stats():
    return Div(
        Card(
            CardHeader(
                CardTitle("Total Revenue"),
                CardDescription("Last 30 days"),
            ),
            CardContent(
                P("$45,231.89", cls="text-2xl font-bold"),
                P("+20.1% from last month", cls="text-sm text-muted-foreground"),
            ),
        ),
        Card(
            CardHeader(
                CardTitle("Active Users"),
                CardDescription("Current month"),
            ),
            CardContent(
                P("+2,350", cls="text-2xl font-bold"),
                P("+180.1% from last month", cls="text-sm text-muted-foreground"),
            ),
        ),
        Card(
            CardHeader(
                CardTitle("Sales"),
                CardDescription("This week"),
            ),
            CardContent(
                P("+12,234", cls="text-2xl font-bold"),
                P("+19% from last week", cls="text-sm text-muted-foreground"),
            ),
        ),
        cls="grid grid-cols-1 md:grid-cols-3 gap-4"
    )


page = Div(
        H1("Card Component"),
        P(
            "A flexible container that groups related content and actions. "
            "Works well with compound subcomponents for structured layouts."
        ),
        TitledSection(
            "Design Philosophy",
            P("The Card component follows the compound component pattern:"),
            Ul(
                Li("Card - Root container"),
                Li("CardHeader - Header section (optional)"),
                Li("CardTitle - Title element"),
                Li("CardDescription - Description/subtitle"),
                Li("CardContent - Main content area"),
                Li("CardFooter - Footer section for actions"),
            ),
        ),
        TitledSection(
            "Basic Card",
            P("A complete card with header, content, and footer:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "Simple Card",
            P("Cards can be as simple as a container with content:"),
            ComponentShowcase(example_simple),
        ),

        TitledSection(
            "Login Form Example",
            P("Cards work great for forms:"),
            ComponentShowcase(example_login_form),
        ),
        TitledSection(
            "Stats Dashboard",
            P("Multiple cards in a grid layout:"),
            ComponentShowcase(example_stats),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(             
"""def Card(
    *children,                              # Card content (typically Card* subcomponents)
    variant: str = "default",               # default, elevated, outline, ghost
    cls: str = "",                          # Additional CSS classes
    **attrs                                 # Additional HTML attributes
) -> HtmlString

def CardHeader(*children, cls="", **attrs) -> HtmlString
def CardTitle(*children, cls="", **attrs) -> HtmlString
def CardDescription(*children, cls="", **attrs) -> HtmlString
def CardContent(*children, cls="", **attrs) -> HtmlString
def CardFooter(*children, cls="", **attrs) -> HtmlString""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
        id="content"

    )

@router.get("/xtras/card")
@template(title="Card Component Documentation")
def card_docs():
    return page

@on("page.card")
async def get_card(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.card")