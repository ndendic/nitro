"""Switch component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.responses import HTMLResponse
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signal, Signals

from nitro.infrastructure.html.components import Switch, Label

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Switch("Enable notifications", id="notifications"),
        cls="flex flex-col gap-2"
    )


def example_with_binding():
    sigs = Signals(notifications=True, dark_mode=False, auto_save=True)
    return Div(
        Div(
            Switch("Enable notifications", id="notifications", bind=sigs.notifications),
            cls="mb-3"
        ),
        Div(
            Switch("Dark mode", id="dark_mode", bind=sigs.dark_mode),
            cls="mb-3"
        ),
        Div(
            Switch("Auto-save documents", id="auto_save", bind=sigs.auto_save),
            cls="mb-3"
        ),
        Div(
            P("Notifications: ", Span(data_text="$notifications ? 'Enabled' : 'Disabled'")),
            P("Dark mode: ", Span(data_text="$dark_mode ? 'On' : 'Off'")),
            P("Auto-save: ", Span(data_text="$auto_save ? 'Enabled' : 'Disabled'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="flex flex-col"
    )


def example_settings_panel():
    sigs = Signals(
        email_notifications=True,
        push_notifications=False,
        marketing_emails=False,
        weekly_digest=True
    )
    return Div(
        H3("Notification Settings", cls="text-lg font-semibold mb-4"),
        Div(
            Div(
                Div(
                    H4("Email Notifications", cls="font-medium"),
                    P("Receive notifications via email", cls="text-sm text-muted-foreground"),
                    cls="flex-1"
                ),
                Switch(id="email_notifications", bind=sigs.email_notifications),
                cls="flex items-center justify-between py-3 border-b"
            ),
            Div(
                Div(
                    H4("Push Notifications", cls="font-medium"),
                    P("Receive push notifications", cls="text-sm text-muted-foreground"),
                    cls="flex-1"
                ),
                Switch(id="push_notifications", bind=sigs.push_notifications),
                cls="flex items-center justify-between py-3 border-b"
            ),
            Div(
                Div(
                    H4("Marketing Emails", cls="font-medium"),
                    P("Receive marketing and promotional emails", cls="text-sm text-muted-foreground"),
                    cls="flex-1"
                ),
                Switch(id="marketing_emails", bind=sigs.marketing_emails),
                cls="flex items-center justify-between py-3 border-b"
            ),
            Div(
                Div(
                    H4("Weekly Digest", cls="font-medium"),
                    P("Receive a weekly summary email", cls="text-sm text-muted-foreground"),
                    cls="flex-1"
                ),
                Switch(id="weekly_digest", bind=sigs.weekly_digest),
                cls="flex items-center justify-between py-3"
            ),
            cls="rounded-lg border p-4"
        ),
        signals=sigs,
        cls="max-w-md"
    )


def example_disabled():
    return Div(
        Div(
            Switch("Enabled switch", id="enabled"),
            cls="mb-3"
        ),
        Div(
            Switch("Disabled switch (off)", id="disabled_off", disabled=True),
            cls="mb-3"
        ),
        Div(
            Switch("Disabled switch (on)", id="disabled_on", disabled=True, checked=True),
            cls="mb-3"
        ),
        cls="flex flex-col"
    )


def example_in_field():
    sigs = Signals(feature_enabled=False)
    return Div(
        Div(
            Switch("Enable experimental feature", id="feature_enabled", bind=sigs.feature_enabled),
            P("Warning: This feature is still in development.", cls="text-muted-foreground text-sm mt-1"),
            cls="field"
        ),
        Div(
            P("Feature status: ", Span(data_text="$feature_enabled ? 'Enabled' : 'Disabled'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
    )


def example_without_label():
    return Div(
        Div(
            Switch(id="standalone"),
            Label("Standalone switch (separate label)", html_for="standalone", cls="ml-2"),
            cls="flex items-center"
        ),
        cls="flex flex-col gap-2"
    )


@router.get("/xtras/switch")
@template(title="Switch Component Documentation")
def switch_docs():
    return Div(
        H1("Switch Component"),
        P(
            "Toggle switch using native checkbox with role=\"switch\" for Basecoat styling. "
            "Uses smooth CSS animations and supports Datastar two-way binding for reactive state management."
        ),
        Section(
            "Basic Switch",
            P("A simple toggle switch with integrated label:"),
            ComponentShowcase(example_basic),
        ),
        Section(
            "With Datastar Binding",
            P("Switches with two-way binding showing live state:"),
            ComponentShowcase(example_with_binding),
        ),
        Section(
            "Settings Panel Example",
            P("A realistic settings panel with multiple switches:"),
            ComponentShowcase(example_settings_panel),
        ),
        Section(
            "Disabled State",
            P("Switches can be disabled in both on and off states:"),
            ComponentShowcase(example_disabled),
        ),
        Section(
            "In Field Context",
            P("Inside a .field container for form layout with description text:"),
            ComponentShowcase(example_in_field),
        ),
        Section(
            "Without Integrated Label",
            P("Switch without children returns just the input, allowing custom label placement:"),
            ComponentShowcase(example_without_label),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
def Switch(
    *children,                   # Label content (text, icons, etc.)
    id: str,                     # Unique identifier (required)
    bind: Signal = None,         # Datastar Signal for two-way binding
    checked: bool = False,       # Initial checked state (when no bind)
    disabled: bool = False,      # Whether switch is disabled
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Key Differences from Checkbox",
            CodeBlock(
                """
# Switch uses role="switch" for Basecoat styling
# This triggers special CSS with smooth sliding animation

# The HTML output:
<input type="checkbox" role="switch" id="..." />

# Checkbox output (no role attribute):
<input type="checkbox" id="..." />

# Use Switch for binary on/off toggles
# Use Checkbox for agreement/selection scenarios
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Datastar Binding",
            CodeBlock(
                """
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.html.components import Switch

# Create signals
settings = Signals(notifications=True, dark_mode=False)

# Bind to signals
Switch("Enable notifications", id="notifications", bind=settings.notifications)
Switch("Dark mode", id="dark_mode", bind=settings.dark_mode)

# The switch state will sync with the signal
# Signal value: True when on, False when off
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
    )
