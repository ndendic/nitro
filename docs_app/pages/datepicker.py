"""DatePicker and Calendar component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.events import on, emit_elements

from nitro.infrastructure.html.components import DatePicker, DateRangePicker, Calendar

router: APIRouter = APIRouter()


def example_basic_datepicker():
    return Div(
        DatePicker(
            id="basic-date",
            placeholder="Select a date",
        ),
        cls="w-[280px]"
    )


def example_datepicker_with_binding():
    sigs = Signals(appointment_date="")
    return Div(
        DatePicker(
            id="appointment",
            bind=sigs.appointment_date,
            placeholder="Select appointment date",
        ),
        Div(
            P("Selected date: ", Span(data_text="$appointment_date || 'None'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="w-[280px]"
    )


def example_datepicker_with_value():
    sigs = Signals(event_date="2025-12-25")
    return Div(
        DatePicker(
            id="event-date",
            bind=sigs.event_date,
            value="2025-12-25",
            placeholder="Select event date",
        ),
        Div(
            P("Event date: ", Span(data_text="$event_date")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="w-[280px]"
    )


def example_datepicker_constraints():
    sigs = Signals(booking_date="")
    return Div(
        P("Only dates in December 2025 are selectable:", cls="text-sm text-muted-foreground mb-2"),
        DatePicker(
            id="booking",
            bind=sigs.booking_date,
            placeholder="Select booking date",
            min_date="2025-12-01",
            max_date="2025-12-31",
        ),
        Div(
            P("Booking date: ", Span(data_text="$booking_date || 'None'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="w-[280px]"
    )


def example_datepicker_disabled_dates():
    sigs = Signals(available_date="")
    return Div(
        P("Weekends (21st, 22nd, 28th, 29th) are disabled:", cls="text-sm text-muted-foreground mb-2"),
        DatePicker(
            id="available",
            bind=sigs.available_date,
            placeholder="Select available date",
            disabled_dates=["2025-12-21", "2025-12-22", "2025-12-28", "2025-12-29"],
        ),
        Div(
            P("Selected: ", Span(data_text="$available_date || 'None'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="w-[280px]"
    )


def example_datepicker_disabled():
    return Div(
        DatePicker(
            id="disabled-picker",
            placeholder="Disabled date picker",
            disabled=True,
        ),
        cls="w-[280px]"
    )


def example_daterangepicker():
    sigs = Signals(start_date="", end_date="")
    return Div(
        DateRangePicker(
            id="date-range",
            bind_start=sigs.start_date,
            bind_end=sigs.end_date,
            placeholder="Select date range",
        ),
        Div(
            P("Start: ", Span(data_text="$start_date || 'None'")),
            P("End: ", Span(data_text="$end_date || 'None'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="w-[400px]"
    )


def example_calendar_standalone():
    sigs = Signals(cal_date="")
    return Div(
        Calendar(
            id="standalone-cal",
            bind=sigs.cal_date,
        ),
        Div(
            P("Selected: ", Span(data_text="$cal_date || 'None'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
    )


def example_calendar_with_value():
    sigs = Signals(preset_date="2025-12-15")
    return Div(
        Calendar(
            id="preset-cal",
            bind=sigs.preset_date,
            value="2025-12-15",
        ),
        Div(
            P("Selected: ", Span(data_text="$preset_date")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
    )


page = Div(
    H1("DatePicker & Calendar Components"),
    P(
        "Date selection components using Calendar in a Popover. The DatePicker provides "
        "a button trigger that opens a calendar for date selection, while Calendar can "
        "be used standalone for inline date picking."
    ),

    # DatePicker Section
    H2("DatePicker", cls="text-3xl font-bold mt-8 mb-4"),
    P(
        "A complete date picker that shows a calendar in a popover when clicked. "
        "Supports Datastar two-way binding, min/max constraints, and disabled dates.",
        cls="text-muted-foreground mb-6"
    ),

    TitledSection(
        "Basic DatePicker",
        P("A simple date picker with placeholder text:"),
        ComponentShowcase(example_basic_datepicker),
    ),
    TitledSection(
        "With Datastar Binding",
        P("DatePicker with two-way binding showing live state:"),
        ComponentShowcase(example_datepicker_with_binding),
    ),
    TitledSection(
        "With Initial Value",
        P("DatePicker with a pre-selected date:"),
        ComponentShowcase(example_datepicker_with_value),
    ),
    TitledSection(
        "Date Constraints",
        P("Restrict selectable dates with min_date and max_date:"),
        ComponentShowcase(example_datepicker_constraints),
    ),
    TitledSection(
        "Disabled Dates",
        P("Specific dates can be disabled:"),
        ComponentShowcase(example_datepicker_disabled_dates),
    ),
    TitledSection(
        "Disabled State",
        P("The entire date picker can be disabled:"),
        ComponentShowcase(example_datepicker_disabled),
    ),

    # DateRangePicker Section
    H2("DateRangePicker", cls="text-3xl font-bold mt-8 mb-4"),
    P(
        "For selecting a date range with start and end dates. Shows two calendars "
        "side by side with automatic constraint handling.",
        cls="text-muted-foreground mb-6"
    ),

    TitledSection(
        "Date Range Selection",
        P("Select a start and end date:"),
        ComponentShowcase(example_daterangepicker),
    ),

    # Calendar Section
    H2("Calendar (Standalone)", cls="text-3xl font-bold mt-8 mb-4"),
    P(
        "The Calendar component can be used directly for inline date selection "
        "without the popover wrapper.",
        cls="text-muted-foreground mb-6"
    ),

    TitledSection(
        "Standalone Calendar",
        P("Calendar displayed inline:"),
        ComponentShowcase(example_calendar_standalone),
    ),
    TitledSection(
        "Calendar with Pre-selected Date",
        P("Calendar with an initial value:"),
        ComponentShowcase(example_calendar_with_value),
    ),

    # API Reference
    TitledSection(
        "DatePicker API Reference",
        CodeBlock(
            """
