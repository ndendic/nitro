"""DatePicker component using Calendar and Popover composition.

A complete date picker implementation following the shadcn/ui pattern,
using Calendar in a Popover with a Button trigger.
"""

from typing import Any, Optional
from datetime import datetime
import rusty_tags as rt
from rusty_tags.datastar import Signal
from .utils import cn
from .button import Button
from .popover import Popover, PopoverTrigger, PopoverContent
from .calendar import Calendar


def DatePicker(
    *,
    id: Optional[str] = None,
    bind: Signal | str | None = None,
    value: str | None = None,
    placeholder: str = "Pick a date",
    min_date: str | None = None,
    max_date: str | None = None,
    disabled_dates: list[str] | None = None,
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """DatePicker component using Calendar in a Popover.

    A complete date picker that shows a calendar in a popover when clicked.
    Displays the selected date or placeholder text when no date is selected.

    Args:
        id: Unique identifier
        bind: Datastar signal for selected date (YYYY-MM-DD format)
        value: Initial selected date (YYYY-MM-DD format)
        placeholder: Text shown when no date is selected
        min_date: Minimum selectable date (YYYY-MM-DD format)
        max_date: Maximum selectable date (YYYY-MM-DD format)
        disabled_dates: List of disabled dates (YYYY-MM-DD format)
        disabled: Whether the picker is disabled
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Complete DatePicker with trigger button and calendar popover

    Example:
        from nitro.infrastructure.html.datastar import Signals

        sigs = Signals(selected_date="2025-12-23")

        DatePicker(
            bind=sigs.selected_date,
            placeholder="Select appointment date",
            min_date="2025-01-01",
        )
    """
    # Generate popover ID
    popover_id = id or "datepicker"

    # Extract signal name for reactive display
    signal_name = None
    if bind is not None:
        if hasattr(bind, 'to_js'):
            signal_name = bind.to_js().lstrip('$')
        elif isinstance(bind, str):
            signal_name = bind.lstrip('$')

    # Calendar icon SVG
    calendar_icon = rt.Svg(
        rt.Rect(x="3", y="4", width="18", height="18", rx="2", ry="2", stroke="currentColor", stroke_width="2", fill="none"),
        rt.Line(x1="16", y1="2", x2="16", y2="6", stroke="currentColor", stroke_width="2"),
        rt.Line(x1="8", y1="2", x2="8", y2="6", stroke="currentColor", stroke_width="2"),
        rt.Line(x1="3", y1="10", x2="21", y2="10", stroke="currentColor", stroke_width="2"),
        viewBox="0 0 24 24",
        cls="w-4 h-4 mr-2",
        xmlns="http://www.w3.org/2000/svg",
    )

    # Build the display text span with reactive binding
    if signal_name:
        # Reactive display: show formatted date or placeholder
        # Use JavaScript Date formatting for client-side display
        format_expr = f"new Date(${signal_name} + 'T00:00:00').toLocaleDateString('en-US', {{month: 'short', day: 'numeric', year: 'numeric'}})"
        display_span = rt.Span(
            placeholder,
            data_text=f"${signal_name} ? {format_expr} : '{placeholder}'",
            data_class_text_muted_foreground=f"!${signal_name}",
        )
    else:
        # Static display
        display_text = _format_date_display(value) if value else placeholder
        display_span = rt.Span(
            display_text,
            cls=cn("" if value else "text-muted-foreground"),
        )

    # Build the trigger button
    trigger_content = Button(
        calendar_icon,
        display_span,
        variant="outline",
        type="button",
        cls=cn("w-full justify-start text-left font-normal", cls),
        disabled=disabled,
    )

    # Build the popover with calendar
    return Popover(
        PopoverTrigger(trigger_content),
        PopoverContent(
            Calendar(
                bind=bind,
                value=value,
                min_date=min_date,
                max_date=max_date,
                disabled_dates=disabled_dates,
                popover_id=popover_id,
            ),
            side="bottom",
            align="start",
        ),
        id=popover_id,
        **attrs,
    )


def DateRangePicker(
    *,
    id: Optional[str] = None,
    bind_start: Signal | str | None = None,
    bind_end: Signal | str | None = None,
    start_value: str | None = None,
    end_value: str | None = None,
    placeholder: str = "Pick a date range",
    min_date: str | None = None,
    max_date: str | None = None,
    disabled_dates: list[str] | None = None,
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """DateRangePicker for selecting a date range.

    Similar to DatePicker but allows selecting a start and end date.

    Args:
        id: Unique identifier
        bind_start: Datastar signal for start date (YYYY-MM-DD format)
        bind_end: Datastar signal for end date (YYYY-MM-DD format)
        start_value: Initial start date (YYYY-MM-DD format)
        end_value: Initial end date (YYYY-MM-DD format)
        placeholder: Text shown when no dates are selected
        min_date: Minimum selectable date (YYYY-MM-DD format)
        max_date: Maximum selectable date (YYYY-MM-DD format)
        disabled_dates: List of disabled dates (YYYY-MM-DD format)
        disabled: Whether the picker is disabled
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Complete DateRangePicker with trigger button and calendar popover

    Example:
        from nitro.infrastructure.html.datastar import Signals

        sigs = Signals(
            start_date="2025-12-01",
            end_date="2025-12-31",
        )

        DateRangePicker(
            bind_start=sigs.start_date,
            bind_end=sigs.end_date,
            placeholder="Select date range",
        )
    """
    # Generate popover ID
    popover_id = id or "daterangepicker"

    # Extract signal names
    start_signal_name = None
    if bind_start is not None:
        if hasattr(bind_start, 'to_js'):
            start_signal_name = bind_start.to_js().lstrip('$')
        elif isinstance(bind_start, str):
            start_signal_name = bind_start.lstrip('$')

    end_signal_name = None
    if bind_end is not None:
        if hasattr(bind_end, 'to_js'):
            end_signal_name = bind_end.to_js().lstrip('$')
        elif isinstance(bind_end, str):
            end_signal_name = bind_end.lstrip('$')

    # Calendar icon
    calendar_icon = rt.Svg(
        rt.Rect(x="3", y="4", width="18", height="18", rx="2", ry="2", stroke="currentColor", stroke_width="2", fill="none"),
        rt.Line(x1="16", y1="2", x2="16", y2="6", stroke="currentColor", stroke_width="2"),
        rt.Line(x1="8", y1="2", x2="8", y2="6", stroke="currentColor", stroke_width="2"),
        rt.Line(x1="3", y1="10", x2="21", y2="10", stroke="currentColor", stroke_width="2"),
        viewBox="0 0 24 24",
        cls="w-4 h-4 mr-2",
        xmlns="http://www.w3.org/2000/svg",
    )

    # Build display text with reactive binding
    if start_signal_name and end_signal_name:
        # Reactive display
        format_start = f"new Date(${start_signal_name} + 'T00:00:00').toLocaleDateString('en-US', {{month: 'short', day: 'numeric', year: 'numeric'}})"
        format_end = f"new Date(${end_signal_name} + 'T00:00:00').toLocaleDateString('en-US', {{month: 'short', day: 'numeric', year: 'numeric'}})"
        display_expr = f"${start_signal_name} && ${end_signal_name} ? {format_start} + ' - ' + {format_end} : (${start_signal_name} ? {format_start} + ' - ...' : '{placeholder}')"
        display_span = rt.Span(
            placeholder,
            data_text=display_expr,
            data_class_text_muted_foreground=f"!${start_signal_name} && !${end_signal_name}",
        )
    else:
        # Static display
        if start_value and end_value:
            display_text = f"{_format_date_display(start_value)} - {_format_date_display(end_value)}"
        elif start_value:
            display_text = f"{_format_date_display(start_value)} - ..."
        else:
            display_text = placeholder
        display_span = rt.Span(
            display_text,
            cls=cn("" if (start_value or end_value) else "text-muted-foreground"),
        )

    # Build the trigger button
    trigger_content = Button(
        calendar_icon,
        display_span,
        variant="outline",
        type="button",
        cls=cn("w-full justify-start text-left font-normal", cls),
        disabled=disabled,
    )

    # Build the popover with two calendars side by side
    return Popover(
        PopoverTrigger(trigger_content),
        PopoverContent(
            rt.Div(
                rt.Div(
                    rt.Span("From", cls="text-sm font-medium mb-2 block"),
                    Calendar(
                        bind=bind_start,
                        value=start_value,
                        min_date=min_date,
                        max_date=end_value or max_date,  # Can't select start after end
                        disabled_dates=disabled_dates,
                        show_navigation=True,
                    ),
                ),
                rt.Div(
                    rt.Span("To", cls="text-sm font-medium mb-2 block"),
                    Calendar(
                        bind=bind_end,
                        value=end_value,
                        min_date=start_value or min_date,  # Can't select end before start
                        max_date=max_date,
                        disabled_dates=disabled_dates,
                        show_navigation=True,
                    ),
                ),
                cls="flex gap-4",
            ),
            side="bottom",
            align="start",
        ),
        id=popover_id,
        **attrs,
    )


def _format_date_display(date_str: str) -> str:
    """Format date for display in the button.

    Converts YYYY-MM-DD to a more readable format like "Dec 23, 2025".
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%b %d, %Y")
    except ValueError:
        return date_str
