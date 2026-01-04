"""Theme Switcher component for light/dark/system theme modes.

A button component that cycles through theme modes and updates the document
theme. Supports persistence via Datastar's data-persist.
"""

from typing import Any, Optional, Literal
import rusty_tags as rt
from rusty_tags.datastar import Signals, Signal
from .utils import cn
from .icons import LucideIcon
from .button import Button

ThemeMode = Literal["light", "dark", "system"]


def ThemeSwitcher(
    signal: str = "theme_mode",
    default_theme: ThemeMode = "system",
    persist: bool = True,
    size: str = "default",
    variant: str = "ghost",
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Theme toggle button that cycles through light, dark, and system modes.

    Updates document.documentElement class ('dark') and optionally persists
    the selection using Datastar's data-persist.

    Args:
        signal: The Datastar signal name to store theme mode
        default_theme: Initial theme mode (light, dark, system)
        persist: Whether to persist theme choice using data-persist
        size: Button size (default, sm, lg, icon)
        variant: Button variant (ghost, outline, etc.)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Theme switcher button element

    Example:
        ThemeSwitcher()  # Uses default signal "theme_mode"
        ThemeSwitcher(signal="app_theme", default_theme="dark")
    """
    # Create the cycling logic for theme modes
    # light -> dark -> system -> light
    cycle_expression = f"""
        ${signal} === 'light' ? '${signal}' = 'dark' :
        ${signal} === 'dark' ? '${signal}' = 'system' :
        '${signal}' = 'light'
    """

    # Effect to apply theme to document
    theme_effect = f"""
        const mode = ${signal};
        const isDark = mode === 'dark' || (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
        if (isDark) {{
            document.documentElement.classList.add('dark');
        }} else {{
            document.documentElement.classList.remove('dark');
        }}
    """

    # Build button class based on size
    btn_cls = "btn"
    if size == "sm":
        btn_cls = "btn-sm-icon"
    elif size == "lg":
        btn_cls = "btn-lg-icon"
    else:
        btn_cls = "btn-icon"

    if variant == "ghost":
        btn_cls += "-ghost"
    elif variant == "outline":
        btn_cls += "-outline"
    elif variant == "secondary":
        btn_cls += "-secondary"

    return rt.Div(
        rt.Button(
            # Sun icon for light mode
            LucideIcon(
                "sun",
                cls="size-5 transition-transform",
                data_show=f"${signal} === 'light'",
            ),
            # Moon icon for dark mode
            LucideIcon(
                "moon",
                cls="size-5 transition-transform",
                data_show=f"${signal} === 'dark'",
            ),
            # Laptop icon for system mode
            LucideIcon(
                "laptop",
                cls="size-5 transition-transform",
                data_show=f"${signal} === 'system'",
            ),
            type="button",
            cls=cn(btn_cls, cls),
            aria_label="Toggle theme",
            on_click=cycle_expression,
            data_tooltip=f"Theme: ${signal}",
            **attrs,
        ),
        # Persistence element (hidden)
        rt.Div(
            cls="hidden",
            data_persist=signal if persist else None,
            data_effect=theme_effect,
        ) if persist else rt.Div(
            cls="hidden",
            data_effect=theme_effect,
        ),
        # Initialize signals
        signals=Signals(**{signal: default_theme}),
    )


def ThemeSwitcherDropdown(
    signal: str = "theme_mode",
    default_theme: ThemeMode = "system",
    persist: bool = True,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Theme switcher with dropdown menu for explicit theme selection.

    Provides a dropdown menu with Light, Dark, and System options
    instead of cycling through modes.

    Args:
        signal: The Datastar signal name to store theme mode
        default_theme: Initial theme mode (light, dark, system)
        persist: Whether to persist theme choice using data-persist
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Theme switcher dropdown element

    Example:
        ThemeSwitcherDropdown()
        ThemeSwitcherDropdown(signal="app_theme", default_theme="dark")
    """
    open_signal = f"{signal}_dropdown_open"

    # Effect to apply theme to document
    theme_effect = f"""
        const mode = ${signal};
        const isDark = mode === 'dark' || (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
        if (isDark) {{
            document.documentElement.classList.add('dark');
        }} else {{
            document.documentElement.classList.remove('dark');
        }}
    """

    return rt.Div(
        rt.Div(
            # Trigger button
            rt.Button(
                LucideIcon("sun", cls="size-5", data_show=f"${signal} === 'light'"),
                LucideIcon("moon", cls="size-5", data_show=f"${signal} === 'dark'"),
                LucideIcon("laptop", cls="size-5", data_show=f"${signal} === 'system'"),
                type="button",
                cls="btn-icon-ghost",
                aria_label="Select theme",
                aria_haspopup="menu",
                on_click=f"${open_signal} = !${open_signal}",
                **{"data-attr-aria-expanded": f"${open_signal}"},
            ),
            # Dropdown menu
            rt.Div(
                rt.Div(
                    rt.Div(
                        LucideIcon("sun", cls="size-4"),
                        "Light",
                        role="menuitem",
                        tabindex="0",
                        on_click=f"${signal} = 'light'; ${open_signal} = false",
                        **{"data-attr-aria-selected": f"${signal} === 'light'"},
                    ),
                    rt.Div(
                        LucideIcon("moon", cls="size-4"),
                        "Dark",
                        role="menuitem",
                        tabindex="0",
                        on_click=f"${signal} = 'dark'; ${open_signal} = false",
                        **{"data-attr-aria-selected": f"${signal} === 'dark'"},
                    ),
                    rt.Div(
                        LucideIcon("laptop", cls="size-4"),
                        "System",
                        role="menuitem",
                        tabindex="0",
                        on_click=f"${signal} = 'system'; ${open_signal} = false",
                        **{"data-attr-aria-selected": f"${signal} === 'system'"},
                    ),
                    role="menu",
                ),
                data_popover="",
                data_side="bottom",
                data_align="end",
                aria_hidden="true",
                **{"data-attr-aria-hidden": f"!${open_signal}"},
            ),
            cls="dropdown-menu",
            on_click__outside=f"${open_signal} = false",
            on_keydown=f"evt.key === 'Escape' && (${open_signal} = false)",
        ),
        # Persistence element (hidden)
        rt.Div(
            cls="hidden",
            data_persist=signal if persist else None,
            data_effect=theme_effect,
        ) if persist else rt.Div(
            cls="hidden",
            data_effect=theme_effect,
        ),
        # Initialize signals
        signals=Signals(**{
            signal: default_theme,
            open_signal: False,
        }),
        cls=cn("inline-flex", cls),
        **attrs,
    )


def ThemeSelect(
    signal: str = "theme",
    options: Optional[list[dict[str, str]]] = None,
    default_theme: str = "default",
    persist: bool = True,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Theme select dropdown for named theme selection.

    For selecting named themes (e.g., "claude", "candy", "neo-brutal")
    rather than light/dark modes.

    Args:
        signal: The Datastar signal name to store theme name
        options: List of theme options [{value: "theme-name", label: "Theme Name"}]
        default_theme: Initial theme name
        persist: Whether to persist theme choice
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Theme select element

    Example:
        ThemeSelect(
            options=[
                {"value": "default", "label": "Default"},
                {"value": "claude", "label": "Claude"},
                {"value": "candy", "label": "Candy"},
            ]
        )
    """
    if options is None:
        options = [
            {"value": "default", "label": "Default"},
            {"value": "claude", "label": "Claude"},
            {"value": "candy", "label": "Candy"},
            {"value": "neo-brutal", "label": "Neo Brutalism"},
            {"value": "darkmatter", "label": "Dark Matter"},
        ]

    # Effect to apply theme to document
    theme_effect = f"document.documentElement.setAttribute('data-theme', ${signal});"

    option_elements = [
        rt.Option(opt["label"], value=opt["value"])
        for opt in options
    ]

    return rt.Div(
        rt.Select(
            *option_elements,
            cls=cn("select", cls),
            data_bind=signal,
            on_change=f"document.documentElement.setAttribute('data-theme', ${signal});",
            **attrs,
        ),
        # Persistence element (hidden)
        rt.Div(
            cls="hidden",
            data_persist=signal if persist else None,
            data_effect=theme_effect,
        ) if persist else None,
        # Initialize signals
        signals=Signals(**{signal: default_theme}),
    )
