"""Boost base.py template for new Nitro projects."""

BOOST_BASE_TEMPLATE = '''\
"""
Nitro base template - Your starting point for building with Nitro.
Edit this file to customize your page layout and add routes.
"""

from nitro import *
from nitro.infrastructure.html import template as templ

# Page template configuration
# Add more options as needed: highlightjs=True, charts=True, datastar=True
page = page_template(
    lucide=True,  # Lucide icons included by default
)


@templ
def template(content, title: str = "Nitro App"):
    """
    Base template wrapper for all pages.

    Args:
        content: The page content to wrap
        title: Page title (default: "Nitro App")

    Returns:
        Wrapped HTML response

    Note: Uncomment wrap_in and import your framework's response class:
        - FastAPI: from fastapi.responses import HTMLResponse
        - Flask: from flask import Response (or use make_response)
        - Starlette: from starlette.responses import HTMLResponse
    """
    return page(
        Main(
            Div(
                content,
                cls="min-h-screen max-w-4xl mx-auto px-4 py-8",
            ),
        ),
        title=title,
        # wrap_in=HTMLResponse,  # Uncomment and import your framework's response class
    )


@template
def index():
    """
    Example index page - You've been Nitro Boosted!
    Edit this function to create your first page.
    """
    return Div(
        H1("You've been Nitro Boosted!", cls="text-4xl font-bold mb-4"),
        P("Edit this page in base.py", cls="text-lg text-gray-600"),
        cls="text-center py-20",
    )
'''


def generate_boost_base() -> str:
    """Generate the base.py template content."""
    return BOOST_BASE_TEMPLATE
