from nitro.infrastructure.html import *
from nitro.infrastructure.html.components import *
from datetime import datetime
from .site_search import SiteSearch
from .base import get

COMPONENT_PAGES = {
    "Foundation Components": [
        {"title": "Button", "href": "/cmds/page.button/nikola", "icon": "square", "page": "page.button"},
        {"title": "Card", "href": "/xtras/card", "icon": "credit-card"},
        {"title": "Badge", "href": "/xtras/badge", "icon": "tag"},
        {"title": "Alert", "href": "/xtras/alert", "icon": "alert-circle"},
        {"title": "Label", "href": "/xtras/label", "icon": "type"},
        {"title": "Kbd", "href": "/xtras/kbd", "icon": "keyboard"},
        {"title": "Spinner", "href": "/xtras/spinner", "icon": "loader"},
        {"title": "Skeleton", "href": "/xtras/skeleton", "icon": "layers"},
    ],
    "Form Controls": [
        {"title": "Field", "href": "/xtras/field", "icon": "form-input"},
        {"title": "Input Group", "href": "/xtras/input-group", "icon": "text-cursor-input"},
        {"title": "Checkbox", "href": "/xtras/checkbox", "icon": "check-square"},
        {"title": "Radio Group", "href": "/xtras/radio", "icon": "circle-dot"},
        {"title": "Switch", "href": "/xtras/switch", "icon": "toggle-right"},
        {"title": "Select", "href": "/xtras/select", "icon": "chevron-down"},
        {"title": "Textarea", "href": "/xtras/textarea", "icon": "align-left"},
    ],
    "Interactive Components": [
        {"title": "Tabs", "href": "/xtras/tabs", "icon": "folder"},
        {"title": "Accordion", "href": "/xtras/accordion", "icon": "chevrons-down"},
        {"title": "Dialog", "href": "/xtras/dialog", "icon": "square-stack"},
        {"title": "Dropdown Menu", "href": "/xtras/dropdown", "icon": "chevron-down"},
        {"title": "Popover", "href": "/xtras/popover", "icon": "message-square"},
        {"title": "Tooltip", "href": "/xtras/tooltip", "icon": "info"},
        {"title": "Alert Dialog", "href": "/xtras/alert-dialog", "icon": "alert-triangle"},
    ],
    "Feedback Components": [
        {"title": "Toast", "href": "/xtras/toast", "icon": "bell"},
        {"title": "Progress", "href": "/xtras/progress", "icon": "bar-chart-2"},
    ],
    "Navigation & Display": [
        {"title": "Breadcrumb", "href": "/xtras/breadcrumb", "icon": "navigation"},
        {"title": "Pagination", "href": "/xtras/pagination", "icon": "list"},
        {"title": "Avatar", "href": "/xtras/avatar", "icon": "user"},
        {"title": "Table", "href": "/xtras/table", "icon": "table"},
    ],
    "Advanced Components": [
        {"title": "Combobox", "href": "/xtras/combobox", "icon": "search"},
        {"title": "Command", "href": "/xtras/command", "icon": "terminal"},
        {"title": "Theme Switcher", "href": "/xtras/theme-switcher", "icon": "sun-moon"},
    ],
    "Utilities": [
        {"title": "RustyTags Datastar SDK", "href": "/xtras/rustytags", "icon": "code"},
        {"title": "CodeBlock", "href": "/xtras/codeblock", "icon": "file-code"},
    ],
}

def Footer():
    """Footer component with links and attribution."""
    current_year = datetime.now().year
    return CustomTag(
        "footer",
        Div(
            # Left section - Branding
            Div(
                Span("Nitro", cls="font-bold text-lg"),
                Span("Framework", cls="text-muted-foreground ml-1"),
                cls="flex items-center",
            ),
            # Center section - Links
            Div(
                A(
                    "Documentation",
                    href="/",
                    cls="text-muted-foreground hover:text-foreground transition-colors",
                ),
                A(
                    "GitHub",
                    href="https://github.com/ndendic/nitro-systems",
                    target="_blank",
                    rel="noopener noreferrer",
                    cls="text-muted-foreground hover:text-foreground transition-colors",
                ),
                A(
                    "Basecoat UI",
                    href="https://basecoatui.com/",
                    target="_blank",
                    rel="noopener noreferrer",
                    cls="text-muted-foreground hover:text-foreground transition-colors",
                ),
                cls="flex gap-6",
            ),
            # Right section - Attribution
            Div(
                P(
                    f"© {current_year} Nitro Framework",
                    cls="text-muted-foreground text-sm",
                ),
                P(
                    "Built with ",
                    Span("Nitro", cls="font-medium text-foreground"),
                    " + ",
                    Span("RustyTags", cls="font-medium text-foreground"),
                    cls="text-muted-foreground text-sm",
                ),
                cls="text-right",
            ),
            cls="container mx-auto px-4 py-6 flex flex-col md:flex-row justify-between items-center gap-4",
        ),
        cls="border-t bg-background mt-auto",
    )


