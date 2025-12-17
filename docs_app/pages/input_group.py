"""Input Group component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.responses import HTMLResponse
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signal, Signals

from nitro.infrastructure.html.components import InputGroup, LucideIcon, Field

router: APIRouter = APIRouter()


def example_prefix_text():
    return Div(
        InputGroup(
            Input(type="number", id="price", placeholder="0.00", cls="input pl-9"),
            left="$",
        ),
        cls="max-w-xs"
    )


def example_suffix_text():
    return Div(
        InputGroup(
            Input(type="text", id="website", placeholder="example", cls="input pr-14"),
            right=".com",
        ),
        cls="max-w-xs"
    )


def example_prefix_icon():
    return Div(
        InputGroup(
            Input(type="text", id="search", placeholder="Search...", cls="input pl-9"),
            left=LucideIcon("search", cls="w-4 h-4"),
        ),
        cls="max-w-sm"
    )


def example_suffix_icon():
    return Div(
        InputGroup(
            Input(type="email", id="email-with-icon", placeholder="you@example.com", cls="input pr-9"),
            right=LucideIcon("mail", cls="w-4 h-4"),
        ),
        cls="max-w-sm"
    )


def example_both():
    return Div(
        InputGroup(
            Input(type="text", id="url", placeholder="example.com", cls="input pl-20 pr-14"),
            left="https://",
            right="/path",
        ),
        cls="max-w-md"
    )


def example_with_datastar():
    sigs = Signals(amount="100", url="github")
    return Div(
        Div(
            P("Price:", cls="text-sm font-medium mb-1"),
            InputGroup(
                Input(type="number", id="amount", data_bind="amount", cls="input pl-9 pr-12"),
                left="$",
                right=".00",
            ),
            cls="mb-4"
        ),
        Div(
            P("Website:", cls="text-sm font-medium mb-1"),
            InputGroup(
                Input(type="text", id="url-input", data_bind="url", cls="input pl-20 pr-14"),
                left="https://",
                right=".com",
            ),
            cls="mb-4"
        ),
        Div(
            P("Price: $", Span(data_text="$amount"), ".00"),
            P("URL: https://", Span(data_text="$url"), ".com"),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="max-w-md"
    )


def example_with_field():
    return Div(
        Field(
            InputGroup(
                Input(type="number", id="budget", placeholder="0.00", cls="input pl-9"),
                left="$",
            ),
            label="Monthly Budget",
            label_for="budget",
            description="Enter your monthly spending limit.",
        ),
        Field(
            InputGroup(
                Input(type="text", id="username-field", placeholder="username", cls="input pl-9"),
                left=LucideIcon("user", cls="w-4 h-4"),
            ),
            label="Username",
            label_for="username-field",
            description="Choose a unique username.",
        ),
        cls="max-w-sm flex flex-col gap-4"
    )


def example_variations():
    return Div(
        Div(
            P("Credit Card:", cls="text-sm font-medium mb-1"),
            InputGroup(
                Input(type="text", id="card", placeholder="1234 5678 9012 3456", cls="input pl-9"),
                left=LucideIcon("credit-card", cls="w-4 h-4"),
            ),
            cls="mb-4"
        ),
        Div(
            P("Phone Number:", cls="text-sm font-medium mb-1"),
            InputGroup(
                Input(type="tel", id="phone", placeholder="(555) 123-4567", cls="input pl-9"),
                left="+1",
            ),
            cls="mb-4"
        ),
        Div(
            P("Twitter Handle:", cls="text-sm font-medium mb-1"),
            InputGroup(
                Input(type="text", id="twitter", placeholder="username", cls="input pl-9"),
                left="@",
            ),
            cls="mb-4"
        ),
        Div(
            P("Percentage:", cls="text-sm font-medium mb-1"),
            InputGroup(
                Input(type="number", id="percent", placeholder="0", min="0", max="100", cls="input pr-9"),
                right="%",
            ),
            cls="mb-4"
        ),
        cls="max-w-sm"
    )


@router.get("/xtras/input-group")
@template(title="Input Group Component Documentation")
def input_group_docs():
    return Div(
        H1("Input Group Component"),
        P(
            "Container for input with prefix/suffix elements. Add icons, text, or other "
            "elements to the sides of an input using Tailwind utility classes."
        ),
        Section(
            "Prefix with Text",
            P("Add a text prefix to an input, like a currency symbol:"),
            ComponentShowcase(example_prefix_text),
        ),
        Section(
            "Suffix with Text",
            P("Add a text suffix to an input, like a domain extension:"),
            ComponentShowcase(example_suffix_text),
        ),
        Section(
            "Prefix with Icon",
            P("Add an icon as a prefix for visual context:"),
            ComponentShowcase(example_prefix_icon),
        ),
        Section(
            "Suffix with Icon",
            P("Add an icon as a suffix:"),
            ComponentShowcase(example_suffix_icon),
        ),
        Section(
            "Both Prefix and Suffix",
            P("Combine prefix and suffix for complex inputs like URLs:"),
            ComponentShowcase(example_both),
        ),
        Section(
            "With Datastar Binding",
            P("InputGroup works with Datastar for reactive forms:"),
            ComponentShowcase(example_with_datastar),
        ),
        Section(
            "With Field Wrapper",
            P("Use InputGroup inside Field for complete form layouts:"),
            ComponentShowcase(example_with_field),
        ),
        Section(
            "Common Variations",
            P("Examples of common input group patterns:"),
            ComponentShowcase(example_variations),
        ),
        Section(
            "API Reference - InputGroup",
            CodeBlock(
                """
