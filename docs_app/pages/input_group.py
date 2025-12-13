"""Input Group component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.responses import HTMLResponse
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signal, Signals

from nitro.infrastructure.html.components import InputGroup, InputPrefix, InputSuffix, LucideIcon, Field

router: APIRouter = APIRouter()


def example_prefix_text():
    return Div(
        InputGroup(
            InputPrefix("$"),
            Input(type="number", id="price", placeholder="0.00", cls="input"),
        ),
        cls="max-w-xs"
    )


def example_suffix_text():
    return Div(
        InputGroup(
            Input(type="text", id="website", placeholder="example", cls="input"),
            InputSuffix(".com"),
        ),
        cls="max-w-xs"
    )


def example_prefix_icon():
    return Div(
        InputGroup(
            InputPrefix(LucideIcon("search", cls="w-4 h-4")),
            Input(type="text", id="search", placeholder="Search...", cls="input"),
        ),
        cls="max-w-sm"
    )


def example_suffix_icon():
    return Div(
        InputGroup(
            Input(type="email", id="email-with-icon", placeholder="you@example.com", cls="input"),
            InputSuffix(LucideIcon("mail", cls="w-4 h-4")),
        ),
        cls="max-w-sm"
    )


def example_both():
    return Div(
        InputGroup(
            InputPrefix("https://"),
            Input(type="text", id="url", placeholder="example.com", cls="input"),
            InputSuffix("/path"),
        ),
        cls="max-w-md"
    )


def example_with_datastar():
    sigs = Signals(amount="100", url="github")
    return Div(
        Div(
            P("Price:", cls="text-sm font-medium mb-1"),
            InputGroup(
                InputPrefix("$"),
                Input(type="number", id="amount", data_bind="amount", cls="input"),
                InputSuffix(".00"),
            ),
            cls="mb-4"
        ),
        Div(
            P("Website:", cls="text-sm font-medium mb-1"),
            InputGroup(
                InputPrefix("https://"),
                Input(type="text", id="url-input", data_bind="url", cls="input"),
                InputSuffix(".com"),
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
                InputPrefix("$"),
                Input(type="number", id="budget", placeholder="0.00", cls="input"),
            ),
            label="Monthly Budget",
            label_for="budget",
            description="Enter your monthly spending limit.",
        ),
        Field(
            InputGroup(
                InputPrefix(LucideIcon("user", cls="w-4 h-4")),
                Input(type="text", id="username-field", placeholder="username", cls="input"),
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
                InputPrefix(LucideIcon("credit-card", cls="w-4 h-4")),
                Input(type="text", id="card", placeholder="1234 5678 9012 3456", cls="input"),
            ),
            cls="mb-4"
        ),
        Div(
            P("Phone Number:", cls="text-sm font-medium mb-1"),
            InputGroup(
                InputPrefix("+1"),
                Input(type="tel", id="phone", placeholder="(555) 123-4567", cls="input"),
            ),
            cls="mb-4"
        ),
        Div(
            P("Twitter Handle:", cls="text-sm font-medium mb-1"),
            InputGroup(
                InputPrefix("@"),
                Input(type="text", id="twitter", placeholder="username", cls="input"),
            ),
            cls="mb-4"
        ),
        Div(
            P("Percentage:", cls="text-sm font-medium mb-1"),
            InputGroup(
                Input(type="number", id="percent", placeholder="0", min="0", max="100", cls="input"),
                InputSuffix("%"),
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
    *children,           # InputPrefix, Input, InputSuffix elements
    cls: str = "",       # Additional CSS classes
    **attrs              # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "API Reference - InputPrefix",
            CodeBlock(
                """
def InputPrefix(
    *children,           # Content (text, icons, etc.)
    cls: str = "",       # Additional CSS classes
    **attrs              # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "API Reference - InputSuffix",
            CodeBlock(
                """
def InputSuffix(
    *children,           # Content (text, icons, etc.)
    cls: str = "",       # Additional CSS classes
    **attrs              # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Important Notes",
            P("When using InputGroup, add the 'input' class to your Input element:"),
            CodeBlock(
                """
# The Input inside InputGroup needs the 'input' class for proper styling
InputGroup(
    InputPrefix("$"),
    Input(type="number", id="price", cls="input"),  # <-- Add cls="input"
)

# This is because InputGroup handles border radius adjustments
# for seamless appearance between prefix/input/suffix
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Styling Notes",
            CodeBlock(
                """
# InputGroup uses Tailwind utility classes for:
# - flex container with items-stretch
# - Border radius adjustments (first child rounded-l, last child rounded-r)
# - Removing double borders between adjacent elements
# - Making input fill available space

# InputPrefix/InputSuffix use:
# - bg-muted/50 for subtle background
# - text-muted-foreground for subdued text
# - border-input for consistent border color
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
    )
