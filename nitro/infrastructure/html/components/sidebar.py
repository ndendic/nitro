"""
Sidebar component with Datastar reactivity.

Provides a responsive sidebar navigation that:
- Supports left/right placement
- Uses CSS transitions for smooth open/close
- Auto-closes on mobile when clicking outside or pressing Escape
- Works with the Basecoat sidebar CSS
- Requires Datastar resize plugin for mobile detection ($resize_is_mobile)
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

    Requires: data_resize="true" on root HTML element for mobile detection.

    Args:
        *children: SidebarHeader, SidebarContent, SidebarFooter components
        side: Position of sidebar ("left" or "right")
        default_open: Whether sidebar starts open (default True)
        signal: Signal name for open state (auto-generated if not provided)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Example:
        Sidebar(
            SidebarHeader(
                A("My App", href="/"),
            ),
            SidebarContent(
                SidebarMenu(
                    SidebarSectionTitle("Navigation"),
                    SidebarLink("Home", href="/"),
                    SidebarItem("Dashboard", href="/dashboard", icon="layout-dashboard"),
                    label="Main",
                ),
            ),
            SidebarFooter(
                # User profile, actions, etc.
            ),
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
            # Click outside closes on mobile only (requires data-sidebar-toggle on toggle button)
            on_click__outside=f"if ($resize_is_mobile && ${signal} && !evt.target.closest('[data-sidebar-toggle]')) ${signal} = false",
        ),
        signals=Signals(**{signal: default_open}),
        cls=cn("sidebar", cls),
        **{
            "data-side": side,
            "data-sidebar-initialized": "true",
            "data-attr:aria-hidden": f"!${signal}",
            # Close on Escape key (window level)
            "on_keydown__window": f"if (evt.key === 'Escape') ${signal} = false",
        },
        **attrs,
    )


def SidebarHeader(*children, **attrs: Any):
    """
    Header section of the sidebar, typically contains branding or title.

    Styles handled by CSS selector: nav > header

    Args:
        *children: Header content (branding, logo, etc.)
        **attrs: Additional HTML attributes
    """
    def create_header(signal: str):
        return rt.Header(*children, **attrs)
    return create_header


def SidebarContent(*children, **attrs: Any):
    """
    Main scrollable content area of the sidebar.

    Styles handled by CSS selector: nav > section

    Args:
        *children: Sidebar navigation content (SidebarMenu, SidebarNav, etc.)
        **attrs: Additional HTML attributes
    """
    def create_content(signal: str):
        # Process nested children
        processed = [
            child(signal) if callable(child) else child for child in children
        ]
        return rt.Section(*processed, **attrs)
    return create_content


def SidebarFooter(*children, **attrs: Any):
    """
    Footer section of the sidebar.

    Styles handled by CSS selector: nav > footer

    Args:
        *children: Footer content (user profile, actions, etc.)
        **attrs: Additional HTML attributes
    """
    def create_footer(signal: str):
        return rt.Footer(*children, **attrs)
    return create_footer


# =============================================================================
# Navigation Components
# =============================================================================


def SidebarMenu(*children, label: Optional[str] = None, **attrs: Any):
    """
    Navigation menu container with optional section label.

    Styles handled by CSS selector: section > [role=group]

    Args:
        *children: SidebarLink, SidebarItem, SidebarSubmenu, SidebarDivider, SidebarSectionTitle
        label: Optional section label (e.g., "Getting Started", "Components")
        **attrs: Additional HTML attributes

    Example:
        SidebarMenu(
            SidebarSectionTitle("Navigation"),
            SidebarLink("Home", href="/"),
            SidebarItem("Dashboard", href="/dashboard", icon="layout-dashboard"),
            SidebarDivider(),
            SidebarSubmenu(
                SidebarLink("Users", href="/admin/users"),
                SidebarLink("Roles", href="/admin/roles"),
                label="Admin",
                icon="shield",
            ),
        )
    """
    def create_menu(signal: str):
        processed = [
            child(signal) if callable(child) else child for child in children
        ]

        content = []
        if label:
            content.append(rt.H3(label))
        content.append(rt.Ul(*processed))

        return rt.Div(*content, role="group", **attrs)
    return create_menu


def SidebarSectionTitle(title: str, id: Optional[str] = None, **attrs: Any):
    """
    Section title within sidebar content (e.g., "Getting Started", "Components").

    Styles handled by CSS selector: section h3

    Args:
        title: Title text
        id: Optional ID for ARIA labeling
        **attrs: Additional HTML attributes

    Example:
        SidebarSectionTitle("Getting Started", id="section-getting-started")
    """
    def create_title(signal: str):
        title_attrs = {**attrs}
        if id:
            title_attrs["id"] = id
        return rt.H3(title, **title_attrs)
    return create_title


def SidebarLink(
    text: str,
    href: str,
    is_active: bool = False,
    close_on_click: bool = True,
    **attrs: Any,
):
    """
    Simple navigation link without icon/variant complexity.

    Styles handled by CSS selector: ul li > a

    Args:
        text: Link text
        href: Link URL
        is_active: Whether this link is currently active
        close_on_click: Close sidebar on mobile when clicked (default True)
        **attrs: Additional HTML attributes

    Example:
        SidebarLink("Home", href="/")
        SidebarLink("Dashboard", href="/dashboard", is_active=True)
    """
    def create_link(signal: str):
        link_attrs = {**attrs}
        if is_active:
            link_attrs["aria-current"] = "page"
        if close_on_click:
            link_attrs["on_click"] = f"if ($resize_is_mobile) ${signal} = false"

        return rt.Li(
            rt.A(text, href=href, **link_attrs)
        )
    return create_link


def SidebarItem(
    *children,
    href: Optional[str] = None,
    icon: Optional[str] = None,
    is_active: bool = False,
    variant: Literal["default", "outline"] = "default",
    size: Literal["default", "sm", "lg"] = "default",
    close_on_click: bool = True,
    **attrs: Any,
):
    """
    Navigation item with optional icon and variant styling.

    Styles handled by CSS selector: ul li > a (with data-variant, data-size attributes)

    Args:
        *children: Item content (text, badges, etc.)
        href: Link URL (if provided, renders as anchor; otherwise as button)
        icon: Lucide icon name
        is_active: Whether this item is currently active
        variant: Visual variant ("default" or "outline")
        size: Size variant ("default", "sm", or "lg")
        close_on_click: Close sidebar on mobile when clicked (default True)
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
            item_attrs["on_click"] = f"if ($resize_is_mobile) ${signal} = false"

        if href:
            link = rt.A(*content, href=href, **item_attrs)
        else:
            link = rt.Button(*content, type="button", **item_attrs)

        return rt.Li(link)

    return create_item


