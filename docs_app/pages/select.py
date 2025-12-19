"""Select component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import Label
from nitro.infrastructure.html.components.select import Select, SelectOption, SelectOptGroup

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Select(
            SelectOption("Small", value="sm"),
            SelectOption("Medium", value="md"),
            SelectOption("Large", value="lg"),
            id="size-basic",
        ),
        cls="flex flex-col gap-2"
    )


def example_with_placeholder():
    return Div(
        Select(
            SelectOption("Red", value="red"),
            SelectOption("Green", value="green"),
            SelectOption("Blue", value="blue"),
            id="color",
            placeholder="Select a color...",
        ),
        cls="flex flex-col gap-2"
    )


def example_with_binding():
    sigs = Signals(size="md", color="")
    return Div(
        Div(
            Label("Size", html_for="size-bound"),
            Select(
                SelectOption("Small", value="sm"),
                SelectOption("Medium", value="md"),
                SelectOption("Large", value="lg"),
                id="size-bound",
                bind=sigs.size,
            ),
            cls="field mb-4"
        ),
        Div(
            Label("Color", html_for="color-bound"),
            Select(
                SelectOption("Red", value="red"),
                SelectOption("Green", value="green"),
                SelectOption("Blue", value="blue"),
                id="color-bound",
                bind=sigs.color,
                placeholder="Pick a color...",
            ),
            cls="field mb-4"
        ),
        Div(
            P("Selected size: ", Span(data_text="$size")),
            P("Selected color: ", Span(data_text="$color || 'none'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="flex flex-col"
    )


def example_with_optgroup():
    sigs = Signals(vehicle="")
    return Div(
        Div(
            Label("Vehicle", html_for="vehicle"),
            Select(
                SelectOptGroup(
                    SelectOption("Sedan", value="sedan"),
                    SelectOption("SUV", value="suv"),
                    SelectOption("Truck", value="truck"),
                    label="Cars"
                ),
                SelectOptGroup(
                    SelectOption("Sport", value="sport"),
                    SelectOption("Cruiser", value="cruiser"),
                    SelectOption("Touring", value="touring"),
                    label="Motorcycles"
                ),
                id="vehicle",
                bind=sigs.vehicle,
                placeholder="Select a vehicle...",
            ),
            cls="field"
        ),
        Div(
            P("Selected vehicle: ", Span(data_text="$vehicle || 'none'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
    )


def example_disabled():
    return Div(
        Div(
            Label("Enabled Select", html_for="enabled"),
            Select(
                SelectOption("Option 1", value="1"),
                SelectOption("Option 2", value="2"),
                id="enabled",
            ),
            cls="field mb-4"
        ),
        Div(
            Label("Disabled Select", html_for="disabled"),
            Select(
                SelectOption("Option 1", value="1"),
                SelectOption("Option 2", value="2"),
                id="disabled",
                disabled=True,
            ),
            cls="field mb-4"
        ),
        Div(
            Label("With Disabled Option", html_for="disabled-option"),
            Select(
                SelectOption("Available", value="available"),
                SelectOption("Unavailable (sold out)", value="unavailable", disabled=True),
                SelectOption("Available", value="available2"),
                id="disabled-option",
            ),
            cls="field"
        ),
        cls="flex flex-col gap-2"
    )


page = Div(
        H1("Select Component"),
        P(
            "Native select dropdown with Datastar two-way binding. Uses Basecoat's context-based "
            "styling inside Field. When placed inside a .field container, the select is "
            "automatically styled via Basecoat CSS."
        ),
        Section(
            "Basic Select",
            P("A simple select dropdown with options:"),
            ComponentShowcase(example_basic),
        ),
        Section(
            "With Placeholder",
            P("A select with a placeholder option:"),
            ComponentShowcase(example_with_placeholder),
        ),
        Section(
            "With Datastar Binding",
            P("Select with two-way binding showing live selected value:"),
            ComponentShowcase(example_with_binding),
        ),
        Section(
            "With Option Groups",
            P("Organize options into logical groups using SelectOptGroup:"),
            ComponentShowcase(example_with_optgroup),
        ),
        Section(
            "Disabled States",
            P("Select and individual options can be disabled:"),
            ComponentShowcase(example_disabled),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
def Select(
    *children,                   # SelectOption elements
    id: str,                     # Unique identifier (required)
    bind: Signal = None,         # Datastar Signal for two-way binding
    placeholder: str = "",       # Placeholder text (disabled first option)
    disabled: bool = False,      # Whether select is disabled
    required: bool = False,      # Whether select is required
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString

def SelectOption(
    *children,                   # Option label content
    value: str,                  # Value to submit
    disabled: bool = False,      # Whether option is disabled
    selected: bool = False,      # Initial selection (prefer bind)
    **attrs                      # Additional HTML attributes
) -> HtmlString

def SelectOptGroup(
    *children,                   # SelectOption elements
    label: str,                  # Group label
    disabled: bool = False,      # Disable all options in group
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
from nitro.infrastructure.html.components.select import Select, SelectOption

# Create signals
form = Signals(size="md", color="")

# Bind to signal
Select(
    SelectOption("Small", value="sm"),
    SelectOption("Medium", value="md"),
    SelectOption("Large", value="lg"),
    id="size",
    bind=form.size,
)

# The select value will sync with the signal
# Signal updates when user selects a different option
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/select")
@template(title="Select Component Documentation")
def select_page():
    return page

@on("page.select")
async def get_select(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.select")