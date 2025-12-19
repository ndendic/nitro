"""Theme Switcher component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi import APIRouter
from fastapi.requests import Request
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import (
    ThemeSwitcher,
    ThemeSwitcherDropdown,
    ThemeSelect,
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
)
from rusty_tags.datastar import Signals

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        P("Click the button to cycle through themes: Light -> Dark -> System",
          cls="text-sm text-muted-foreground mb-4"),
        Div(
            ThemeSwitcher(signal="demo_theme_1"),
            Span(
                "Current: ",
                Span(data_text="$demo_theme_1", cls="font-semibold capitalize"),
                cls="ml-4 text-sm",
            ),
            cls="flex items-center gap-2",
        ),
    )


def example_variants():
    return Div(
        P("Different button variants and sizes:", cls="text-sm text-muted-foreground mb-4"),
        Div(
            Div(
                P("Ghost (default):", cls="text-xs text-muted-foreground mb-2"),
                ThemeSwitcher(signal="demo_ghost", variant="ghost"),
            ),
            Div(
                P("Outline:", cls="text-xs text-muted-foreground mb-2"),
                ThemeSwitcher(signal="demo_outline", variant="outline"),
            ),
            Div(
                P("Secondary:", cls="text-xs text-muted-foreground mb-2"),
                ThemeSwitcher(signal="demo_secondary", variant="secondary"),
            ),
            cls="flex gap-8",
        ),
    )


def example_sizes():
    return Div(
        P("Different button sizes:", cls="text-sm text-muted-foreground mb-4"),
        Div(
            Div(
                P("Small:", cls="text-xs text-muted-foreground mb-2"),
                ThemeSwitcher(signal="demo_sm", size="sm"),
            ),
            Div(
                P("Default:", cls="text-xs text-muted-foreground mb-2"),
                ThemeSwitcher(signal="demo_default", size="default"),
            ),
            Div(
                P("Large:", cls="text-xs text-muted-foreground mb-2"),
                ThemeSwitcher(signal="demo_lg", size="lg"),
            ),
            cls="flex items-end gap-8",
        ),
    )


def example_dropdown():
    return Div(
        P("Dropdown menu for explicit theme selection:", cls="text-sm text-muted-foreground mb-4"),
        Div(
            ThemeSwitcherDropdown(signal="demo_dropdown"),
            Span(
                "Current: ",
                Span(data_text="$demo_dropdown", cls="font-semibold capitalize"),
                cls="ml-4 text-sm",
            ),
            cls="flex items-center gap-2",
        ),
    )


def example_theme_select():
    return Div(
        P("Select a named theme:", cls="text-sm text-muted-foreground mb-4"),
        ThemeSelect(
            signal="demo_theme_select",
            options=[
                {"value": "default", "label": "Default"},
                {"value": "claude", "label": "Claude"},
                {"value": "candy", "label": "Candy"},
                {"value": "neo-brutal", "label": "Neo Brutalism"},
            ],
            default_theme="default",
            cls="w-48",
        ),
    )


def example_in_card():
    return Card(
        CardHeader(
            CardTitle("Theme Settings"),
            CardDescription("Customize the appearance of the application."),
        ),
        CardContent(
            Div(
                Div(
                    P("Mode", cls="text-sm font-medium"),
                    P("Switch between light and dark mode.", cls="text-xs text-muted-foreground"),
                ),
                ThemeSwitcher(signal="card_theme_mode"),
                cls="flex items-center justify-between",
            ),
        ),
        cls="w-full max-w-md",
    )


def example_persistence():
    return Div(
        P(
            "Theme preference is persisted using Datastar's data-persist. "
            "Refresh the page to verify the theme is remembered.",
            cls="text-sm text-muted-foreground mb-4",
        ),
        Div(
            ThemeSwitcher(signal="persist_demo", persist=True),
            Span(
                "Current: ",
                Span(data_text="$persist_demo", cls="font-semibold capitalize"),
                cls="ml-4 text-sm",
            ),
            cls="flex items-center gap-2",
        ),
        P(
            "Note: This demo uses a separate signal to avoid conflicting with "
            "the main page theme.",
            cls="text-xs text-muted-foreground mt-4 italic",
        ),
    )


page = Div(
        H1("Theme Switcher Component"),
        P(
            "A theme toggle component for switching between light, dark, and system modes. "
            "Also includes a dropdown variant for explicit selection and a theme select "
            "for named themes. Supports persistence via Datastar's data-persist."
        ),
        TitledSection(
            "Design Philosophy",
            P("Theme Switcher follows these principles:"),
            Ul(
                Li("Three modes: light, dark, system (follows OS preference)"),
                Li("Cycle pattern for quick switching: light -> dark -> system -> light"),
                Li("Visual icon feedback: sun for light, moon for dark, laptop for system"),
                Li("Persistence support via data-persist for remembering user preference"),
                Li("Applies theme by toggling 'dark' class on document root"),
            ),
        ),
        TitledSection(
            "Basic Usage",
            P("Simple theme toggle button that cycles through modes:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "Button Variants",
            P("Available button styling variants:"),
            ComponentShowcase(example_variants),
        ),
        TitledSection(
            "Button Sizes",
            P("Available button sizes:"),
            ComponentShowcase(example_sizes),
        ),
        TitledSection(
            "Dropdown Variant",
            P("Dropdown menu for explicit theme selection without cycling:"),
            ComponentShowcase(example_dropdown),
        ),
        TitledSection(
            "Named Theme Select",
            P("For named themes (color schemes) rather than light/dark modes:"),
            ComponentShowcase(example_theme_select),
        ),
        TitledSection(
            "In a Card",
            P("Theme switcher integrated in a settings card:"),
            ComponentShowcase(example_in_card),
        ),
        TitledSection(
            "Persistence",
            P("Theme preference persisted across page refreshes:"),
            ComponentShowcase(example_persistence),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
# ThemeSwitcher - Cycling button for light/dark/system
def ThemeSwitcher(
    signal: str = "theme_mode",      # Datastar signal name
    default_theme: str = "system",   # Initial theme (light, dark, system)
    persist: bool = True,            # Persist with data-persist
    size: str = "default",           # Button size (sm, default, lg, icon)
    variant: str = "ghost",          # Button variant (ghost, outline, secondary)
    cls: str = "",
    **attrs
) -> HtmlString

# ThemeSwitcherDropdown - Dropdown menu for theme selection
def ThemeSwitcherDropdown(
    signal: str = "theme_mode",
    default_theme: str = "system",
    persist: bool = True,
    cls: str = "",
    **attrs
) -> HtmlString

# ThemeSelect - Select dropdown for named themes
def ThemeSelect(
    signal: str = "theme",           # Datastar signal name
    options: list[dict] = None,      # [{value: "name", label: "Label"}]
    default_theme: str = "default",
    persist: bool = True,
    cls: str = "",
    **attrs
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Theme Application",
            P("How themes are applied:"),
            Ul(
                Li("'dark' class is added/removed from document.documentElement"),
                Li("System mode respects prefers-color-scheme media query"),
                Li("Named themes set data-theme attribute on document root"),
                Li("CSS variables change based on dark class or data-theme"),
            ),
        ),
        TitledSection(
            "Key Behaviors",
            Ul(
                Li("Click cycles through: light -> dark -> system -> light"),
                Li("Icons change to indicate current mode"),
                Li("System mode follows OS dark/light preference"),
                Li("Preference persists in localStorage when persist=True"),
                Li("Tooltip shows current theme mode"),
            ),
        ),
        TitledSection(
            "Accessibility",
            Ul(
                Li("aria-label describes the action ('Toggle theme')"),
                Li("Button is keyboard accessible"),
                Li("Tooltip provides additional context"),
                Li("Visual icon feedback for current state"),
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/theme-switcher")
@template(title="Theme Switcher Component Documentation")
def theme_switcher_page():
    return page

@on("page.theme-switcher")
async def get_theme_switcher(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.theme-switcher")