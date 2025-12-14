"""
Error pages for the documentation platform.
Provides user-friendly error pages with navigation.
"""

from .templates.base import *  # noqa: F403
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router: APIRouter = APIRouter()


def error_content(
    status_code: int,
    title: str,
    message: str,
    suggestion: str = "",
):
    """Render error content with consistent styling."""
    return Div(
        Div(
            # Error code display
            Div(
                Span(str(status_code), cls="text-8xl font-bold text-muted-foreground/50"),
                cls="text-center mb-6",
            ),
            # Error title
            H1(title, cls="text-3xl font-bold text-foreground mb-4 text-center"),
            # Error message
            P(
                message,
                cls="text-muted-foreground text-lg mb-8 text-center max-w-md mx-auto",
            ),
            # Suggestion if provided
            P(
                suggestion,
                cls="text-muted-foreground text-sm mb-8 text-center",
            ) if suggestion else None,
            # Navigation links
            Div(
                Button(
                    LucideIcon("home", cls="mr-2"),
                    "Back to Home",
                    variant="primary",
                    data_on_click="@get('/')",
                ),
                Button(
                    LucideIcon("arrow-left", cls="mr-2"),
                    "Go Back",
                    variant="outline",
                    cls="ml-4",
                    data_on_click="history.back()",
                ),
                cls="flex justify-center gap-4 flex-wrap",
            ),
            cls="max-w-2xl mx-auto py-16",
        ),
        cls="flex items-center justify-center min-h-[60vh]",
    )


@router.get("/404")
@template(title="Page Not Found - Nitro Documentation")
def not_found_page():
    """404 Page Not Found"""
    return error_content(
        status_code=404,
        title="Page Not Found",
        message="The page you're looking for doesn't exist or has been moved.",
        suggestion="Try checking the URL or using the navigation menu.",
    )


@router.get("/500")
@template(title="Server Error - Nitro Documentation")
def server_error_page():
    """500 Internal Server Error"""
    return error_content(
        status_code=500,
        title="Something Went Wrong",
        message="We encountered an unexpected error. Please try again later.",
        suggestion="If this problem persists, please report it to our team.",
    )