def DatePicker(
    *,
    id: str = None,              # Unique identifier
    bind: Signal | str = None,   # Datastar signal for selected date
    value: str = None,           # Initial date (YYYY-MM-DD format)
    placeholder: str = "Pick a date",  # Text when no date selected
    min_date: str = None,        # Minimum selectable date (YYYY-MM-DD)
    max_date: str = None,        # Maximum selectable date (YYYY-MM-DD)
    disabled_dates: list = None, # List of disabled dates (YYYY-MM-DD)
    disabled: bool = False,      # Whether picker is disabled
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString
""",
            code_cls="language-python",
        ),
    ),
    TitledSection(
        "DateRangePicker API Reference",
        CodeBlock(
            """
def DateRangePicker(
    *,
    id: str = None,               # Unique identifier
    bind_start: Signal | str = None,  # Signal for start date
    bind_end: Signal | str = None,    # Signal for end date
    start_value: str = None,      # Initial start date (YYYY-MM-DD)
    end_value: str = None,        # Initial end date (YYYY-MM-DD)
    placeholder: str = "Pick a date range",  # Text when no dates
    min_date: str = None,         # Minimum selectable date
    max_date: str = None,         # Maximum selectable date
    disabled_dates: list = None,  # List of disabled dates
    disabled: bool = False,       # Whether picker is disabled
    cls: str = "",                # Additional CSS classes
    **attrs                       # Additional HTML attributes
) -> HtmlString
""",
            code_cls="language-python",
        ),
    ),
    TitledSection(
        "Calendar API Reference",
        CodeBlock(
            """
def Calendar(
    *,
    id: str = None,              # Unique identifier
    bind: Signal | str = None,   # Datastar signal for selected date
    value: str = None,           # Initial date (YYYY-MM-DD format)
    min_date: str = None,        # Minimum selectable date
    max_date: str = None,        # Maximum selectable date
    disabled_dates: list = None, # List of disabled dates
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString
""",
            code_cls="language-python",
        ),
    ),
    TitledSection(
        "Usage Example",
        CodeBlock(
            """
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.html.components import DatePicker, Calendar

# Create signals
sigs = Signals(selected_date="", start="", end="")

# Basic DatePicker with binding
DatePicker(
    id="appointment",
    bind=sigs.selected_date,
    placeholder="Select appointment date",
    min_date="2025-01-01",
    max_date="2025-12-31",
)

# Date Range Picker
DateRangePicker(
    bind_start=sigs.start,
    bind_end=sigs.end,
    placeholder="Select travel dates",
)

# Standalone Calendar (inline)
Calendar(
    bind=sigs.selected_date,
    value="2025-12-23",
)
""",
            code_cls="language-python",
        ),
    ),

    # Known Issues Section
    TitledSection(
        "Known Limitations",
        Alert(
            AlertTitle("Current Limitations"),
            AlertDescription(
                Ul(
                    Li("Calendar does not have month/year navigation - it shows a static month based on the initial value or current date"),
                    Li("The popover does not close automatically after selecting a date"),
                    Li("The display text in the trigger button doesn't update reactively when the signal changes"),
                    cls="list-disc list-inside space-y-1"
                )
            ),
            variant="warning",
        ),
        cls="mt-8",
    ),

    BackLink(),
    id="content"
)


@router.get("/xtras/datepicker")
@template(title="DatePicker Component Documentation")
def datepicker_page():
    return page


@on("page.datepicker")
async def get_datepicker(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.datepicker")