def SidebarSubmenu(
    *children,
    label: str,
    icon: Optional[str] = None,
    default_open: bool = False,
    name: Optional[str] = None,
    **attrs: Any,
):
    """
    Collapsible submenu using native <details>/<summary>.

    Styles handled by CSS selector: ul li > details

    Args:
        *children: SidebarLink or SidebarItem components
        label: Text label for the collapsible trigger
        icon: Optional Lucide icon name
        default_open: Whether section starts expanded
        name: Group name for exclusive open behavior (radio-like)
        **attrs: Additional HTML attributes

    Example:
        SidebarSubmenu(
            SidebarLink("Users", href="/admin/users"),
            SidebarLink("Roles", href="/admin/roles"),
            label="Admin",
            icon="shield",
        )
    """
    def create_submenu(signal: str):
        # Build summary content
        summary_content = []
        if icon:
            summary_content.append(LucideIcon(icon))
        summary_content.append(rt.Span(label))

        # Process children
        processed = [
            child(signal) if callable(child) else child for child in children
        ]

        details_attrs = {**attrs}
        if default_open:
            details_attrs["open"] = True
        if name:
            details_attrs["name"] = name

        return rt.Li(
            rt.Details(
                rt.Summary(*summary_content),
                rt.Ul(*processed),
                **details_attrs,
            )
        )

    return create_submenu


def SidebarDivider(**attrs: Any):
    """
    Visual separator between sidebar sections.

    Styles handled by CSS selector: nav [role=separator]

    Args:
        **attrs: Additional HTML attributes
    """
    def create_divider(signal: str):
        return rt.Hr(role="separator", **attrs)
    return create_divider


# =============================================================================
# Toggle Button
# =============================================================================