def InputGroup(
    input_element: HtmlString,      # The input element
    left: Optional[Any] = None,     # Optional left content (text, icon, etc.)
    right: Optional[Any] = None,    # Optional right content (text, icon, etc.)
    left_interactive: bool = False, # Allow left element interaction
    right_interactive: bool = False,# Allow right element interaction
    cls: str = "",                  # Additional CSS classes
    **attrs                         # Additional HTML attributes
) -> HtmlString

# Uses BasecoatUI's absolute positioning pattern
# Container: relative positioning
# Left/Right: absolute positioning with pointer-events-none (unless interactive)
# Input should have appropriate padding (pl-9, pr-9, etc.)
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Important Notes",
            P("InputGroup uses BasecoatUI's absolute positioning pattern. Key points:"),
            CodeBlock(
                """
# 1. Simple, clean API with left/right parameters
InputGroup(
    Input(type="number", id="price", placeholder="0.00", cls="input pl-9"),
    left="$"
)

# 2. Add appropriate padding to prevent content overlap
# - pl-9: Left padding when using left parameter (icons/text)
# - pr-9: Right padding for right parameter (short text)
# - pr-14: Right padding for right parameter (longer text like ".com")
# - pr-20: Right padding for right parameter (extra long text/buttons)

# 3. Both left and right are optional
InputGroup(
    Input(type="text", cls="input"),  # No padding needed if no left/right
    # left and right parameters omitted
)

# 4. Left/right elements are non-interactive by default
# Use left_interactive=True or right_interactive=True for clickable elements:
InputGroup(
    Input(type="text", id="search", placeholder="Search...", cls="input pl-9 pr-20"),
    left=LucideIcon("search", cls="w-4 h-4"),
    right=Button("Search", cls="btn-sm"),
    right_interactive=True  # <-- Makes the button clickable
)
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Styling Notes",
            CodeBlock(
                """
# InputGroup uses BasecoatUI's absolute positioning pattern:
# - Container: relative positioning
# - Left element: absolute left-3 top-1/2 -translate-y-1/2
# - Right element: absolute right-3 top-1/2 -translate-y-1/2
# - Input: Full width with adjusted padding

# Left/Right elements use:
# - text-muted-foreground for subdued appearance
# - pointer-events-none (decorative by default, unless *_interactive=True)
# - [&>svg]:size-4 for consistent icon sizing
# - No borders or backgrounds (clean integration with input)
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
    )
