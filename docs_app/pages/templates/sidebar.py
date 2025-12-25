from functools import lru_cache

from nitro.infrastructure.html import *
from nitro.infrastructure.html.components import *
from nitro.infrastructure.html import Footer as HTMLFooter
from pathlib import Path as PathLibPath
from domain.page_model import DocPage

COMPONENT_PAGES = {
    "Base": {
        "pages": [
            {"title": "Layouts", "href": "/cmds/page.layouts/nikola", "icon": "layout"},
            {"title": "Typography", "href": "/cmds/page.typography/nikola", "icon": "type"},
            {"title": "Button", "href": "/cmds/page.button/nikola", "icon": "square"},
            {"title": "Card", "href": "/cmds/page.card/nikola", "icon": "credit-card"},
            {"title": "Badge", "href": "/cmds/page.badge/nikola", "icon": "tag"},
            {"title": "Alert", "href": "/cmds/page.alert/nikola", "icon": "alert-circle"},
            {"title": "Label", "href": "/cmds/page.label/nikola", "icon": "type"},
            {"title": "Kbd", "href": "/cmds/page.kbd/nikola", "icon": "keyboard"},
            {"title": "Spinner", "href": "/cmds/page.spinner/nikola", "icon": "loader"},
            {"title": "Skeleton", "href": "/cmds/page.skeleton/nikola", "icon": "layers"},
        ],
        "icon": "layout",
    },
    "Form": {
        "pages": [
            {"title": "Field", "href": "/cmds/page.field/nikola", "icon": "form-input"},
            {"title": "Input Group", "href": "/cmds/page.input-group/nikola", "icon": "text-cursor-input"},
            {"title": "Checkbox", "href": "/cmds/page.checkbox/nikola", "icon": "check-square"},
            {"title": "Radio Group", "href": "/cmds/page.radio/nikola", "icon": "circle-dot"},
            {"title": "Switch", "href": "/cmds/page.switch/nikola", "icon": "toggle-right"},
            {"title": "Select", "href": "/cmds/page.select/nikola", "icon": "chevron-down"},
            {"title": "Textarea", "href": "/cmds/page.textarea/nikola", "icon": "align-left"},
            {"title": "Dropzone", "href": "/cmds/page.dropzone/nikola", "icon": "upload"},
            {"title": "DatePicker", "href": "/cmds/page.datepicker/nikola", "icon": "calendar"},
        ],
        "icon": "form-input",
    },
    "Interactive": {
        "pages": [
            {"title": "Tabs", "href": "/cmds/page.tabs/nikola", "icon": "folder"},
            {"title": "Accordion", "href": "/cmds/page.accordion/nikola", "icon": "chevrons-down"},
            {"title": "Dialog", "href": "/cmds/page.dialog/nikola", "icon": "square-stack"},
            {"title": "Dropdown Menu", "href": "/cmds/page.dropdown/nikola", "icon": "chevron-down"},
            {"title": "Popover", "href": "/cmds/page.popover/nikola", "icon": "message-square"},
            {"title": "Tooltip", "href": "/cmds/page.tooltip/nikola", "icon": "info"},
            {"title": "Alert Dialog", "href": "/cmds/page.alert-dialog/nikola", "icon": "alert-triangle"},
        ],
        "icon": "folder",
    },
    "Feedback": {
        "pages": [
            {"title": "Toast", "href": "/cmds/page.toast/nikola", "icon": "bell"},
            {"title": "Progress", "href": "/cmds/page.progress/nikola", "icon": "bar-chart-2"},
        ],
        "icon": "bell",
    },
    "Navigation & Display": {
        "pages": [
            {"title": "Breadcrumb", "href": "/cmds/page.breadcrumb/nikola", "icon": "navigation"},
            {"title": "Pagination", "href": "/cmds/page.pagination/nikola", "icon": "list"},
            {"title": "Avatar", "href": "/cmds/page.avatar/nikola", "icon": "user"},
            {"title": "Table", "href": "/cmds/page.table/nikola", "icon": "table"},
        ],
        "icon": "navigation",
    },
    "Advanced": {
        "pages": [
            {"title": "Combobox", "href": "/cmds/page.combobox/nikola", "icon": "search"},
            {"title": "Command", "href": "/cmds/page.command/nikola", "icon": "terminal"},
            {"title": "Theme Switcher", "href": "/cmds/page.theme-switcher/nikola", "icon": "sun-moon"},
        ],
        "icon": "search",
    },
    "Layout": {
        "pages": [
            {"title": "Sidebar", "href": "/cmds/page.sidebar/nikola", "icon": "panel-left"},
        ],
        "icon": "panel-left",
    },
    "Utilities": {
        "pages": [
            {"title": "RustyTags Datastar SDK", "href": "/cmds/page.rustytags/nikola", "icon": "code"},
            {"title": "CodeBlock", "href": "/cmds/page.codeblock/nikola", "icon": "file-code"},
            ],
            "icon": "code",
        },
}


