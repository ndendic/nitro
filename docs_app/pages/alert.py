"""Alert component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter

from nitro.infrastructure.html.components import Alert, AlertTitle, AlertDescription
from nitro.infrastructure.events import on, emit_elements

router: APIRouter = APIRouter()


def example_basic():
    return Alert(
        AlertTitle("Heads up!"),
        AlertDescription("You can add components to your app using the cli."),
    )


def example_variants():
    return Div(
        Alert(
            AlertTitle("Default Alert"),
            AlertDescription("This is a default alert for general information."),
            variant="default",
        ),
        Alert(
            AlertTitle("Info"),
            AlertDescription("This is an informational message for the user."),
            variant="info",
        ),
        Alert(
            AlertTitle("Success"),
            AlertDescription("Your changes have been saved successfully."),
            variant="success",
        ),
        Alert(
            AlertTitle("Warning"),
            AlertDescription("Please review your input before proceeding."),
            variant="warning",
        ),
        Alert(
            AlertTitle("Error"),
            AlertDescription("There was a problem processing your request."),
            variant="error",
        ),
        Alert(
            AlertTitle("Destructive"),
            AlertDescription("This action cannot be undone."),
            variant="destructive",
        ),
        cls="space-y-4"
    )


def example_with_icons():
    return Div(
        Alert(
            Div(
                AlertTitle("Information"),
                cls="flex items-center gap-2"
            ),
            AlertDescription("This alert includes an icon for visual emphasis."),
            variant="info",
            icon="bot-message-square",
        ),
        Alert(
            Div(
                AlertTitle("Success"),
                cls="flex items-center gap-2"
            ),
            AlertDescription("Your account has been created successfully."),
            variant="success",
            icon="file-check",
        ),
        Alert(
            Div(
                AlertTitle("Warning"),
                cls="flex items-center gap-2"
            ),
            AlertDescription("Your session will expire in 5 minutes."),
            variant="warning",
            icon="alert-triangle",
        ),
        Alert(
            Div(
                AlertTitle("Security Error"),
                cls="flex items-center gap-2"
            ),
            AlertDescription("Your account has been compromised. Please reset your password."),
            variant="error",
            icon="shield-alert",
        ),
        cls="space-y-4"
    )


def example_title_only():
    return Div(
        Alert(AlertTitle("A simple alert with just a title"), variant="info"),
        Alert(AlertTitle("Another title-only alert"), variant="warning"),
        cls="space-y-4"
    )


def example_custom_content():
    return Alert(
        AlertTitle("Update Available"),
        AlertDescription(
            "A new version of the application is available. ",
            A("Click here to update", href="#", cls="underline font-medium"),
            " or dismiss this message.",
        ),
        variant="info",
    )


page = Div(
        H1("Alert Component"),
        P(
            "Alerts are used to communicate a state that affects a system, "
            "feature, or page. They display contextual feedback messages."
        ),
        TitledSection(
            "Design Philosophy",
            P("Alerts follow accessibility best practices:"),
            Ul(
                Li("Uses role='alert' for screen reader announcements"),
                Li("Semantic variants communicate meaning through color"),
                Li("Compound components (AlertTitle, AlertDescription) for structure"),
                Li("Flexible content - can include icons, links, and custom elements"),
            ),
        ),
        TitledSection(
            "Basic Alert",
            P("A simple alert with title and description:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "Variants",
            P("Six variants for different message types:"),
            ComponentShowcase(example_variants),
        ),
        TitledSection(
            "With Icons",
            P("Add icons for better visual communication:"),
            ComponentShowcase(example_with_icons),
        ),
        TitledSection(
            "Title Only",
            P("Alerts can be used with just a title:"),
            ComponentShowcase(example_title_only),
        ),
        TitledSection(
            "Custom Content",
            P("Alert description can contain links and other elements:"),
            ComponentShowcase(example_custom_content),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
def Alert(
    *children,                              # Alert content (typically AlertTitle/AlertDescription)
    variant: str = "default",               # default, info, success, warning, error, destructive
    cls: str = "",                          # Additional CSS classes
    **attrs                                 # Additional HTML attributes
) -> HtmlString

def AlertTitle(
    *children,                              # Title content
    cls: str = "",                          # Additional CSS classes
    **attrs                                 # Additional HTML attributes
) -> HtmlString

def AlertDescription(
    *children,                              # Description content
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

@router.get("/xtras/alert")
@template(title="Alert Component Documentation")
def alert_page():
    return page

@on("page.alert")
async def get_alert(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.alert")