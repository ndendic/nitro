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


@template
def index():
    """Edit base.py to customize this page."""
    return Div(
        H1("Nitro Boosted!", cls="text-4xl font-bold mb-4"),
        P("Edit ",Code("base.py", cls="text-primary")," to customize this page.", cls="text-lg text-muted-foreground"),
        cls="text-center py-20",
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
                cls="flex gap-2",
            ),
            cls="flex h-14 w-full items-center gap-2 px-4",
        ),
        cls="bg-background sticky inset-x-0 top-0 isolate flex shrink-0 items-center gap-2 border-b z-10",
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
                        Span("Edit components.py", cls="truncate text-xs font-light"),
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
                        Li(A(LucideIcon("home"), Span("Home"), href="/")),
                        Li(
                            Details(
                                Summary(
                                    LucideIcon("settings-2"),
                                    "Settings",
                                    aria_controls="submenu-settings",
                                ),
                                Ul(
                                    Li(A(Span("General"), href="#")),
                                    Li(A(Span("Team"), href="#")),
                                    Li(A(Span("Billing"), href="#")),
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


@template
def index():
    """Edit base.py to customize this page."""
    return Div(
        H1("Nitro Boosted!", cls="text-4xl font-bold mb-4"),
        P("Edit ",Code("base.py", cls="text-primary")," to customize this page.", cls="text-lg text-muted-foreground"),
        P("Edit ",Code("components.py", cls="text-primary")," to customize the sidebar and navbar.", cls="text-lg text-muted-foreground"),
        cls="py-20 text-center",
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
