"""Switch component with Datastar binding support."""

from typing import Any
from rusty_tags import Input as HTMLInput, HtmlString, Label as HTMLLabel, Span
from .utils import cn


def Switch(
    *children: Any,
    id: str,
    bind: Any = None,
    checked: bool = False,
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Toggle switch using native checkbox with role="switch" for Basecoat styling.

    Uses Basecoat's context-based styling with role="switch" attribute.
    The switch is styled via Basecoat CSS when placed inside a .form or .field
    container, or when given the .input class.

    Args:
        *children: Label content (text, icons, etc.) rendered next to switch
        id: Unique identifier for the switch (required for label association)
        bind: Datastar Signal for two-way binding (optional)
        checked: Initial checked state (used when no bind)
        disabled: Whether the switch is disabled
        cls: Additional CSS classes
        **attrs: Additional HTML attributes passed through

    Returns:
        HtmlString: Rendered switch with optional label

    Example:
        # Basic switch with label
        Switch("Enable notifications", id="notifications")

        # With Datastar binding
        from nitro.infrastructure.html.datastar import Signal, Signals
        settings = Signals(notifications=True, dark_mode=False)
        Switch("Enable notifications", id="notifications", bind=settings.notifications)
        Switch("Dark mode", id="dark", bind=settings.dark_mode)

        # Disabled state
        Switch("Unavailable", id="unavail", disabled=True)

        # Inside a Field (recommended for forms)
        Field(
            Switch("Enable feature", id="feature", bind=form.enabled),
            label="Feature Toggle",
        )
    """
    switch_attrs: dict[str, Any] = {
        "type": "checkbox",
        "role": "switch",
        "id": id,
        "name": attrs.pop("name", id),
        "disabled": disabled if disabled else None,
    }

    # Handle Datastar binding
    if bind is not None:
        # Signal from Datastar
        if hasattr(bind, 'to_js'):
            # Get the signal name without the $ prefix
            signal_name = bind.to_js().lstrip('$')
            switch_attrs["data_bind"] = signal_name
        elif isinstance(bind, str):
            switch_attrs["data_bind"] = bind.lstrip('$')
    else:
        # No binding, use static checked state
        if checked:
            switch_attrs["checked"] = True

    # Merge additional attributes
    switch_attrs.update(attrs)

    # Create the switch input - add .input class for Basecoat styling
    # Basecoat CSS targets: .form/.field input[role='switch'] OR .input[role='switch']
    input_kwargs = {k: v for k, v in switch_attrs.items() if v is not None}
    input_kwargs["cls"] = cn("input", cls) if cls else "input"

    switch_input = HTMLInput(**input_kwargs)

    # If no children (label text), return just the switch
    if not children:
        return switch_input

    # If there are children, wrap in a label for accessibility
    return HTMLLabel(
        switch_input,
        Span(*children, cls="ml-2"),
        html_for=id,
        cls="inline-flex items-center cursor-pointer",
        **{"data_disabled": "true"} if disabled else {},
    )