@lru_cache(maxsize=1)
def get_pages():
    content_dir = PathLibPath(__file__).parent.parent.parent / "content"
    md_files = list(content_dir.rglob("*.md"))
    all_pages = []
    for md_file in md_files:
        try:
            page_obj = DocPage.load_from_fs(md_file)
            all_pages.append(page_obj)
        except Exception as e:
            print(f"Error loading {md_file}: {e}")
            continue
    return all_pages

# @lru_cache(maxsize=1)
def DocumentationSidebar():
    categories = {}
    for page in get_pages():
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
                        on_click=f"@get('/documentation/{page.slug}')",
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
                    aria_controls=f'submenu-content-{category}-content',
                ),
                Ul(
                    *page_links,
                    cls="mb-6 space-y-1"
                ),
                name='sidebar'
            ),
        )
    return sections


def ComponentSidebar():
    # Build sidebar sections
    sections = []
    for category, category_pages in COMPONENT_PAGES.items():
        # Pages in category
        page_links = []
        for page in category_pages['pages']:
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
                    LucideIcon(category_pages['icon']),
                    category,
                    aria_controls='submenu-content-1-3-content',
                ),
                Ul(
                    *page_links,
                    cls="mb-6 space-y-1"
                ),
                name='sidebar',
            ),
        )
    return sections


def Sidebar():
    return Aside(
        Nav(
            Header(
                A(
                    Div(
                        LucideIcon('zap', cls="h-4 w-4"),
                        cls='bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg'
                    ),
                    Div(
                        Span('Nitro', cls='truncate font-bold'),
                        Span('Framework', cls='truncate text-xs font-light'),
                        cls='grid flex-1 text-left text-sm leading-tight'
                    ),
                    href='/',
                    aria_current='page',
                    cls='btn-ghost p-2 h-12 w-full justify-start'
                )
            ),
            Section(
                Div(
                    H3('Getting started', id='group-label-content-1'),
                    Ul(
                        Li(A(LucideIcon('terminal'), Span('Playground'),href='/playground',)),
                        Li(A(LucideIcon('terminal'), Span('Components playground'),href='/playground_components',)),

                        Li(
                            *DocumentationSidebar()
                        ),
                        H3('Components', id='group-label-content-2'),
                        Li(
                            *ComponentSidebar()
                        ),
                    ),
                    role='group',
                    aria_labelledby='group-label-content-1'
                ),
                cls='scrollbar',            
            ),
            HTMLFooter(
                Div(
                    Button(
                        Img(src='https://github.com/ndendic.png', cls='rounded-lg shrink-0 size-8'),
                        Div(
                            Span('Nikola Dendic', cls='truncate font-medium'),
                            Span('@ndendic', cls='truncate text-xs'),
                            cls='grid flex-1 text-left text-sm leading-tight'
                        ),
                        LucideIcon('chevrons-up-down', cls="h-4 w-4"),
                        id='popover-979143-trigger',
                        type='button',
                        aria_expanded='true',
                        aria_controls='popover-979143-popover',
                        data_keep_mobile_sidebar_open='',
                        cls='p-2 h-12 w-full flex items-center justify-start',
                        variant="ghost",
                    ),
                    Div(
                        Div(
                            Header(
                                H2('I hope you like Nitro...', cls='font-semibold'),
                                P(
                                    'My name is',
                                    A('Nikola', href='https://ndendic.com', target='_blank', aria_current='page'),
                                    'and I made this (and',
                                    A('other things', href='https://pagescms.org', target='_target', aria_current='page', cls='underline underline-offset-4'),
                                    '). If you find it useful, please consider sponsoring me on GitHub or following me on X.',
                                    cls='text-muted-foreground text-sm'
                                ),
                                cls='grid gap-1.5'
                            ),
                            HTMLFooter(
                                A('Sponsor me on GitHub', href='https://github.com/sponsors/ndendic', target='_blank', cls='btn-sm'),
                                A('Follow me on X', href='https://x.com/ndendic1', target='_blank', cls='btn-sm-outline'),
                                cls='grid gap-2'
                            ),
                            cls='grid gap-4'
                        ),
                        id='popover-979143-popover',
                        data_popover='',
                        aria_hidden='false',
                        data_side='top',
                        cls='w-[271px] md:w-[239px]'
                    ),
                    id='popover-979143',
                    data_popover_initialized='true',
                    cls='popover'
                )
            ),
            aria_label='Sidebar navigation'
        ),
        data_side='left',
        aria_hidden='false',
        cls='sidebar',        
    )