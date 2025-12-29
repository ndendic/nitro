"""Toast notification component.

A notification system with provider pattern. Supports variants, auto-dismiss,
positioning, and stacking. Uses Datastar for state management and animations.
"""

from typing import Any, Optional, Union
from rusty_tags import Div, H2, P, Span, HtmlString, TagBuilder, Footer, Section
from rusty_tags.datastar import Signals, Signal
from .button import Button
from .icons import LucideIcon
from .utils import cn


# Variant icons mapping
TOAST_ICONS = {
    "default": "info",
    "success": "circle-check",
    "error": "circle-x",
    "warning": "triangle-alert",
    "info": "info",
}


def ToastProvider(
    *children: Any,
    position: str = "bottom-right",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Container for toast notifications.

    Provides positioning and stacking context for toast notifications.
    Should wrap your app content and toasts will appear relative to it.

    Args:
        *children: App content and Toast components
        position: Toast position - top-left, top-center, top-right,
                  bottom-left, bottom-center, bottom-right
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Container with toaster element for notifications

    Example:
        ToastProvider(
            # Your app content here
            Button("Show Toast", on_click="showToast()"),
            Toast(id="my-toast", title="Hello!", variant="success"),
            position="bottom-right",
        )
    """
    # Map position to data-align attribute
    align_map = {
        "top-left": "start",
        "top-center": "center",
        "top-right": "end",
        "bottom-left": "start",
        "bottom-center": "center",
        "bottom-right": "end",
    }

    # Determine if position is top or bottom
    is_top = position.startswith("top")
    align = align_map.get(position, "end")

    # Position classes for the toaster
    position_cls = "top-0" if is_top else "bottom-0"

    # Separate toasts from other children
    toasts = []
    other_children = []
    for child in children:
        if hasattr(child, '__str__') and 'class="toast"' in str(child):
            toasts.append(child)
        else:
            other_children.append(child)

    toaster = Div(
        *toasts,
        id="toaster",
        cls=cn("toaster", position_cls, cls),
        data_align=align,
        **attrs,
    )

    return Div(
        *other_children,
        toaster,
        cls="relative min-h-screen",
    )


def Toaster(
    position: str = "bottom-right",
    cls: str = "",
    **attrs: Any,
) -> Union[TagBuilder, HtmlString]:
    """Standalone toaster container for dynamic toast injection.

    Place this in your layout to receive dynamically created toasts.
    Toasts can be added via HTMX or JavaScript events.

    Args:
        position: Toast position - top-left, top-center, top-right,
                  bottom-left, bottom-center, bottom-right
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Empty toaster container ready to receive toasts

    Example:
        # In your base layout
        Toaster(position="bottom-right")

        # Add toast via HTMX
        Button(
            "Show Toast",
            hx_get="/toast/success",
            hx_target="#toaster",
            hx_swap="beforeend",
        )
    """
    # Map position to data-align attribute
    align_map = {
        "top-left": "start",
        "top-center": "center",
        "top-right": "end",
        "bottom-left": "start",
        "bottom-center": "center",
        "bottom-right": "end",
    }

    is_top = position.startswith("top")
    align = align_map.get(position, "end")
    position_cls = "top-0" if is_top else "bottom-0"

    return Div(
        id="toaster",
        cls=cn("toaster", position_cls, cls),
        data_align=align,
        **attrs,
    )


def Toast(
    *children: Any,
    id: str,
    title: str = "",
    description: str = "",
    variant: str = "default",
    duration: int = 5000,
    show_icon: bool = True,
    dismissible: bool = True,
    visible: bool = False,
    action_label: str = "",
    action_onclick: str = "",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Individual toast notification.

    Creates a toast notification with title, description, optional icon,
    and action buttons. Auto-dismisses after duration milliseconds.

    Args:
        *children: Additional content (overrides title/description if provided)
        id: Unique identifier for the toast (required)
        title: Toast title text
        description: Toast description text
        variant: Toast variant - default, success, error, warning, info
        duration: Auto-dismiss time in ms (0 for no auto-dismiss)
        show_icon: Whether to show variant icon
        dismissible: Whether to show close button
        visible: Whether toast is initially visible (default False)
        action_label: Label for optional action button
        action_onclick: Action button click handler
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Toast notification element

    Example:
        Toast(
            id="success-toast",
            title="Success!",
            description="Your changes have been saved.",
            variant="success",
            duration=3000,
        )
    """
    signal_name = f"{id.replace('-', '_')}_visible"

    # Build content section
    content_elements = []

    # Icon
    if show_icon:
        icon_name = TOAST_ICONS.get(variant, "info")
        content_elements.append(
            LucideIcon(icon_name, cls="size-4 shrink-0")
        )

    # Text section (title and description)
    text_section = []
    if title:
        text_section.append(H2(title))
    if description:
        text_section.append(P(description))

    # If children provided, use them instead
    if children:
        content_elements.append(Section(*children))
    elif text_section:
        content_elements.append(Section(*text_section))

    # Footer with buttons
    footer_elements = []

    if action_label:
        footer_elements.append(
            Button(
                action_label,
                variant="default",
                size="sm",
                data_toast_action="",
                on_click=f"{action_onclick}; el.closest('.toast').setAttribute('aria-hidden', 'true')" if action_onclick else "el.closest('.toast').setAttribute('aria-hidden', 'true')",
            )
        )

    if dismissible:
        footer_elements.append(
            Button(
                "Dismiss",
                variant="outline",
                size="sm",
                data_toast_cancel="",
                on_click="el.closest('.toast').setAttribute('aria-hidden', 'true')",
            )
        )

    if footer_elements:
        content_elements.append(Footer(*footer_elements))

    # Build toast
    toast_attrs = dict(attrs)
    toast_attrs["role"] = "status"
    toast_attrs["aria_atomic"] = "true"
    toast_attrs["aria_hidden"] = "false" if visible else "true"
    toast_attrs["data_category"] = variant

    if duration > 0:
        toast_attrs["data_duration"] = str(duration)

    return Div(
        Div(
            *content_elements,
            cls="toast-content",
            data_ref=id,
        ),
        id=id,
        cls=cn("toast", cls),
        signals=Signals(**{signal_name: visible}),
        **toast_attrs,
    )


def ToastTrigger(
    *children: Any,
    toast_id: Optional[str] = None,
    variant: str = "default",
    button_variant: str = "default",
    title: str = "",
    description: str = "",
    duration: int = 5000,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Button that triggers a toast notification.

    Can either show an existing toast by ID or dispatch a new toast
    via the basecoat:toast custom event.

    Args:
        *children: Button content
        toast_id: ID of existing toast to show (optional)
        variant: Toast variant for new toasts
        button_variant: Button variant for the trigger button
        title: Toast title for new toasts
        description: Toast description for new toasts
        duration: Auto-dismiss duration for new toasts
        cls: Additional CSS classes
        **attrs: Additional button attributes

    Returns:
        Button that triggers toast notification

    Example:
        # Trigger existing toast
        ToastTrigger("Show Toast", toast_id="my-toast")

        # Create new toast via event
        ToastTrigger(
            "Success!",
            variant="success",
            title="Saved",
            description="Your changes have been saved.",
        )
    """
    if toast_id:
        # Show existing toast
        onclick = f"document.getElementById('{toast_id}').setAttribute('aria-hidden', 'false')"
    else:
        # Dispatch new toast event
        event_detail = {
            "category": variant,
            "title": title,
            "description": description,
            "duration": duration,
        }
        # Create JavaScript object literal
        js_obj = str(event_detail).replace("'", '"')
        onclick = f"document.dispatchEvent(new CustomEvent('basecoat:toast', {{detail: {js_obj}}}));"

    return Button(
        *children,
        variant=button_variant,
        cls=cls,
        on_click=onclick,
        **attrs,
    )


def ToastClose(
    *children: Any,
    toast_id: str,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Button that closes/hides a specific toast.

    Args:
        *children: Button content (defaults to "Dismiss" if empty)
        toast_id: ID of the toast to close
        cls: Additional CSS classes
        **attrs: Additional button attributes

    Returns:
        Button that closes the toast

    Example:
        ToastClose("Got it!", toast_id="notification-toast")
    """
    content = children if children else ("Dismiss",)

    return Button(
        *content,
        variant="outline",
        size="sm",
        cls=cls,
        on_click=f"document.getElementById('{toast_id}').setAttribute('aria-hidden', 'true')",
        **attrs,
    )
