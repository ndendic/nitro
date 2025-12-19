"""Global site search component with Cmd+K shortcut."""

from nitro.infrastructure.html import *
from nitro.infrastructure.html.components import Kbd
from nitro.infrastructure.html.components.icons import LucideIcon
from rusty_tags.datastar import Signals


# Define all searchable pages
SEARCH_PAGES = {
    "Foundation Components": [
        {"title": "Button", "href": "/xtras/button", "icon": "square"},
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


def SearchItem(title: str, href: str, icon: str, dialog_id: str, category: str):
    """Individual search result item with native onclick navigation."""
    search_key = f"{title} {category}".lower()
    return A(
        LucideIcon(icon, cls="h-4 w-4 mr-2 text-muted-foreground"),
        Span(title),
        href=href,
        cls="search-item flex items-center px-3 py-2 rounded-md hover:bg-accent cursor-pointer",
        onclick=f"document.getElementById('{dialog_id}').close();",
        data_search_key=search_key,
        role="menuitem",
        tabindex="0",
    )


def SearchGroup(heading: str, *items):
    """Group of search items with heading."""
    return Div(
        Div(heading, cls="text-xs font-medium text-muted-foreground px-3 py-1.5"),
        Div(*items, cls="search-group-items"),
        cls="search-group mb-2",
        data_group=heading.lower().replace(" ", "-"),
    )


def SiteSearch():
    """Global site search component with Cmd+K shortcut.

    Opens a command palette dialog with all searchable pages organized by category.
    Supports keyboard navigation and real-time filtering.

    Returns:
        Site search dialog with trigger button
    """
    dialog_id = "site-search-dialog"
    input_id = "site-search-input"

    # Build search groups for each category
    groups = []
    for category, pages in SEARCH_PAGES.items():
        items = [
            SearchItem(page["title"], page["href"], page["icon"], dialog_id, category)
            for page in pages
        ]
        groups.append(SearchGroup(category, *items))

    return Div(
        # Trigger button with keyboard shortcut hint
        Button(
            LucideIcon("search", cls="h-4 w-4"),
            Span("Search...", cls="hidden md:inline ml-2 text-muted-foreground"),
            Span(
                Kbd("Ctrl", cls="text-xs"),
                Kbd("K", cls="text-xs"),
                cls="hidden md:flex gap-0.5 ml-4",
            ),
            cls="btn btn-outline flex items-center gap-1 w-auto md:w-[200px] justify-start text-muted-foreground",
            id="site-search-trigger",
            onclick=f"document.getElementById('{dialog_id}').showModal(); setTimeout(() => document.getElementById('{input_id}').focus(), 50);",
        ),
        # Search dialog - native HTML dialog
        Dialog(
            Div(
                # Search input
                Div(
                    LucideIcon("search", cls="h-4 w-4 text-muted-foreground"),
                    Input(
                        type="text",
                        placeholder="Search documentation...",
                        id=input_id,
                        cls="flex-1 bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground",
                        oninput="filterSearchResults(this.value)",
                        autocomplete="off",
                    ),
                    cls="flex items-center gap-2 px-3 py-3 border-b",
                    id="site-search-input",
                ),
                # Results container
                Div(
                    *groups,
                    Div(
                        "No results found.",
                        id="search-empty",
                        cls="hidden py-6 text-center text-sm text-muted-foreground",
                    ),
                    cls="max-h-[400px] overflow-y-auto p-2",
                    id="search-results",
                    data_anchor="site-search-input",
                ),
                cls="bg-popover rounded-lg shadow-lg border w-full max-w-lg",
            ),
            cls="p-0 bg-transparent border-none shadow-none backdrop:bg-black/50",
            id=dialog_id,
        ),
        # Search filtering and keyboard handling
        Script(f"""
            // Filter search results based on query
            function filterSearchResults(query) {{
                const resultsContainer = document.getElementById('search-results');
                const emptyState = document.getElementById('search-empty');
                const items = resultsContainer.querySelectorAll('.search-item');
                const groups = resultsContainer.querySelectorAll('.search-group');
                const q = query.toLowerCase().trim();

                let visibleCount = 0;

                items.forEach(item => {{
                    const searchKey = item.dataset.searchKey || '';
                    const matches = !q || searchKey.includes(q);
                    item.style.display = matches ? 'flex' : 'none';
                    if (matches) visibleCount++;
                }});

                // Hide groups with no visible items
                groups.forEach(group => {{
                    const visibleItems = group.querySelectorAll('.search-item[style="display: flex;"], .search-item:not([style*="display"])');
                    const hasVisible = Array.from(group.querySelectorAll('.search-item')).some(
                        item => item.style.display !== 'none'
                    );
                    group.style.display = hasVisible ? 'block' : 'none';
                }});

                // Show/hide empty state
                emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
            }}

            // Keyboard shortcut (Cmd+K / Ctrl+K)
            document.addEventListener('keydown', function(e) {{
                if ((e.metaKey || e.ctrlKey) && e.key === 'k') {{
                    e.preventDefault();
                    const dialog = document.getElementById('{dialog_id}');
                    const input = document.getElementById('{input_id}');

                    if (dialog.open) {{
                        dialog.close();
                    }} else {{
                        dialog.showModal();
                        setTimeout(() => {{
                            if (input) {{
                                input.focus();
                                input.select();
                            }}
                        }}, 50);
                    }}
                }}
            }});

            // Close on backdrop click
            document.getElementById('{dialog_id}')?.addEventListener('click', function(e) {{
                if (e.target === this) {{
                    this.close();
                }}
            }});

            // Close on Escape
            document.getElementById('{dialog_id}')?.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    this.close();
                }}
            }});

            // Reset search when dialog closes
            document.getElementById('{dialog_id}')?.addEventListener('close', function() {{
                const input = document.getElementById('{input_id}');
                if (input) {{
                    input.value = '';
                    filterSearchResults('');
                }}
            }});
        """),
    )
