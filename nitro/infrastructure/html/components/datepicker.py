"""DatePicker components using vanillajs-datepicker.

Simple, lightweight date picker components that use the vanillajs-datepicker library
for all date selection functionality. Styled with shadcn/Basecoat CSS variables.

Requires: vanillajs-datepicker CDN script loaded in the page.
"""

from turtle import right
from typing import Any, Optional
import rusty_tags as rt
from rusty_tags.datastar import Signal
from .utils import cn
from .icons import LucideIcon
from .input_group import InputGroup


def DatePicker(
    *,
    id: Optional[str] = None,
    bind: Signal | str | None = None,
    value: str = "",
    placeholder: str = "Select date",
    format: str = "yyyy-mm-dd",
    min_date: str | None = None,
    max_date: str | None = None,
    autohide: bool = True,
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """DatePicker component using vanillajs-datepicker.

    A simple date picker that uses the vanillajs-datepicker library for all
    date selection functionality. Integrates with Datastar for reactive binding.

    Args:
        id: Unique identifier for the input
        bind: Datastar signal for two-way binding (YYYY-MM-DD format)
        value: Initial date value (YYYY-MM-DD format)
        placeholder: Placeholder text when no date selected
        format: Date format for display (default: yyyy-mm-dd)
        min_date: Minimum selectable date (YYYY-MM-DD format)
        max_date: Maximum selectable date (YYYY-MM-DD format)
        autohide: Whether to hide picker on selection (default: True)
        disabled: Whether the picker is disabled
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        DatePicker input with calendar dropdown

    Example:
        from nitro.infrastructure.html.datastar import Signals

        sigs = Signals(selected_date="2025-12-23")

        DatePicker(
            id="appointment",
            bind=sigs.selected_date,
            placeholder="Select appointment date",
            min_date="2025-01-01",
        )
    """
    # Build datepicker options
    options = [f"autohide: {str(autohide).lower()}"]
    options.append(f"format: '{format}'")

    if min_date:
        options.append(f"minDate: '{min_date}'")
    if max_date:
        options.append(f"maxDate: '{max_date}'")

    options_str = ", ".join(options)

    # Build data_init script for datepicker initialization
    init_script = f"new Datepicker(el, {{{options_str}}});"

    # Build input attributes
    input_attrs = {
        "type": "text",
        "placeholder": placeholder,
        "data_init": init_script,
        "cls": cn("input pl-10", cls),
        **attrs,
    }

    if id:
        input_attrs["id"] = id
    if value:
        input_attrs["value"] = value
    if disabled:
        input_attrs["disabled"] = True

    # Add Datastar binding if provided
    if bind is not None:
        input_attrs["bind"] = bind

    return InputGroup(
        rt.Input(**input_attrs),
        right=LucideIcon("calendar"),
    )


def DateRangePicker(
    *,
    id: Optional[str] = None,
    bind_start: Signal | str | None = None,
    bind_end: Signal | str | None = None,
    start_value: str = "",
    end_value: str = "",
    start_placeholder: str = "Start date",
    end_placeholder: str = "End date",
    format: str = "yyyy-mm-dd",
    min_date: str | None = None,
    max_date: str | None = None,
    autohide: bool = False,
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """DateRangePicker for selecting a date range.

    Uses vanillajs-datepicker's DateRangePicker for linked start/end date selection.
    The end date input automatically constrains to dates after the start date.

    Args:
        id: Unique identifier prefix
        bind_start: Datastar signal for start date (YYYY-MM-DD format)
        bind_end: Datastar signal for end date (YYYY-MM-DD format)
        start_value: Initial start date (YYYY-MM-DD format)
        end_value: Initial end date (YYYY-MM-DD format)
        start_placeholder: Placeholder for start date input
        end_placeholder: Placeholder for end date input
        format: Date format for display (default: yyyy-mm-dd)
        min_date: Minimum selectable date (YYYY-MM-DD format)
        max_date: Maximum selectable date (YYYY-MM-DD format)
        autohide: Whether to hide picker on selection (default: True)
        disabled: Whether the picker is disabled
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        DateRangePicker with linked start and end date inputs

    Example:
        from nitro.infrastructure.html.datastar import Signals

        sigs = Signals(start_date="", end_date="")

        DateRangePicker(
            bind_start=sigs.start_date,
            bind_end=sigs.end_date,
            start_placeholder="Check-in",
            end_placeholder="Check-out",
        )
    """
    range_id = id or "daterange"

    # Build datepicker options
    options = [f"autohide: {str(autohide).lower()}"]
    options.append(f"format: '{format}'")

    if min_date:
        options.append(f"minDate: '{min_date}'")
    if max_date:
        options.append(f"maxDate: '{max_date}'")

    options_str = ", ".join(options)

    # DateRangePicker initialization script - applied to the container
    init_script = f"new DateRangePicker(el, {{{options_str}}});"

    # Build start input attributes
    start_attrs = {
        "type": "text",
        "placeholder": start_placeholder,
        "name": f"{range_id}-start",
        "cls": cn("input pl-10", cls),
    }
    if start_value:
        start_attrs["value"] = start_value
    if disabled:
        start_attrs["disabled"] = True
    if bind_start is not None:
        start_attrs["bind"] = bind_start

    # Build end input attributes
    end_attrs = {
        "type": "text",
        "placeholder": end_placeholder,
        "name": f"{range_id}-end",
        "cls": cn("input pl-10", cls),
    }
    if end_value:
        end_attrs["value"] = end_value
    if disabled:
        end_attrs["disabled"] = True
    if bind_end is not None:
        end_attrs["bind"] = bind_end

    return rt.Div(
        InputGroup(
            rt.Input(**start_attrs),
            right=LucideIcon("calendar"),
        ),
        rt.Span("to", cls="text-muted-foreground text-sm px-2"),
        InputGroup(
            rt.Input(**end_attrs),
            right=LucideIcon("calendar"),
        ),
        cls=cn("flex items-center gap-2", cls),
        id=range_id,
        data_init=init_script,
        **attrs,
    )
