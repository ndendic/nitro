"""Radio Group component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signal, Signals
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import Label
from nitro.infrastructure.html.components.radio import RadioGroup, RadioItem

router: APIRouter = APIRouter()


def example_basic():
    sigs = Signals(size="md")
    return Div(
        RadioGroup(
            RadioItem("Small", value="sm"),
            RadioItem("Medium", value="md"),
            RadioItem("Large", value="lg"),
            bind=sigs.size,
        ),
        Div(
            P("Selected size: ", Span(data_text="$size")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
    )


def example_horizontal():
    sigs = Signals(alignment="left")
    return Div(
        RadioGroup(
            RadioItem("Left", value="left"),
            RadioItem("Center", value="center"),
            RadioItem("Right", value="right"),
            bind=sigs.alignment,
            orientation="horizontal",
        ),
        Div(
            P("Selected alignment: ", Span(data_text="$alignment")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
    )


def example_preselected():
    sigs = Signals(plan="pro")
    return Div(
        P("Choose your plan:", cls="font-medium mb-2"),
        RadioGroup(
            RadioItem("Free - $0/month", value="free"),
            RadioItem("Pro - $10/month", value="pro"),
            RadioItem("Enterprise - $50/month", value="enterprise"),
            bind=sigs.plan,
        ),
        Div(
            P("Selected plan: ", Span(data_text="$plan")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
    )


def example_disabled():
    sigs = Signals(status="active")
    return Div(
        RadioGroup(
            RadioItem("Active", value="active"),
            RadioItem("Inactive", value="inactive"),
            RadioItem("Archived (unavailable)", value="archived", disabled=True),
            bind=sigs.status,
        ),
        Div(
            P("Selected status: ", Span(data_text="$status")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
    )


def example_in_field():
    sigs = Signals(priority="medium")
    return Div(
        Div(
            Label("Priority Level", cls="font-medium mb-2"),
            RadioGroup(
                RadioItem("Low", value="low"),
                RadioItem("Medium", value="medium"),
                RadioItem("High", value="high"),
                RadioItem("Critical", value="critical"),
                bind=sigs.priority,
            ),
            P("Select the priority for this task.", cls="text-muted-foreground text-sm mt-2"),
            cls="field"
        ),
        Div(
            P("Selected priority: ", Span(data_text="$priority")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
    )


page = Div(
        H1("Radio Group Component"),
        P(
            "Radio group with compound component pattern. Uses Datastar two-way binding "
            "to track the selected value. Only one option can be selected at a time."
        ),
        Section(
            "Basic Radio Group",
            P("A vertical radio group with signal binding:"),
            ComponentShowcase(example_basic),
        ),
        Section(
            "Horizontal Orientation",
            P("Radio buttons can be arranged horizontally:"),
            ComponentShowcase(example_horizontal),
        ),
        Section(
            "Pre-selected Value",
            P("Set the initial value in your Signals:"),
            ComponentShowcase(example_preselected),
        ),
        Section(
            "Disabled Options",
            P("Individual radio options can be disabled:"),
            ComponentShowcase(example_disabled),
        ),
        Section(
            "In Field Context",
            P("Inside a .field container with label and description:"),
            ComponentShowcase(example_in_field),
        ),
        Section(
            "API Reference",
            H3("RadioGroup", cls="font-semibold mb-2"),
            CodeBlock(
                """
def RadioGroup(
    *children,                   # RadioItem children
    bind: Signal,                # Datastar Signal for binding (required)
    orientation: str = "vertical",  # "vertical" or "horizontal"
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
            H3("RadioItem", cls="font-semibold mb-2 mt-4"),
            CodeBlock(
                """
def RadioItem(
    *children,                   # Label content (text, icons, etc.)
    value: str,                  # Value for this option (required)
    id: str = "",                # Unique identifier (auto-generated)
    name: str = "",              # Name attribute (uses signal name)
    disabled: bool = False,      # Whether option is disabled
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> Callable                    # Returns closure called by RadioGroup
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Usage Example",
            CodeBlock(
                """
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.html.components.radio import RadioGroup, RadioItem

# Create signals with initial value
form = Signals(theme="light")

# Create radio group - bind passes signal to children
RadioGroup(
    RadioItem("Light Mode", value="light"),
    RadioItem("Dark Mode", value="dark"),
    RadioItem("System", value="system"),
    bind=form.theme,
    orientation="vertical",  # or "horizontal"
)

# Access signal value: $theme contains "light", "dark", or "system"
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Compound Component Pattern",
            P(
                "RadioGroup uses the closure pattern for compound components. "
                "RadioItem returns a function that RadioGroup calls with the signal name, "
                "enabling automatic binding without manually passing the signal to each item."
            ),
            CodeBlock(
                """
# RadioItem returns a closure
def RadioItem(*children, value, ...):
    def create_radio(signal_name: str) -> HtmlString:
        # Uses signal_name for data_bind
        return HTMLInput(..., data_bind=signal_name, value=value)
    return create_radio

# RadioGroup calls the closure with the signal
def RadioGroup(*children, bind, ...):
    signal_name = bind.to_js().lstrip('$')
    for child in children:
        if callable(child):
            result = child(signal_name)  # Pass signal to closure
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/radio")
@template(title="Radio Group Component Documentation")
def radio_page():
    return page

@on("page.radio")
async def get_radio(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.radio")