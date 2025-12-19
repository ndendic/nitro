"""Progress component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from rusty_tags.datastar import Signal, Signals
from nitro.infrastructure.events import on, emit_elements

from nitro.infrastructure.html.components import (
    Progress,
    Button,
)

router: APIRouter = APIRouter()


def example_basic():
    """Basic progress bar with different values."""
    return Div(
        Div(
            P("25%", cls="text-sm text-muted-foreground mb-2"),
            Progress(value=25),
            cls="mb-4",
        ),
        Div(
            P("50%", cls="text-sm text-muted-foreground mb-2"),
            Progress(value=50),
            cls="mb-4",
        ),
        Div(
            P("75%", cls="text-sm text-muted-foreground mb-2"),
            Progress(value=75),
            cls="mb-4",
        ),
        Div(
            P("100%", cls="text-sm text-muted-foreground mb-2"),
            Progress(value=100),
        ),
    )


def example_sizes():
    """Different size variants."""
    return Div(
        Div(
            P("Small (sm)", cls="text-sm text-muted-foreground mb-2"),
            Progress(value=60, size="sm"),
            cls="mb-4",
        ),
        Div(
            P("Medium (md) - Default", cls="text-sm text-muted-foreground mb-2"),
            Progress(value=60, size="md"),
            cls="mb-4",
        ),
        Div(
            P("Large (lg)", cls="text-sm text-muted-foreground mb-2"),
            Progress(value=60, size="lg"),
        ),
    )


def example_indeterminate():
    """Indeterminate loading state."""
    return Div(
        P("Loading state with unknown progress:", cls="text-sm text-muted-foreground mb-2"),
        Progress(indeterminate=True),
    )


def example_interactive():
    """Interactive progress with button controls."""
    return Div(
        Div(
            Progress(value=0, id="interactive-progress"),
            cls="mb-4",
        ),
        Div(
            Button(
                "Set 25%",
                variant="outline",
                on_click="document.querySelector('#interactive-progress > div').style.width = '25%'",
            ),
            Button(
                "Set 50%",
                variant="outline",
                on_click="document.querySelector('#interactive-progress > div').style.width = '50%'",
            ),
            Button(
                "Set 75%",
                variant="outline",
                on_click="document.querySelector('#interactive-progress > div').style.width = '75%'",
            ),
            Button(
                "Set 100%",
                variant="outline",
                on_click="document.querySelector('#interactive-progress > div').style.width = '100%'",
            ),
            Button(
                "Reset",
                variant="ghost",
                on_click="document.querySelector('#interactive-progress > div').style.width = '0%'",
            ),
            cls="flex flex-wrap gap-2",
        ),
        signals=Signals(progress=0),
    )


def example_with_label():
    """Progress bar with percentage label."""
    return Div(
        Div(
            Div(
                Span("Uploading files...", cls="text-sm font-medium"),
                Span("65%", cls="text-sm text-muted-foreground"),
                cls="flex justify-between mb-2",
            ),
            Progress(value=65),
        ),
    )


page = Div(
        H1("Progress Component"),
        P(
            "A progress bar indicates the completion status of a task. It can show "
            "determinate progress (specific percentage) or indeterminate progress (loading state)."
        ),
        TitledSection(
            "Design Philosophy",
            P("Progress bars follow these principles:"),
            Ul(
                Li("Uses native HTML with ARIA progressbar role"),
                Li("Smooth transitions for value changes"),
                Li("Indeterminate mode for unknown duration tasks"),
                Li("Multiple sizes for different contexts"),
                Li("Accessible with proper ARIA attributes"),
            ),
        ),
        TitledSection(
            "Basic Usage",
            P("Static progress bars with different completion values:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "Sizes",
            P("Three size variants - small, medium (default), and large:"),
            ComponentShowcase(example_sizes),
        ),
        TitledSection(
            "Indeterminate",
            P("Use indeterminate mode when the progress percentage is unknown:"),
            ComponentShowcase(example_indeterminate),
        ),
        TitledSection(
            "Interactive Progress",
            P("Progress can be updated via JavaScript or Datastar signals:"),
            ComponentShowcase(example_interactive),
        ),
        TitledSection(
            "With Label",
            P("Combine with text labels for more context:"),
            ComponentShowcase(example_with_label),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
def Progress(
    value: Union[int, float, Signal, None] = None,  # Progress value (0-max_value)
    max_value: int = 100,                            # Maximum value
    indeterminate: bool = False,                     # Animated loading state
    size: str = "md",                                # "sm", "md", "lg"
    cls: str = "",                                   # Additional CSS classes
    **attrs                                          # Additional HTML attributes
) -> HtmlString

# Examples
Progress(value=65)                    # 65% progress
Progress(value=50, size="lg")         # Large progress bar
Progress(indeterminate=True)          # Loading state
Progress(value=25, max_value=50)      # Custom max value (shows 50%)
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Accessibility",
            Ul(
                Li("role='progressbar' - Identifies element as progress indicator"),
                Li("aria-valuemin='0' - Minimum progress value"),
                Li("aria-valuemax - Maximum progress value"),
                Li("aria-valuenow - Current progress value (determinate mode)"),
                Li("aria-busy='true' - Indicates loading state (indeterminate mode)"),
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/progress")
@template(title="Progress Component Documentation")
def progress_page():
    return page

@on("page.progress")
async def get_progress(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.progress")