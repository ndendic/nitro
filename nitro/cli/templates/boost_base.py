"""Boost base.py template for new Nitro projects."""

# --- Framework config ---

FRAMEWORK_IMPORTS = {
    "sanic": "from sanic.response import html as sanic_html",
    "fastapi": "from fastapi.responses import HTMLResponse",
}

FRAMEWORK_WRAP_IN = {
    "sanic": "sanic_html",
    "fastapi": "HTMLResponse",
}

# --- Template: blank ---

BLANK_TEMPLATE = '''\
"""
Nitro base template - Your starting point for building with Nitro.
Edit this file to customize your page layout and add routes.
"""

from nitro import *
from nitro.html import *
from nitro.html.components import *  # Card, Badge, LucideIcon, etc.
from nitro.html import template as templ, page_template
{framework_import}

# Page template configuration
# Add more options as needed: highlightjs=True, charts=True, datastar=True
htmlkws = dict(lang="en", data_resize="true")
page = page_template(htmlkw=htmlkws, lucide=True)


@templ
def template(content, title: str = "Nitro App"):
    return page(
        Main(
            Div(
                content,
                cls="min-h-screen max-w-4xl mx-auto px-4 py-8",
            ),
        ),
        title=title,
        wrap_in={wrap_in},
    )


def FeatureCard(icon, title, description):
    return Div(
        Div(
            LucideIcon(icon, cls="size-5 text-primary"),
            cls="flex items-center justify-center size-10 rounded-lg bg-primary/10 mb-3",
        ),
        H3(title, cls="font-semibold text-sm mb-1"),
        P(description, cls="text-xs text-muted-foreground leading-relaxed"),
        cls="p-4 rounded-xl border border-border/50 bg-card hover:border-primary/30 hover:shadow-sm transition-all duration-200",
    )


@template
def index():
    """Edit base.py to customize this page."""
    return Div(
        # Hero
        Div(
            Div(
                LucideIcon("zap", cls="size-5 text-primary"),
                cls="flex items-center justify-center size-12 rounded-xl bg-primary/10 mb-6 mx-auto",
            ),
            H1("Nitro ", Span("Boosted", cls="text-primary"), cls="text-4xl font-bold tracking-tight mb-3"),
            P("Your app is ready. Start building something great.",
              cls="text-lg text-muted-foreground max-w-md mx-auto"),
            cls="text-center pt-16 pb-12",
        ),
        # Features
        Div(
            FeatureCard("database", "Active Record", "Entity-centric persistence with rich domain models."),
            FeatureCard("layout-template", "UI Components", "High-performance HTML generation with RustyTags."),
            FeatureCard("radio", "Event Routing", "Decoupled domain events with auto-routing decorators."),
            cls="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-12",
        ),
        # Next steps
        Div(
            H2("Next steps", cls="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4"),
            Div(
                Div(
                    Span("1", cls="flex items-center justify-center size-6 rounded-full bg-primary text-primary-foreground text-xs font-bold"),
                    Div(
                        P("Edit ", Code("base.py", cls="text-primary text-xs"), cls="text-sm font-medium"),
                        P("Customize this page and add routes.", cls="text-xs text-muted-foreground"),
                        cls="ml-3",
                    ),
                    cls="flex items-start",
                ),
                Div(
                    Span("2", cls="flex items-center justify-center size-6 rounded-full bg-primary text-primary-foreground text-xs font-bold"),
                    Div(
                        P("Define entities", cls="text-sm font-medium"),
                        P("Create domain models with built-in persistence.", cls="text-xs text-muted-foreground"),
                        cls="ml-3",
                    ),
                    cls="flex items-start",
                ),
                Div(
                    Span("3", cls="flex items-center justify-center size-6 rounded-full bg-primary text-primary-foreground text-xs font-bold"),
                    Div(
                        P("Add reactivity", cls="text-sm font-medium"),
                        P("Use Datastar signals for live updates.", cls="text-xs text-muted-foreground"),
                        cls="ml-3",
                    ),
                    cls="flex items-start",
                ),
                cls="space-y-4",
            ),
            cls="border-t border-border/50 pt-8",
        ),
    )
'''

