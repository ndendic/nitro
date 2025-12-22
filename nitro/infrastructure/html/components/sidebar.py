"""
Sidebar component with Datastar reactivity.

Provides a responsive sidebar navigation that:
- Supports left/right placement
- Uses CSS transitions for smooth open/close
- Auto-closes on mobile when clicking outside or pressing Escape
- Works with the Basecoat sidebar CSS
"""

from itertools import count
from typing import Any, List, Literal, Optional
import rusty_tags as rt
from rusty_tags.datastar import Signals
from .utils import cn
from .icons import LucideIcon

_sidebar_ids = count(1)


def Sidebar(
    *children,
    side: Literal["left", "right"] = "left",
    default_open: bool = True,
    signal: Optional[str] = None,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """
    Responsive sidebar component with Datastar reactivity.

    The sidebar uses aria-hidden for state management which integrates
    with the Basecoat CSS for proper animations and responsive behavior.

    On mobile (<768px): Sidebar overlays content and closes on outside click.
    On desktop (>=768px): Sidebar pushes content and stays visible.

    Args:
        *children: SidebarHeader, SidebarContent, SidebarFooter components
        side: Position of sidebar ("left" or "right")
        default_open: Whether sidebar starts open (default True)
        signal: Signal name for open state (auto-generated if not provided)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Example:
        Sidebar(
            SidebarHeader(H3("Navigation")),
            SidebarContent(
                SidebarNav(
                    SidebarGroup(
                        SidebarGroupLabel("Main"),
                        SidebarItem("Home", href="/", icon="home"),
                        SidebarItem("Dashboard", href="/dashboard", icon="layout-dashboard"),
                    ),
                ),
            ),
            SidebarFooter(P("Footer content")),
            default_open=True,
        )
    """
    if not signal:
        signal = f"sidebar_{next(_sidebar_ids)}"

    # Process children by calling closures with signal context
    processed_children = [
        child(signal) if callable(child) else child for child in children
    ]

    return rt.Aside(
        rt.Nav(
            *processed_children,
            aria_label="Sidebar navigation",
        ),
        signals=Signals(**{signal: default_open}),
        cls=cn("sidebar", cls),
        # Bind aria-hidden to the inverse of the signal
        **{
            "data-side": side,
            "data-attr:aria-hidden": f"!${signal}",
            # Close on Escape key (window level)
            "on_keydown__window": f"if (evt.key === 'Escape') ${signal} = false",
            # Close when clicking on the overlay (the aside element itself, not nav)
            "on_click": f"if (evt.target === this) ${signal} = false",
        },
        **attrs,
    )


def SidebarHeader(*children, cls: str = "", **attrs: Any):
    """
    Header section of the sidebar, typically contains branding or title.

    Args:
        *children: Header content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes
    """
    def create_header(signal: str):
        return rt.Header(
            *children,
            cls=cn(cls),
            **attrs,
        )
    return create_header


def SidebarContent(*children, cls: str = "", **attrs: Any):
    """
    Main scrollable content area of the sidebar.

    Args:
        *children: Sidebar navigation content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes
    """
    def create_content(signal: str):
        # Process nested children
        processed = [
            child(signal) if callable(child) else child for child in children
        ]
        return rt.Section(
            *processed,
            cls=cn("scrollbar", cls),
            **attrs,
        )
    return create_content


def SidebarFooter(*children, cls: str = "", **attrs: Any):
    """
    Footer section of the sidebar.

    Args:
        *children: Footer content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes
    """
    def create_footer(signal: str):
        return rt.Footer(
            *children,
            cls=cn(cls),
            **attrs,
        )
    return create_footer


def SidebarNav(*children, cls: str = "", **attrs: Any):
    """
    Navigation list container within the sidebar.

    Args:
        *children: SidebarGroup or SidebarItem components
        cls: Additional CSS classes
        **attrs: Additional HTML attributes
    """
    def create_nav(signal: str):
        processed = [
            child(signal) if callable(child) else child for child in children
        ]
        return rt.Div(
            rt.Ul(*processed, cls=cn(cls)),
            role="group",
            **attrs,
        )
    return create_nav


def SidebarGroup(*children, cls: str = "", **attrs: Any):
    """
    Group of related sidebar items, typically with a label.

    Args:
        *children: SidebarGroupLabel and SidebarItem components
        cls: Additional CSS classes
        **attrs: Additional HTML attributes
    """
    def create_group(signal: str):
        processed = [
            child(signal) if callable(child) else child for child in children
        ]
        return rt.Li(*processed, cls=cn(cls), **attrs)
    return create_group


def SidebarGroupLabel(*children, cls: str = "", **attrs: Any):
    """
    Label for a sidebar group.

    Args:
        *children: Label text/content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes
    """
    def create_label(signal: str):
        return rt.H3(*children, cls=cn(cls), **attrs)
    return create_label


def SidebarItem(
    *children,
    href: Optional[str] = None,
    icon: Optional[str] = None,
    is_active: bool = False,
    variant: Literal["default", "outline"] = "default",
    size: Literal["default", "sm", "lg"] = "default",
    close_on_click: bool = True,
    cls: str = "",
    **attrs: Any,
):
    """
    Individual sidebar navigation item.

    Args:
        *children: Item content (text, badges, etc.)
        href: Link URL (if provided, renders as anchor)
        icon: Lucide icon name
        is_active: Whether this item is currently active
        variant: Visual variant ("default" or "outline")
        size: Size variant ("default", "sm", or "lg")
        close_on_click: Close sidebar on mobile when clicked (default True)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Example:
        SidebarItem("Dashboard", href="/dashboard", icon="layout-dashboard")
        SidebarItem("Settings", href="/settings", icon="settings", is_active=True)
    """
    def create_item(signal: str):
        content = []

        # Add icon if provided
        if icon:
            content.append(LucideIcon(icon))

        # Add text/children with truncation wrapper
        content.append(rt.Span(*children))

        # Common attributes
        item_attrs = {
            "data-variant": variant,
            "data-size": size,
            **attrs,
        }

        if is_active:
            item_attrs["aria-current"] = "page"

        # Add mobile close behavior
        if close_on_click and href:
            # Close sidebar on mobile when link is clicked
            item_attrs["on_click"] = f"if (window.innerWidth < 768) ${signal} = false"

        if href:
            link = rt.A(
                *content,
                href=href,
                cls=cn(cls),
                **item_attrs,
            )
        else:
            link = rt.Button(
                *content,
                type="button",
                cls=cn(cls),
                **item_attrs,
            )

        return rt.Li(link)

    return create_item


def SidebarCollapsible(
    *children,
    label: str,
    icon: Optional[str] = None,
    default_open: bool = False,
    cls: str = "",
    **attrs: Any,
):
    """
    Collapsible sidebar section using native <details>/<summary>.

    Uses native HTML details/summary for accessibility and CSS-driven animations.

    Args:
        *children: SidebarItem components to show when expanded
        label: Text label for the collapsible trigger
        icon: Optional Lucide icon name
        default_open: Whether section starts expanded
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Example:
        SidebarCollapsible(
            SidebarItem("Users", href="/admin/users"),
            SidebarItem("Roles", href="/admin/roles"),
            label="Admin",
            icon="shield",
        )
    """
    def create_collapsible(signal: str):
        # Build summary content
        summary_content = []
        if icon:
            summary_content.append(LucideIcon(icon))
        summary_content.append(rt.Span(label))

        # Process children
        processed = [
            child(signal) if callable(child) else child for child in children
        ]

        return rt.Li(
            rt.Details(
                rt.Summary(*summary_content),
                rt.Ul(*processed),
                open=default_open if default_open else None,
                cls=cn(cls),
                **attrs,
            )
        )

    return create_collapsible


def SidebarSeparator(cls: str = "", **attrs: Any):
    """
    Visual separator between sidebar sections.

    Args:
        cls: Additional CSS classes
        **attrs: Additional HTML attributes
    """
    def create_separator(signal: str):
        return rt.Hr(role="separator", cls=cn(cls), **attrs)
    return create_separator


def SidebarToggle(
    *children,
    target_signal: Optional[str] = None,
    icon: str = "panel-left",
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """
    Toggle button for sidebar open/close state.

    This is a standalone component that can be placed outside the Sidebar.
    It toggles the sidebar visibility via a Datastar signal.

    Args:
        *children: Button content (uses icon if not provided)
        target_signal: Signal name to toggle (default: "sidebar_1")
        icon: Lucide icon name (default: "panel-left")
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Example:
        # In navbar
        SidebarToggle()

        # Custom styling
        SidebarToggle(icon="menu", cls="md:hidden")
    """
    signal = target_signal or "sidebar_1"
    content = children if children else (LucideIcon(icon),)

    return rt.Button(
        *content,
        type="button",
        on_click=f"${signal} = !${signal}",
        cls=cn(cls),
        **{
            "aria-label": "Toggle sidebar",
            "data-attr:aria-expanded": f"${signal}",
        },
        **attrs,
    )


# Convenience function for creating navigation data
def create_nav_item(
    label: str,
    href: Optional[str] = None,
    icon: Optional[str] = None,
    children: Optional[List[dict]] = None,
) -> dict:
    """
    Helper function to create navigation item dictionaries.

    Args:
        label: Display text
        href: Link URL
        icon: Lucide icon name
        children: Nested items for collapsible sections

    Returns:
        Dictionary suitable for SidebarItem or SidebarCollapsible
    """
    return {
        "label": label,
        "href": href,
        "icon": icon,
        "children": children,
    }