def SidebarToggle(
    *children,
    target_signal: Optional[str] = None,
    icon: str = "panel-left",
    **attrs: Any,
) -> rt.HtmlString:
    """
    Toggle button for sidebar open/close state.

    This is a standalone component that can be placed outside the Sidebar
    (typically in a navbar). It toggles the sidebar visibility via a Datastar signal.

    IMPORTANT: The data-sidebar-toggle attribute prevents the sidebar's
    click-outside handler from closing the sidebar when the toggle is clicked.

    Args:
        *children: Button content (uses icon if not provided)
        target_signal: Signal name to toggle (default: "sidebar_1")
        icon: Lucide icon name (default: "panel-left")
        **attrs: Additional HTML attributes

    Example:
        # In navbar
        SidebarToggle()

        # With custom icon
        SidebarToggle(icon="menu")

        # With explicit signal (must match Sidebar's signal)
        SidebarToggle(target_signal="my_sidebar")
    """
    signal = target_signal or "sidebar_1"
    content = children if children else (LucideIcon(icon),)

    return rt.Button(
        *content,
        type="button",
        on_click=f"${signal} = !${signal}",
        **{
            "aria-label": "Toggle sidebar",
            "data-sidebar-toggle": "",
            "data-attr:aria-expanded": f"${signal}",
        },
        **attrs,
    )


# =============================================================================
# Legacy Components (kept for backward compatibility)
# =============================================================================


def SidebarNav(*children, **attrs: Any):
    """
    Navigation list container within the sidebar.

    Note: Consider using SidebarMenu instead for a simpler API.

    Args:
        *children: SidebarGroup or SidebarItem components
        **attrs: Additional HTML attributes
    """
    def create_nav(signal: str):
        processed = [
            child(signal) if callable(child) else child for child in children
        ]
        return rt.Div(
            rt.Ul(*processed),
            role="group",
            **attrs,
        )
    return create_nav


def SidebarGroup(*children, **attrs: Any):
    """
    Group of related sidebar items, typically with a label.

    Note: Consider using SidebarMenu with SidebarSectionTitle instead.

    Args:
        *children: SidebarGroupLabel and SidebarItem components
        **attrs: Additional HTML attributes
    """
    def create_group(signal: str):
        processed = [
            child(signal) if callable(child) else child for child in children
        ]
        return rt.Li(*processed, **attrs)
    return create_group


def SidebarGroupLabel(*children, **attrs: Any):
    """
    Label for a sidebar group.

    Note: Consider using SidebarSectionTitle instead.

    Args:
        *children: Label text/content
        **attrs: Additional HTML attributes
    """
    def create_label(signal: str):
        return rt.H3(*children, **attrs)
    return create_label


def SidebarCollapsible(
    *children,
    label: str,
    icon: Optional[str] = None,
    default_open: bool = False,
    **attrs: Any,
):
    """
    Collapsible sidebar section using native <details>/<summary>.

    Note: Consider using SidebarSubmenu instead for a consistent API.

    Args:
        *children: SidebarItem components to show when expanded
        label: Text label for the collapsible trigger
        icon: Optional Lucide icon name
        default_open: Whether section starts expanded
        **attrs: Additional HTML attributes
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
                **attrs,
            )
        )

    return create_collapsible


def SidebarSeparator(**attrs: Any):
    """
    Visual separator between sidebar sections.

    Note: Consider using SidebarDivider instead for a consistent naming convention.

    Args:
        **attrs: Additional HTML attributes
    """
    def create_separator(signal: str):
        return rt.Hr(role="separator", **attrs)
    return create_separator


# =============================================================================
# Helper Functions
# =============================================================================


def create_nav_item(
    label: str,
    href: Optional[str] = None,
    icon: Optional[str] = None,
    children: Optional[List[dict]] = None,
) -> dict:
    """
    Helper function to create navigation item dictionaries.

    Useful for data-driven sidebar navigation.

    Args:
        label: Display text
        href: Link URL
        icon: Lucide icon name
        children: Nested items for collapsible sections

    Returns:
        Dictionary suitable for SidebarItem or SidebarSubmenu
    """
    return {
        "label": label,
        "href": href,
        "icon": icon,
        "children": children,
    }
