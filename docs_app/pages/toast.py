"""Toast component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import (
    Toast,
    Toaster,
    ToastTrigger,
    Button,
)

router: APIRouter = APIRouter()


def example_basic():
    """Basic toast example with toaster container."""
    return Div(
        # Toaster container for this example
        Div(
            Toast(
                id="basic-toast",
                title="Heads up!",
                description="You can add components to your app using the cli.",
            ),
            cls="toaster",
            data_align="end",
            style="position: relative; bottom: auto; right: auto;",  # Override fixed positioning for demo
        ),
        Button(
            "Show Toast",
            on_click="document.getElementById('basic-toast').setAttribute('aria-hidden', 'false')",
        ),
        cls="relative min-h-[100px]",
    )


def example_variants():
    """All variant examples with a shared toaster."""
    return Div(
        # Toaster container for variant toasts
        Div(
            Toast(
                id="default-toast",
                title="Default",
                description="This is a default notification.",
                variant="default",
            ),
            Toast(
                id="success-toast",
                title="Success!",
                description="Your changes have been saved successfully.",
                variant="success",
            ),
            Toast(
                id="error-toast",
                title="Error",
                description="There was a problem with your request.",
                variant="error",
            ),
            Toast(
                id="warning-toast",
                title="Warning",
                description="This action may have unintended consequences.",
                variant="warning",
            ),
            Toast(
                id="info-toast",
                title="Info",
                description="Here's some helpful information.",
                variant="info",
            ),
            cls="toaster",
            data_align="end",
            style="position: relative; bottom: auto; right: auto;",
        ),
        # Trigger buttons
        Div(
            Button(
                "Default",
                on_click="document.getElementById('default-toast').setAttribute('aria-hidden', 'false')",
                variant="outline",
            ),
            Button(
                "Success",
                on_click="document.getElementById('success-toast').setAttribute('aria-hidden', 'false')",
                variant="outline",
            ),
            Button(
                "Error",
                on_click="document.getElementById('error-toast').setAttribute('aria-hidden', 'false')",
                variant="outline",
            ),
            Button(
                "Warning",
                on_click="document.getElementById('warning-toast').setAttribute('aria-hidden', 'false')",
                variant="outline",
            ),
            Button(
                "Info",
                on_click="document.getElementById('info-toast').setAttribute('aria-hidden', 'false')",
                variant="outline",
            ),
            cls="flex flex-wrap gap-2 mt-4",
        ),
        cls="relative",
    )


def example_with_action():
    """Toast with action button."""
    return Div(
        Div(
            Toast(
                id="action-toast",
                title="Update Available",
                description="A new version is available. Would you like to update?",
                variant="info",
                action_label="Update",
                action_onclick="console.log('Update clicked')",
            ),
            cls="toaster",
            data_align="end",
            style="position: relative; bottom: auto; right: auto;",
        ),
        Button(
            "Show Toast with Action",
            on_click="document.getElementById('action-toast').setAttribute('aria-hidden', 'false')",
        ),
        cls="relative min-h-[100px]",
    )


def example_persistent():
    """Persistent toast that doesn't auto-dismiss."""
    return Div(
        Div(
            Toast(
                id="persistent-toast",
                title="Important Notice",
                description="This toast will not auto-dismiss. You must close it manually.",
                variant="warning",
                duration=0,  # No auto-dismiss
            ),
            cls="toaster",
            data_align="end",
            style="position: relative; bottom: auto; right: auto;",
        ),
        Button(
            "Show Persistent Toast",
            on_click="document.getElementById('persistent-toast').setAttribute('aria-hidden', 'false')",
        ),
        cls="relative min-h-[100px]",
    )


def example_minimal():
    """Minimal toast without dismiss button."""
    return Div(
        Div(
            Toast(
                id="minimal-toast",
                title="File uploaded successfully",
                variant="success",
                show_icon=True,
                dismissible=False,  # No dismiss button
            ),
            cls="toaster",
            data_align="end",
            style="position: relative; bottom: auto; right: auto;",
        ),
        Button(
            "Show Minimal Toast",
            on_click="document.getElementById('minimal-toast').setAttribute('aria-hidden', 'false')",
        ),
        cls="relative min-h-[100px]",
    )