# --- Template: app (sidebar + navbar) ---

APP_COMPONENTS = '''\
"""
Layout components - Sidebar and Navbar.
Edit this file to customize navigation and branding.
"""

from nitro.html import *
from nitro.html.components import *


THEMES = [
    ("Default", "default"),
    ("Nitro", "nitro"),
    ("Claude", "claude"),
    ("Candy", "candy"),
    ("Neo Brutalism", "neo-brutal"),
    ("Dark Matter", "darkmatter"),
    ("Gruvbox", "gruvbox"),
]


def ThemeSelector():
    return Select(
        Optgroup(
            *[Option(name, value=value) for name, value in THEMES],
        ),
        bind="theme",
        on_change="document.documentElement.setAttribute('data-theme', $theme);",
        cls="select w-[180px]",
    )


def ThemeSwitcher():
    return Button(
        LucideIcon("sun"),
        on_click="$darkMode = !$darkMode; $darkMode ? document.documentElement.classList.add('dark') : document.documentElement.classList.remove('dark');",
        cls="btn",
    )


def Navbar():
    return Header(
        Div(
            Button(
                LucideIcon("panel-left"),
                type="button",
                on_click="$sidebar_open = !$sidebar_open",
                cls="mr-auto",
                variant="ghost",
            ),
            Div(
                ThemeSelector(),
                ThemeSwitcher(),
                cls="flex items-center gap-2",
            ),
            cls="flex h-14 w-full items-center gap-2 px-4",
        ),
        cls="bg-background/80 backdrop-blur-sm sticky inset-x-0 top-0 isolate flex shrink-0 items-center gap-2 border-b border-border/50 z-10",
    )


def Sidebar():
    return Aside(
        Nav(
            Header(
                A(
                    Div(
                        LucideIcon("zap", cls="h-4 w-4"),
                        cls="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg",
                    ),
                    Div(
                        Span("Nitro", Span("App", cls="truncate font-light"), cls="truncate font-bold"),
                        Span("v0.1.0", cls="truncate text-xs text-muted-foreground"),
                        cls="grid flex-1 text-left text-sm leading-tight",
                    ),
                    href="/",
                    aria_current="page",
                    cls="btn-ghost p-2 h-12 w-full justify-start",
                )
            ),
            Section(
                Div(
                    H3("Navigation", id="group-label-nav"),
                    Ul(
                        Li(A(LucideIcon("home"), Span("Dashboard"), href="/")),
                        Li(
                            Details(
                                Summary(
                                    LucideIcon("database"),
                                    "Entities",
                                    aria_controls="submenu-entities",
                                ),
                                Ul(
                                    Li(A(Span("All Entities"), href="#")),
                                    Li(A(Span("Create New"), href="#")),
                                    id="submenu-entities",
                                ),
                                id="submenu-entities-details",
                            )
                        ),
                        Li(
                            Details(
                                Summary(
                                    LucideIcon("settings-2"),
                                    "Settings",
                                    aria_controls="submenu-settings",
                                ),
                                Ul(
                                    Li(A(Span("General"), href="#")),
                                    Li(A(Span("Theme"), href="#")),
                                    id="submenu-settings",
                                ),
                                id="submenu-settings-details",
                            )
                        ),
                    ),
                    role="group",
                    aria_labelledby="group-label-nav",
                ),
                cls="scrollbar",
            ),
            Footer(
                Div(
                    A(
                        LucideIcon("book-open", cls="size-4 text-muted-foreground"),
                        Span("Documentation", cls="text-xs text-muted-foreground"),
                        href="https://nitro.ndendic.com",
                        target="_blank",
                        cls="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-sidebar-accent/50 transition-colors",
                    ),
                    cls="border-t border-sidebar-border pt-2 mt-2",
                ),
            ),
            aria_label="Sidebar navigation",
            on_click__outside="if ($resize_is_mobile && $sidebar_open && !evt.target.closest('[data-sidebar-toggle]')) {$sidebar_open = false;}",
        ),
        data_side="left",
        aria_hidden="false",
        data_sidebar_initialized="true",
        **{"data-attr:aria-hidden": "!$sidebar_open"},
        signals=Signals(sidebar_open=True),
        cls="sidebar",
    )
'''

