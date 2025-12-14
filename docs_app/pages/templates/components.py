from nitro.infrastructure.html import *
from nitro.infrastructure.html.components import *
from datetime import datetime


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
                cls="flex items-center gap-1 mr-auto hover:opacity-80 transition-opacity",
            ),
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
                    LucideIcon('sun'),
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

def Sidebar(pages: list = []):

    # Group pages by category
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
                                href='#'
                            )
                        ),

                        Li(
                            *sections
                        )
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