def example_toaster():
    """Documentation for Toaster component usage."""
    return Div(
        P(
            "The Toaster component provides a container for dynamic toast injection. "
            "Toasts can be added via HTMX, JavaScript events, or server-sent events.",
            cls="text-muted-foreground mb-4",
        ),
        CodeBlock(
            """
# In your base layout
Toaster(position="bottom-right")

# Add toast via HTMX
Button(
    "Show Toast",
    hx_get="/api/toast/success",
    hx_target="#toaster",
    hx_swap="beforeend",
)

# Or via JavaScript event
Button(
    "Show via Event",
    on_click="document.dispatchEvent(new CustomEvent('basecoat:toast', {detail: {category: 'success', title: 'Hello!'}}))",
)
""",
            code_cls="language-python",
        ),
    )


page = Div(
        # Global toaster for the page (for potential dynamic toast injection)
        Toaster(position="bottom-right"),
        H1("Toast Component"),
        P(
            "Toast notifications are used to display brief, non-blocking messages "
            "to the user. They appear temporarily and can auto-dismiss."
        ),
        TitledSection(
            "Design Philosophy",
            P("Toasts follow accessibility and UX best practices:"),
            Ul(
                Li("Uses role='status' for non-intrusive announcements"),
                Li("Auto-dismisses after configurable duration"),
                Li("Manual dismiss option always available"),
                Li("Stacking support for multiple toasts"),
                Li("Position options for flexible placement"),
            ),
        ),
        TitledSection(
            "Basic Toast",
            P("A simple toast notification with title and description. Click the button to show the toast:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "Variants",
            P("Five variants for different message types - default, success, error, warning, info:"),
            ComponentShowcase(example_variants),
        ),
        TitledSection(
            "With Action Button",
            P("Toasts can include an action button for user interaction:"),
            ComponentShowcase(example_with_action),
        ),
        TitledSection(
            "Persistent Toast",
            P("Set duration to 0 to create a toast that doesn't auto-dismiss:"),
            ComponentShowcase(example_persistent),
        ),
        TitledSection(
            "Minimal Toast",
            P("A simplified toast without the dismiss button:"),
            ComponentShowcase(example_minimal),
        ),
        TitledSection(
            "Using Toaster",
            P("For dynamic toast injection:"),
            example_toaster(),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
def ToastProvider(
    *children,
    position: str = "bottom-right",  # top-left, top-center, top-right, bottom-left, bottom-center, bottom-right
    cls: str = "",
    **attrs
) -> HtmlString

def Toaster(
    position: str = "bottom-right",
    cls: str = "",
    **attrs
) -> HtmlString

def Toast(
    *children,
    id: str,                         # Required unique identifier
    title: str = "",                 # Toast title
    description: str = "",           # Toast description
    variant: str = "default",        # default, success, error, warning, info
    duration: int = 5000,            # Auto-dismiss time in ms (0 = no auto-dismiss)
    show_icon: bool = True,          # Show variant icon
    dismissible: bool = True,        # Show dismiss button
    visible: bool = False,           # Initial visibility (default hidden)
    action_label: str = "",          # Action button text
    action_onclick: str = "",        # Action button handler
    cls: str = "",
    **attrs
) -> HtmlString

def ToastTrigger(
    *children,
    toast_id: str = None,            # ID of existing toast to show
    variant: str = "default",        # Variant for new toasts
    title: str = "",                 # Title for new toasts
    description: str = "",           # Description for new toasts
    duration: int = 5000,
    cls: str = "",
    **attrs
) -> HtmlString

def ToastClose(
    *children,
    toast_id: str,                   # ID of toast to close
    cls: str = "",
    **attrs
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Accessibility",
            Ul(
                Li("role='status' - Non-intrusive announcement"),
                Li("aria-atomic='true' - Entire toast announced"),
                Li("aria-hidden for show/hide state"),
                Li("Keyboard accessible dismiss buttons"),
                Li("Icons have aria-hidden='true'"),
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/toast")
@template(title="Toast Component Documentation")
def toast_page():
    return page

@on("page.toast")
async def get_toast(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.toast")