APP_TEMPLATE = '''\
"""
Nitro base template - App layout with sidebar and navbar.
Edit this file to customize your page layout.
"""

from nitro import *
from nitro.html import *
from nitro.html.components import *  # Card, Badge, LucideIcon, etc.
from nitro.html import template as templ, page_template
{framework_import}
from components import Sidebar, Navbar

# Page template configuration
htmlkws = dict(lang="en", data_resize="true")
page = page_template(htmlkw=htmlkws, lucide=True)


@templ
def template(content, title: str = "Nitro App"):
    return page(
        Fragment(
            Sidebar(),
            Main(
                Navbar(),
                Div(
                    Div(content, id="content"),
                    cls="p-4 md:p-6 xl:p-12",
                ),
            ),
        ),
        title=title,
        wrap_in={wrap_in},
    )


def StatCard(icon, label, value, description=""):
    return Div(
        Div(
            Div(
                LucideIcon(icon, cls="size-4 text-muted-foreground"),
                cls="flex items-center gap-2",
            ),
            Span(label, cls="text-sm text-muted-foreground"),
            cls="flex items-center justify-between",
        ),
        Div(
            Span(value, cls="text-2xl font-bold tracking-tight"),
            P(description, cls="text-xs text-muted-foreground mt-0.5") if description else "",
            cls="mt-2",
        ),
        cls="card p-5 hover:shadow-md transition-shadow duration-200",
    )


def QuickAction(icon, title, description, file_hint):
    return Div(
        Div(
            Div(
                LucideIcon(icon, cls="size-4 text-primary"),
                cls="flex items-center justify-center size-8 rounded-lg bg-primary/10",
            ),
            Div(
                P(title, cls="text-sm font-medium"),
                P(description, cls="text-xs text-muted-foreground"),
            ),
            cls="flex items-center gap-3",
        ),
        Code(file_hint, cls="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded"),
        cls="flex items-center justify-between p-3 rounded-lg border border-border/50 hover:border-primary/30 hover:bg-accent/5 transition-all duration-200",
    )


@template
def index():
    """Edit base.py to customize this page."""
    return Div(
        # Header
        Div(
            H1("Welcome to ", Span("Nitro", cls="text-primary"), cls="text-2xl font-bold tracking-tight"),
            P("Your app is running. Here is your starting dashboard.", cls="text-sm text-muted-foreground mt-1"),
            cls="mb-8",
        ),
        # Stats overview
        Div(
            StatCard("zap", "Status", "Running", "All systems operational"),
            StatCard("layers", "Entities", "0", "Define models in base.py"),
            StatCard("route", "Routes", "1", "This page — add more!"),
            StatCard("palette", "Theme", "Default", "Try the theme selector"),
            cls="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-8",
        ),
        # Quick actions
        Div(
            H2("Quick Start", cls="text-lg font-semibold mb-4"),
            Div(
                QuickAction("file-code", "Customize this page", "Edit the layout and add your content", "base.py"),
                QuickAction("sidebar", "Edit navigation", "Customize sidebar links and branding", "components.py"),
                QuickAction("database", "Add an entity", "Create your first domain model", "base.py"),
                QuickAction("radio", "Wire up events", "Add reactive updates with Datastar", "base.py"),
                cls="space-y-2",
            ),
            cls="card p-6",
        ),
    )
'''

# --- Template registry ---

TEMPLATES = {
    "blank": {
        "base": BLANK_TEMPLATE,
    },
    "app": {
        "base": APP_TEMPLATE,
        "components": APP_COMPONENTS,
    },
}


def generate_boost_base(framework: str, template: str = "blank") -> str:
    """Generate the base.py template content for the chosen framework."""
    return TEMPLATES[template]["base"].format(
        framework_import=FRAMEWORK_IMPORTS[framework],
        wrap_in=FRAMEWORK_WRAP_IN[framework],
    )


def generate_boost_components(template: str) -> str | None:
    """Generate components.py if the template requires it."""
    tpl = TEMPLATES.get(template, {})
    return tpl.get("components")
