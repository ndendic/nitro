"""
Navigation sidebar component for documentation.

Auto-generates from DocPage categories and pages.
"""

from typing import List, Optional
from rusty_tags import Nav, Div, H3, Ul, Li, A, Button, Span
from rusty_tags.datastar import Signals


def Sidebar(pages: List, current_page: Optional[str] = None, mobile: bool = False):
    """
    Generate navigation sidebar from DocPage entities.

    Args:
        pages: List of DocPage entities
        current_page: Slug of current active page (for highlighting)
        mobile: Whether to render mobile-responsive version

    Returns:
        Sidebar navigation component
    """
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
        # Category header
        sections.append(
            H3(
                category,
                cls="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 px-3"
            )
        )

        # Pages in category
        page_links = []
        for page in category_pages:
            is_active = page.slug == current_page

            # Active styling
            link_cls = "block px-3 py-2 rounded-md text-sm transition-colors "
            if is_active:
                link_cls += "bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100 font-medium"
            else:
                link_cls += "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"

            page_links.append(
                Li(
                    A(
                        page.title,
                        href=f"/documentation/{page.slug}",
                        data_on_click=f"$$get('/documentation/{page.slug}')",
                        cls=link_cls,
                        **({'aria-current': 'page'} if is_active else {})
                    ),
                    cls="mb-1"
                )
            )

        sections.append(
            Ul(
                *page_links,
                cls="mb-6 space-y-1"
            )
        )

    # Mobile toggle signal
    if mobile:
        sigs = Signals(sidebar_open=False)

        # Mobile header with toggle button
        mobile_header = Div(
            Button(
                Span("☰", cls="text-2xl"),
                data_on_click="$sidebar_open = !$sidebar_open",
                cls="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white dark:bg-gray-800 rounded-md shadow-md",
                type="button",
                aria_label="Toggle sidebar"
            ),
            signals=sigs
        )

        # Sidebar with mobile toggle
        sidebar_content = Div(
            *sections,
            cls="p-4 overflow-y-auto"
        )

        return Div(
            mobile_header,
            Nav(
                sidebar_content,
                cls=(
                    "fixed inset-y-0 left-0 z-40 w-64 bg-white dark:bg-gray-900 "
                    "border-r border-gray-200 dark:border-gray-700 "
                    "transform transition-transform duration-200 "
                    "lg:translate-x-0 lg:static "
                    "data-[sidebar_open=false]:-translate-x-full "
                    "data-[sidebar_open=true]:translate-x-0"
                ),
                data_bind_class="$sidebar_open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'",
                role="navigation",
                aria_label="Documentation navigation"
            ),
            # Backdrop for mobile
            Div(
                cls=(
                    "fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden "
                    "data-[sidebar_open=false]:hidden"
                ),
                data_bind_class="$sidebar_open ? '' : 'hidden'",
                data_on_click="$sidebar_open = false"
            )
        )
    else:
        # Desktop-only sidebar (no mobile controls)
        return Nav(
            Div(
                *sections,
                cls="p-4 overflow-y-auto"
            ),
            cls=(
                "w-64 bg-white dark:bg-gray-900 border-r border-gray-200 "
                "dark:border-gray-700 h-screen sticky top-0"
            ),
            role="navigation",
            aria_label="Documentation navigation"
        )


def SidebarSkeleton():
    """
    Loading skeleton for sidebar (while pages are loading).
    """
    return Nav(
        Div(
            # Category skeleton
            Div(cls="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-2"),
            # Link skeletons
            Div(cls="h-8 w-full bg-gray-100 dark:bg-gray-800 rounded mb-1"),
            Div(cls="h-8 w-full bg-gray-100 dark:bg-gray-800 rounded mb-1"),
            Div(cls="h-8 w-full bg-gray-100 dark:bg-gray-800 rounded mb-6"),
            # Second category
            Div(cls="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-2"),
            Div(cls="h-8 w-full bg-gray-100 dark:bg-gray-800 rounded mb-1"),
            Div(cls="h-8 w-full bg-gray-100 dark:bg-gray-800 rounded mb-1"),
            cls="p-4 animate-pulse"
        ),
        cls=(
            "w-64 bg-white dark:bg-gray-900 border-r border-gray-200 "
            "dark:border-gray-700 h-screen sticky top-0"
        ),
        role="navigation",
        aria_label="Documentation navigation"
    )
