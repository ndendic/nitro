"""Calendar component for date selection with Datastar reactivity.

A calendar grid component that displays a month view with navigation,
date selection, and support for min/max constraints.
"""

from typing import Any, Optional
from datetime import datetime, timedelta
import calendar
import rusty_tags as rt
from rusty_tags.datastar import Signal, Signals
from .utils import cn
from .button import Button


# Month names constant
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def Calendar(
    *,
    id: Optional[str] = None,
    bind: Signal | str | None = None,
    value: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
    disabled_dates: list[str] | None = None,
    show_navigation: bool = True,
    popover_id: str | None = None,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """Calendar component for date selection.

    Displays a monthly calendar grid with navigation. Uses Datastar signals
    for month/year navigation and date selection state.

    Args:
        id: Unique identifier
        bind: Datastar signal for selected date (YYYY-MM-DD format)
        value: Initial selected date (YYYY-MM-DD format)
        min_date: Minimum selectable date (YYYY-MM-DD format)
        max_date: Maximum selectable date (YYYY-MM-DD format)
        disabled_dates: List of disabled dates (YYYY-MM-DD format)
        show_navigation: Whether to show prev/next month buttons
        popover_id: ID of parent popover to close on selection (optional)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Calendar component with month navigation and date selection

    Example:
        Calendar(
            bind=sigs.selected_date,
            value="2025-12-23",
            min_date="2025-01-01",
            max_date="2025-12-31",
        )
    """
    # Parse current value or default to today
    if value:
        try:
            current_date = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            current_date = datetime.now()
    else:
        current_date = datetime.now()

    # Extract signal name for binding
    signal_name = None
    if bind is not None:
        if hasattr(bind, 'to_js'):
            signal_name = bind.to_js().lstrip('$')
        elif isinstance(bind, str):
            signal_name = bind.lstrip('$')

    # Generate unique prefix for calendar signals (replace hyphens with underscores for valid signal names)
    raw_cal_id = id or f"cal_{signal_name or 'default'}"
    cal_id = raw_cal_id.replace('-', '_')
    month_signal = f"{cal_id}_month"
    year_signal = f"{cal_id}_year"

    year = current_date.year
    month = current_date.month

    # Build navigation buttons
    nav_buttons = []
    if show_navigation:
        # Previous month button
        prev_click = f"${month_signal} === 1 ? (${month_signal} = 12, ${year_signal}--) : ${month_signal}--"
        nav_buttons.append(
            Button(
                rt.Svg(
                    rt.Path(d="M15 18l-6-6 6-6", fill="none", stroke="currentColor", stroke_width="2"),
                    xmlns="http://www.w3.org/2000/svg",
                    viewBox="0 0 24 24",
                    cls="w-4 h-4",
                ),
                variant="icon-ghost",
                size="icon",
                type="button",
                aria_label="Previous month",
                cls="calendar-nav-button",
                on_click=prev_click,
            )
        )
        # Next month button
        next_click = f"${month_signal} === 12 ? (${month_signal} = 1, ${year_signal}++) : ${month_signal}++"
        nav_buttons.append(
            Button(
                rt.Svg(
                    rt.Path(d="M9 18l6-6-6-6", fill="none", stroke="currentColor", stroke_width="2"),
                    xmlns="http://www.w3.org/2000/svg",
                    viewBox="0 0 24 24",
                    cls="w-4 h-4",
                ),
                variant="icon-ghost",
                size="icon",
                type="button",
                aria_label="Next month",
                cls="calendar-nav-button",
                on_click=next_click,
            )
        )

    # Weekday headers
    weekday_headers = rt.Div(
        *[
            rt.Div(
                day,
                cls="calendar-head-cell",
            )
            for day in ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
        ],
        cls="calendar-grid",
    )

    # Build calendar grid for the initial month
    days_grid = _build_days_grid(
        year, month, signal_name, value, min_date, max_date, disabled_dates, popover_id
    )

    # Header with navigation and month/year title
    if show_navigation:
        header = rt.Div(
            rt.Div(*nav_buttons, cls="calendar-nav flex gap-1"),
            rt.H3(
                f"{MONTH_NAMES[month - 1]} {year}",
                cls="calendar-title text-sm font-semibold",
            ),
            cls="calendar-header flex items-center justify-between mb-4",
        )
    else:
        header = rt.Div(
            rt.H3(
                f"{MONTH_NAMES[month - 1]} {year}",
                cls="calendar-title text-sm font-semibold",
            ),
            cls="calendar-header",
        )

    # Create signals for calendar state
    cal_signals = Signals(**{month_signal: month, year_signal: year})

    return rt.Div(
        header,
        weekday_headers,
        days_grid,
        cls=cn("calendar", cls),
        id=id,
        signals=cal_signals,
        **attrs,
    )


def _build_days_grid(
    year: int,
    month: int,
    signal_name: str | None,
    selected_date: str | None,
    min_date: str | None,
    max_date: str | None,
    disabled_dates: list[str] | None,
    popover_id: str | None = None,
) -> rt.HtmlString:
    """Build the days grid for a given month."""
    # Get first day of month and number of days
    first_day = datetime(year, month, 1)
    first_weekday = first_day.weekday()
    # Adjust for Sunday start (calendar module uses Monday=0)
    first_weekday = (first_weekday + 1) % 7

    num_days = calendar.monthrange(year, month)[1]

    # Previous month days to fill the grid
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    prev_month_days = calendar.monthrange(prev_year, prev_month)[1]

    # Build calendar grid (6 weeks)
    days = []
    day_counter = 1
    next_month_day = 1

    for week in range(6):
        for weekday in range(7):
            cell_index = week * 7 + weekday

            if cell_index < first_weekday:
                # Previous month
                day_num = prev_month_days - first_weekday + cell_index + 1
                date_str = f"{prev_year:04d}-{prev_month:02d}-{day_num:02d}"
                days.append(
                    _create_day_button(
                        day_num,
                        date_str,
                        signal_name,
                        selected_date=selected_date,
                        is_today=False,
                        is_outside_month=True,
                        is_disabled=_is_date_disabled(date_str, min_date, max_date, disabled_dates),
                        popover_id=popover_id,
                    )
                )
            elif day_counter <= num_days:
                # Current month
                date_str = f"{year:04d}-{month:02d}-{day_counter:02d}"
                today = datetime.now().strftime("%Y-%m-%d")
                days.append(
                    _create_day_button(
                        day_counter,
                        date_str,
                        signal_name,
                        selected_date=selected_date,
                        is_today=(date_str == today),
                        is_outside_month=False,
                        is_disabled=_is_date_disabled(date_str, min_date, max_date, disabled_dates),
                        popover_id=popover_id,
                    )
                )
                day_counter += 1
            else:
                # Next month
                if month == 12:
                    next_month = 1
                    next_year = year + 1
                else:
                    next_month = month + 1
                    next_year = year
                date_str = f"{next_year:04d}-{next_month:02d}-{next_month_day:02d}"
                days.append(
                    _create_day_button(
                        next_month_day,
                        date_str,
                        signal_name,
                        selected_date=selected_date,
                        is_today=False,
                        is_outside_month=True,
                        is_disabled=_is_date_disabled(date_str, min_date, max_date, disabled_dates),
                        popover_id=popover_id,
                    )
                )
                next_month_day += 1

    return rt.Div(*days, cls="calendar-grid")


def _create_day_button(
    day: int,
    date_str: str,
    signal_name: str | None,
    selected_date: str | None,
    is_today: bool,
    is_outside_month: bool,
    is_disabled: bool,
    popover_id: str | None = None,
) -> rt.HtmlString:
    """Create a single day button for the calendar grid."""
    attrs = {}

    # Data attributes for styling
    if is_today:
        attrs["data_today"] = "true"
    if is_outside_month:
        attrs["data_outside_month"] = "true"
    # Use reactive class binding for selected state
    if signal_name:
        attrs["data_class:selected"] = f"${signal_name} === '{date_str}'"
    elif selected_date and date_str == selected_date:
        attrs["data_selected"] = "true"
    if is_disabled:
        attrs["data_disabled"] = "true"
        attrs["disabled"] = True

    # Click handler to set selected date and optionally close popover
    if signal_name and not is_disabled:
        click_action = f"${signal_name} = '{date_str}'"
        if popover_id:
            # Also close the popover - use same naming convention as Popover component
            popover_signal = f"{popover_id.replace('-', '_')}_open"
            click_action = f"${signal_name} = '{date_str}'; ${popover_signal} = false"
        attrs["on_click"] = click_action

    return rt.Button(
        str(day),
        cls="calendar-day",
        type="button",
        **attrs,
    )


def _is_date_disabled(
    date_str: str,
    min_date: str | None,
    max_date: str | None,
    disabled_dates: list[str] | None,
) -> bool:
    """Check if a date should be disabled."""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")

        if min_date:
            min_dt = datetime.strptime(min_date, "%Y-%m-%d")
            if date < min_dt:
                return True

        if max_date:
            max_dt = datetime.strptime(max_date, "%Y-%m-%d")
            if date > max_dt:
                return True

        if disabled_dates and date_str in disabled_dates:
            return True

        return False
    except ValueError:
        return False
