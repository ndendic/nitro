"""Checkbox component with Datastar binding support."""

from typing import Any, Optional
from rusty_tags import Input as HTMLInput, HtmlString, Label as HTMLLabel, Span
from .utils import cn


def Checkbox(
    *children: Any,
    id: str,
    bind: Any = None,
    checked: bool = False,
    disabled: bool = False,
    required: bool = False,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Checkbox input with Datastar two-way binding.

    Uses Basecoat's context-based styling inside Field.
    When placed inside a .field container, the checkbox is
    automatically styled via Basecoat CSS.

    Args:
        *children: Label content (text, icons, etc.) rendered next to checkbox
        id: Unique identifier for the checkbox (required for label association)
        bind: Datastar Signal for two-way binding (optional)
        checked: Initial checked state (used when no bind)
        disabled: Whether the checkbox is disabled
        required: Whether the checkbox is required
        cls: Additional CSS classes
        **attrs: Additional HTML attributes passed through

    Returns:
        HtmlString: Rendered checkbox with optional label

    Example:
        # Basic checkbox with label
        Checkbox("Accept terms", id="terms")

        # With Datastar binding
        from nitro.infrastructure.html.datastar import Signal, Signals
        form = Signals(accepted=False)
        Checkbox("I agree", id="agree", bind=form.accepted)

        # Disabled state
        Checkbox("Unavailable", id="unavail", disabled=True)

        # Inside a Field (recommended for forms)
        Field(
            Checkbox("Accept terms", id="terms", bind=form.accepted),
            label="Terms and Conditions",
        )
    """
    checkbox_attrs: dict[str, Any] = {
        "type": "checkbox",
        "id": id,
        "name": attrs.pop("name", id),
        "disabled": disabled if disabled else None,
        "required": required if required else None,
    }

    # Handle Datastar binding
    if bind is not None:
        # Signal from Datastar
        if hasattr(bind, 'to_js'):
            # Get the signal name without the $ prefix
            signal_name = bind.to_js().lstrip('$')
            checkbox_attrs["data_bind"] = signal_name
        elif isinstance(bind, str):
            checkbox_attrs["data_bind"] = bind.lstrip('$')
    else:
        # No binding, use static checked state
        if checked:
            checkbox_attrs["checked"] = True

    # Merge additional attributes
    checkbox_attrs.update(attrs)

    # Create the checkbox input - only add cls if user provided classes
    input_kwargs = {k: v for k, v in checkbox_attrs.items() if v is not None}
    if cls:
        input_kwargs["cls"] = cn(cls)
    else:
        input_kwargs["cls"] = cn("input")

    checkbox_input = HTMLInput(**input_kwargs)

    # If no children (label text), return just the checkbox
    if not children:
        return checkbox_input

    # If there are children, wrap in a label for accessibility
    return HTMLLabel(
        checkbox_input,
        Span(*children, cls="ml-2"),
        html_for=id,
        cls="inline-flex items-center cursor-pointer",
        **{"data_disabled": "true"} if disabled else {},
    )
