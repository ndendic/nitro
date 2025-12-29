"""Radio Group component with Datastar binding support using compound component pattern."""

from typing import Any, Callable, Optional
from rusty_tags import Input as HTMLInput, HtmlString, Label as HTMLLabel, Span, Div
from .utils import cn


def RadioGroup(
    *children: Any,
    bind: Any = "radio_group",
    orientation: str = "vertical",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Radio group container with Datastar two-way binding.

    Uses compound component pattern - children that are callables (RadioItem)
    receive the bind signal from the parent.

    Uses Basecoat's context-based styling inside Field.
    When placed inside a .field container, the radios are
    automatically styled via Basecoat CSS.

    Args:
        *children: RadioItem children (or other content)
        bind: Datastar Signal for two-way binding (required)
        orientation: Layout direction - "vertical" or "horizontal"
        cls: Additional CSS classes
        **attrs: Additional HTML attributes passed through

    Returns:
        HtmlString: Rendered radio group container

    Example:
        from nitro.infrastructure.html.datastar import Signals

        form = Signals(size="md")

        RadioGroup(
            RadioItem("Small", value="sm"),
            RadioItem("Medium", value="md"),
            RadioItem("Large", value="lg"),
            bind=form.size,
        )
    """
    # Get signal name for binding
    if hasattr(bind, 'to_js'):
        signal_name = bind.to_js().lstrip('$')
    elif isinstance(bind, str):
        signal_name = bind.lstrip('$')
    else:
        signal_name = str(bind)

    # Process children - call closures with signal context
    processed_children = []
    for child in children:
        if callable(child) and not isinstance(child, HtmlString):
            # It's a RadioItem closure - call it with the signal
            processed_children.append(child(signal_name))
        else:
            # It's regular content - pass through
            processed_children.append(child)

    # Orientation classes
    orientation_cls = "flex flex-col gap-2" if orientation == "vertical" else "flex flex-row gap-4"

    return Div(
        *processed_children,
        cls=cn(orientation_cls, cls),
        role="radiogroup",
        **attrs
    )


def RadioItem(
    *children: Any,
    value: str,
    id: str = "",
    name: str = "",
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> Callable[[str], HtmlString]:
    """Radio input item that receives signal from parent RadioGroup.

    Returns a closure that will be called by RadioGroup with the signal name.

    Args:
        *children: Label content (text, icons, etc.) rendered next to radio
        value: Value for this radio option (required)
        id: Unique identifier for the radio (auto-generated if not provided)
        name: Name attribute for the radio group (uses signal name if not provided)
        disabled: Whether the radio is disabled
        cls: Additional CSS classes
        **attrs: Additional HTML attributes passed through

    Returns:
        Callable: Closure that accepts signal_name and returns HtmlString

    Example:
        RadioItem("Option 1", value="opt1")
        RadioItem("Option 2", value="opt2", disabled=True)
    """
    def create_radio(signal_name: str) -> HtmlString:
        # Generate ID if not provided
        radio_id = id if id else f"radio-{signal_name}-{value}"
        radio_name = name if name else signal_name

        radio_attrs: dict[str, Any] = {
            "type": "radio",
            "id": radio_id,
            "name": radio_name,
            "value": value,
            "disabled": disabled if disabled else None,
            "data_bind": signal_name,
            "cls": cn("input"),
        }

        # Merge additional attributes
        radio_attrs.update(attrs)

        # Create the radio input - only add cls if user provided classes
        input_kwargs = {k: v for k, v in radio_attrs.items() if v is not None}

        radio_input = HTMLInput(**input_kwargs)

        # If no children (label text), return just the radio
        if not children:
            return radio_input

        # If there are children, wrap in a label for accessibility
        label_cls = "inline-flex items-center cursor-pointer gap-2"
        if disabled:
            label_cls = cn(label_cls, "opacity-50 cursor-not-allowed")

        return HTMLLabel(
            radio_input,
            Span(*children),
            html_for=radio_id,
            cls=cn(label_cls, cls),
        )

    return create_radio
