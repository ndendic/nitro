"""Breadcrumb component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import on, emit_elements

from nitro.infrastructure.html.components import (
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbSeparator,
    BreadcrumbEllipsis,
)

router: APIRouter = APIRouter()


def example_basic():
    """Basic breadcrumb navigation."""
    return Breadcrumb(
        BreadcrumbItem("Home", href="#"),
        BreadcrumbSeparator(),
        BreadcrumbItem("Components", href="#"),
        BreadcrumbSeparator(),
        BreadcrumbItem("Breadcrumb", current=True),
    )


def example_with_icons():
    """Breadcrumb with icons."""
    return Breadcrumb(
        BreadcrumbItem(LucideIcon("home", cls="size-4"), href="#"),
        BreadcrumbSeparator(),
        BreadcrumbItem("Library", href="#"),
        BreadcrumbSeparator(),
        BreadcrumbItem("Data", current=True),
    )


def example_custom_separator():
    """Breadcrumb with custom separators."""
    return Div(
        # Slash separator
        Div(
            P("Slash separator:", cls="text-sm text-muted-foreground mb-2"),
            Breadcrumb(
                BreadcrumbItem("Home", href="#"),
                BreadcrumbSeparator(icon="slash"),
                BreadcrumbItem("Components", href="#"),
                BreadcrumbSeparator(icon="slash"),
                BreadcrumbItem("Breadcrumb", current=True),
            ),
            cls="mb-4",
        ),
        # Arrow separator
        Div(
            P("Arrow separator:", cls="text-sm text-muted-foreground mb-2"),
            Breadcrumb(
                BreadcrumbItem("Home", href="#"),
                BreadcrumbSeparator(icon="arrow-right"),
                BreadcrumbItem("Components", href="#"),
                BreadcrumbSeparator(icon="arrow-right"),
                BreadcrumbItem("Breadcrumb", current=True),
            ),
        ),
    )


def example_with_ellipsis():
    """Breadcrumb with collapsed items (ellipsis)."""
    return Breadcrumb(
        BreadcrumbItem("Home", href="#"),
        BreadcrumbSeparator(),
        BreadcrumbEllipsis(),
        BreadcrumbSeparator(),
        BreadcrumbItem("Components", href="#"),
        BreadcrumbSeparator(),
        BreadcrumbItem("Breadcrumb", current=True),
    )


def example_long_path():
    """Breadcrumb with longer navigation path."""
    return Breadcrumb(
        BreadcrumbItem("Dashboard", href="#"),
        BreadcrumbSeparator(),
        BreadcrumbItem("Settings", href="#"),
        BreadcrumbSeparator(),
        BreadcrumbItem("Profile", href="#"),
        BreadcrumbSeparator(),
        BreadcrumbItem("Security", href="#"),
        BreadcrumbSeparator(),
        BreadcrumbItem("Two-Factor Auth", current=True),
    )


page = Div(
        H1("Breadcrumb Component"),
        P(
            "A navigation component that helps users understand their location "
            "within a website's hierarchy and navigate back to parent pages."
        ),
        TitledSection(
            "Design Philosophy",
            P("Breadcrumbs follow Basecoat patterns:"),
            Ul(
                Li("Uses semantic nav and ol/li elements"),
                Li("aria-label='Breadcrumb' on nav container"),
                Li("aria-current='page' on current item"),
                Li("Separators hidden from screen readers"),
                Li("Tailwind utility classes for styling"),
            ),
        ),
        TitledSection(
            "Basic Usage",
            P("A simple breadcrumb navigation with text links:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "With Icons",
            P("Use icons for visual enhancement (home icon is common):"),
            ComponentShowcase(example_with_icons),
        ),
        TitledSection(
            "Custom Separators",
            P("Change the separator icon from the default chevron:"),
            ComponentShowcase(example_custom_separator),
        ),
        TitledSection(
            "With Ellipsis",
            P("Collapse middle items when the path is too long:"),
            ComponentShowcase(example_with_ellipsis),
        ),
        TitledSection(
            "Long Path",
            P("Full breadcrumb trail for deep navigation:"),
            ComponentShowcase(example_long_path),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
def Breadcrumb(
    *children,                  # BreadcrumbItem and BreadcrumbSeparator components
    cls: str = "",              # Additional CSS classes
    **attrs                     # Additional HTML attributes
) -> HtmlString

def BreadcrumbItem(
    *children,                  # Item content (text, icons, etc.)
    href: str = "",             # Link URL (optional)
    current: bool = False,      # Whether this is the current page
    cls: str = "",              # Additional CSS classes
    **attrs                     # Additional HTML attributes
) -> HtmlString

def BreadcrumbSeparator(
    icon: str = "chevron-right",  # Lucide icon name for separator
    cls: str = "",                # Additional CSS classes
    **attrs                       # Additional HTML attributes
) -> HtmlString

def BreadcrumbEllipsis(
    cls: str = "",              # Additional CSS classes
    **attrs                     # Additional HTML attributes
) -> HtmlString

# Usage example
Breadcrumb(
    BreadcrumbItem("Home", href="/"),
    BreadcrumbSeparator(),
    BreadcrumbItem("Products", href="/products"),
    BreadcrumbSeparator(),
    BreadcrumbItem("Shoes", current=True),
)
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Accessibility",
            Ul(
                Li("nav element with aria-label='Breadcrumb'"),
                Li("Ordered list (ol) for semantic structure"),
                Li("aria-current='page' on current item"),
                Li("Separators have aria-hidden='true' and role='presentation'"),
                Li("Links are keyboard navigable"),
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/breadcrumb")
@template(title="Breadcrumb Component Documentation")
def breadcrumb_page():
    return page

@on("page.breadcrumb")
async def get_breadcrumb(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.breadcrumb")