def Navbar():
    return Header(
        Div(
            # Sidebar toggle button
            Button(
                LucideIcon('panel-left'),
                type='button',
                onclick="document.dispatchEvent(new CustomEvent('basecoat:sidebar'))",
            ),
            # Logo/Branding
            A(
                LucideIcon('zap', cls="text-primary"),
                Span("Nitro", cls="font-bold"),
                href="/",
                cls="flex items-center gap-1 hover:opacity-80 transition-opacity",
            ),
            # Site Search - centered with flex-grow
            Div(
                SiteSearch(),
                cls="flex-1 flex justify-center mx-4",
            ),
            # Theme controls
            Div(
                Select(
                    Optgroup(
                        Option('Claude', value='claude'),
                        Option('Candy', value='candy'),
                        Option('Neo Brutalism', value='neo-brutal'),
                        Option('Dark Matter', value='darkmatter'),
                        label='Themes'
                    ),
                    bind='theme',
                    on_change="document.documentElement.setAttribute('data-theme', $theme);",
                    cls='select w-[180px]'
                ),
                Button(
                    LucideIcon('sun',  show="!$darkMode"),
                    LucideIcon('moon',  show="$darkMode"),
                    on_click="$darkMode = !$darkMode; $darkMode ? document.documentElement.classList.add('dark') : document.documentElement.classList.remove('dark');",
                    cls="btn"
                ),
                cls="flex gap-2"
            ),
            cls='flex h-14 w-full items-center gap-2 px-4'
        ),
        cls='bg-background sticky inset-x-0 top-0 isolate flex shrink-0 items-center gap-2 border-b z-10'
    )
    #     cls="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
    # )


def DocumentationSidebar(pages: list = []):
    categories = {}
    for page in pages:
        category = page.category
        if category not in categories:
            categories[category] = []
        categories[category].append(page)

    # Sort pages within each category by order
    for category in categories:
        categories[category].sort(key=lambda p: p.order)

    # Build sidebar sections
    sections = []
    for category, category_pages in sorted(categories.items()):        
        # Pages in category
        page_links = []
        for page in category_pages:
            page_links.append(
                Li(
                    A(
                        page.title,
                        href=f"/documentation/{page.slug}",
                        data_on_click=f"@get('/documentation/{page.slug}')",
                    ),
                    cls="mb-1"
                )
            )

        # Category header
        sections.append(
            Details(
                Summary(
                    LucideIcon('book'),
                    category,
                    aria_controls='submenu-content-1-3-content'
                ),
                Ul(
                    *page_links,
                    cls="mb-6 space-y-1"
                )
            ),
        )
    return sections

def ComponentSidebar():
    # Build sidebar sections
    sections = []
    for category, category_pages in sorted(COMPONENT_PAGES.items()):        
        # Pages in category
        page_links = []
        for page in category_pages:
            page_links.append(
                Li(
                    A(
                        LucideIcon(page['icon']),
                        Span(page['title']),
                        # href=page['href'],
                        # href="#",
                        on_click=f"@get('{page['href']}')",
                    ),
                    cls="mb-1"
                )
            )

        # Category header
        sections.append(
            Details(
                Summary(
                    LucideIcon('book'),
                    category,
                    aria_controls='submenu-content-1-3-content'
                ),
                Ul(
                    *page_links,
                    cls="mb-6 space-y-1"
                )
            ),
        )
    return sections

def Sidebar(pages: list = []):
    return Aside(
        Nav(
            Section(
                Div(
                    H3('Getting started', id='group-label-content-1'),
                    Ul(
                        Li(
                            A(
                                LucideIcon('terminal'),
                                Span('Playground'),
                                href='/playground',
                            )
                        ),

                        Li(
                            *DocumentationSidebar(pages)
                        ),
                        H3('Components', id='group-label-content-2'),
                        Li(
                            *ComponentSidebar()
                        ),
                    ),
                    role='group',
                    aria_labelledby='group-label-content-1'
                ),
                cls='scrollbar'
            ),
            aria_label='Sidebar navigation'
        ),
        data_side='left',
        aria_hidden='false',
        cls='sidebar'
    )

