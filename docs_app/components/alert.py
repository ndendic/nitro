"""
Alert component for displaying contextual information in documentation.

Supports multiple variants: info, warning, danger, tip
"""

from rusty_tags import Div, Span, I
from typing import Literal

def Alert(
    *content,
    variant: Literal["info", "warning", "danger", "tip"] = "info",
    cls: str = "",
    **kwargs
):
    """
    Alert component with support for different variants.

    Args:
        *content: Child elements to render inside the alert
        variant: Alert type (info, warning, danger, tip)
        cls: Additional CSS classes
        **kwargs: Additional HTML attributes

    Returns:
        Div element styled as an alert

    Examples:
        Alert("This is important information", variant="info")
        Alert("Be careful!", variant="warning")
    """

    # Base classes for all alerts
    base_cls = "rounded-lg border p-4 mb-4"

    # Variant-specific classes and icons
    variant_config = {
        "info": {
            "cls": "bg-blue-50 border-blue-200 text-blue-900 dark:bg-blue-950 dark:border-blue-800 dark:text-blue-100",
            "icon": "info",
            "icon_cls": "text-blue-600 dark:text-blue-400"
        },
        "warning": {
            "cls": "bg-yellow-50 border-yellow-200 text-yellow-900 dark:bg-yellow-950 dark:border-yellow-800 dark:text-yellow-100",
            "icon": "alert-triangle",
            "icon_cls": "text-yellow-600 dark:text-yellow-400"
        },
        "danger": {
            "cls": "bg-red-50 border-red-200 text-red-900 dark:bg-red-950 dark:border-red-800 dark:text-red-100",
            "icon": "alert-circle",
            "icon_cls": "text-red-600 dark:text-red-400"
        },
        "tip": {
            "cls": "bg-green-50 border-green-200 text-green-900 dark:bg-green-950 dark:border-green-800 dark:text-green-100",
            "icon": "lightbulb",
            "icon_cls": "text-green-600 dark:text-green-400"
        }
    }

    config = variant_config.get(variant, variant_config["info"])

    # Combine classes
    combined_cls = f"{base_cls} {config['cls']}"
    if cls:
        combined_cls = f"{combined_cls} {cls}"

    # Create icon element using Lucide icon (via data-lucide attribute)
    icon_element = I(
        data_lucide=config["icon"],
        cls=f"inline-block mr-2 h-4 w-4 {config['icon_cls']}"
    )

    # Wrapper for content with flex layout
    return Div(
        Div(
            icon_element,
            Span(*content, cls="flex-1"),
            cls="flex items-start gap-2"
        ),
        cls=combined_cls,
        data_variant=variant,  # For testing purposes
        **kwargs
    )
