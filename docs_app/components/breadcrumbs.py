"""Breadcrumb navigation component"""

from rusty_tags import Nav, Ol, Li, A, Span
from nitro.infrastructure.html.datastar import Signals


def Breadcrumbs(path_segments: list[tuple[str, str]], current_title: str):
    """
    Create breadcrumb navigation.

    Args:
        path_segments: List of (title, url) tuples for each breadcrumb segment
        current_title: Title of the current page (not a link)

    Returns:
        Breadcrumb navigation component with Datastar navigation

    Example:
        Breadcrumbs(
            [("Docs", "/documentation"), ("Guide", "/documentation/guide")],
            "Getting Started"
        )
    """

    items = []

    # Add each segment as a link with Datastar navigation
    for title, url in path_segments:
        items.append(
            Li(
                A(
                    title,
                    href=url,
                    data_on_click=f"$$get('{url}')",
                    cls="text-primary hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                ),
                cls="inline-flex items-center"
            )
        )

        # Add separator after each item except the last
        items.append(
            Li(
                Span(
                    "/",
                    cls="mx-2 text-muted-foreground",
                    aria_hidden="true"
                ),
                cls="inline-flex items-center"
            )
        )

    # Add current page (not a link)
    items.append(
        Li(
            Span(
                current_title,
                cls="text-foreground font-medium",
                aria_current="page"
            ),
            cls="inline-flex items-center"
        )
    )

    return Nav(
        Ol(
            *items,
            cls="inline-flex items-center space-x-0 flex-wrap"
        ),
        aria_label="Breadcrumb",
        cls="mb-6 text-sm"
    )
