"""Select component with Datastar binding support."""

from typing import Any, Optional
from rusty_tags import Select as HTMLSelect, Option as HTMLOption, HtmlString
from .utils import cn


def Select(
    *children: Any,
    id: Optional[str] = None,
    bind: Any = None,
    placeholder: str = "",
    disabled: bool = False,
    required: bool = False,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Native select dropdown with Datastar two-way binding.

    Uses Basecoat's context-based styling inside Field.
    When placed inside a .field container, the select is
    automatically styled via Basecoat CSS. Can also use .select class
    for standalone usage.

    Args:
        *children: SelectOption elements
        id: Unique identifier for the select (optional, used for label association)
        bind: Datastar Signal for two-way binding (optional)
        placeholder: Placeholder text shown as first disabled option
        disabled: Whether the select is disabled
        required: Whether the select is required
        cls: Additional CSS classes
        **attrs: Additional HTML attributes passed through

    Returns:
        HtmlString: Rendered select element

    Example:
        # Basic select with options
        Select(
            SelectOption("Small", value="sm"),
            SelectOption("Medium", value="md"),
            SelectOption("Large", value="lg"),
            id="size",
        )

        # With Datastar binding
        from nitro.infrastructure.html.datastar import Signal, Signals
        form = Signals(size="md")
        Select(
            SelectOption("Small", value="sm"),
            SelectOption("Medium", value="md"),
            SelectOption("Large", value="lg"),
            id="size",
            bind=form.size,
        )

        # Inside a Field (recommended for forms)
        Field(
            Select(
                SelectOption("Red", value="red"),
                SelectOption("Green", value="green"),
                SelectOption("Blue", value="blue"),
                id="color",
                bind=form.color,
            ),
            label="Color",
            label_for="color",
        )
    """
    select_attrs: dict[str, Any] = {
        "id": id if id else None,
        "name": attrs.pop("name", id) if id else attrs.pop("name", None),
        "disabled": disabled if disabled else None,
        "required": required if required else None,
    }

    # Handle Datastar binding
    if bind is not None:
        # Signal from Datastar
        if hasattr(bind, 'to_js'):
            # Get the signal name without the $ prefix
            signal_name = bind.to_js().lstrip('$')
            select_attrs["data_bind"] = signal_name
        elif isinstance(bind, str):
            select_attrs["data_bind"] = bind.lstrip('$')

    # Merge additional attributes
    select_attrs.update(attrs)

    # Create the select - add .select class for Basecoat styling
    # Basecoat CSS targets: .form/.field select OR select.select
    input_kwargs = {k: v for k, v in select_attrs.items() if v is not None}
    input_kwargs["cls"] = cn("select", cls) if cls else "select"

    # Build options list
    options = []

    # Add placeholder option if provided
    if placeholder:
        options.append(HTMLOption(placeholder, value="", disabled=True, selected=True))

    # Add all child options
    options.extend(children)

    return HTMLSelect(*options, **input_kwargs)


def SelectOption(
    *children: Any,
    value: str,
    disabled: bool = False,
    selected: bool = False,
    **attrs: Any,
) -> HtmlString:
    """Option element for Select component.

    Args:
        *children: Option label content
        value: The value to submit when this option is selected
        disabled: Whether the option is disabled
        selected: Whether the option is initially selected (use bind instead)
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered option element

    Example:
        SelectOption("Small (S)", value="sm")
        SelectOption("Medium (M)", value="md")
        SelectOption("Large (L)", value="lg", disabled=True)
    """
    option_attrs: dict[str, Any] = {
        "value": value,
        "disabled": disabled if disabled else None,
        "selected": selected if selected else None,
    }

    # Merge additional attributes
    option_attrs.update(attrs)

    # Filter out None values
    option_kwargs = {k: v for k, v in option_attrs.items() if v is not None}

    return HTMLOption(*children, **option_kwargs)


def SelectOptGroup(
    *children: Any,
    label: str,
    disabled: bool = False,
    **attrs: Any,
) -> HtmlString:
    """Option group element for Select component.

    Args:
        *children: SelectOption elements in this group
        label: Group label shown in the dropdown
        disabled: Whether all options in this group are disabled
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered optgroup element

    Example:
        Select(
            SelectOptGroup(
                SelectOption("Red", value="red"),
                SelectOption("Blue", value="blue"),
                label="Colors"
            ),
            SelectOptGroup(
                SelectOption("Small", value="sm"),
                SelectOption("Large", value="lg"),
                label="Sizes"
            ),
            id="option",
        )
    """
    from rusty_tags import Optgroup as HTMLOptgroup

    optgroup_attrs: dict[str, Any] = {
        "label": label,
        "disabled": disabled if disabled else None,
    }

    # Merge additional attributes
    optgroup_attrs.update(attrs)

    # Filter out None values
    optgroup_kwargs = {k: v for k, v in optgroup_attrs.items() if v is not None}

    return HTMLOptgroup(*children, **optgroup_kwargs)
