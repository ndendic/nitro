"""DatePicker component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import DatePicker, DateRangePicker

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


def example_datepicker_format():
    sigs = Signals(formatted_date="")
    return Div(
        P("Custom date format (mm/dd/yyyy):", cls="text-sm text-muted-foreground mb-2"),
        DatePicker(
            id="formatted",
            bind=sigs.formatted_date,
            placeholder="MM/DD/YYYY",
            format="mm/dd/yyyy",
        ),
        Div(
            P("Selected: ", Span(data_text="$formatted_date || 'None'")),
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
            start_placeholder="Check-in",
            end_placeholder="Check-out",
        ),
        Div(
            P("Start: ", Span(data_text="$start_date || 'None'")),
            P("End: ", Span(data_text="$end_date || 'None'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="w-full max-w-md"
    )


def example_daterangepicker_constrained():
    sigs = Signals(range_start="", range_end="")
    return Div(
        P("Booking dates in Q1 2025:", cls="text-sm text-muted-foreground mb-2"),
        DateRangePicker(
            id="booking-range",
            bind_start=sigs.range_start,
            bind_end=sigs.range_end,
            start_placeholder="Start date",
            end_placeholder="End date",
            min_date="2025-01-01",
            max_date="2025-03-31",
        ),
        Div(
            P("Range: ", Span(data_text="($range_start || '...') + ' to ' + ($range_end || '...')")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="w-full max-w-md"
    )


page = Div(
    H1("DatePicker"),
    P(
        "Date selection components using vanillajs-datepicker. Provides a simple, "
        "accessible date picker with calendar dropdown, min/max constraints, and "
        "Datastar two-way binding support."
    ),

    # DatePicker Section
    H2("DatePicker", cls="text-3xl font-bold mt-8 mb-4"),
    P(
        "A simple date picker input with a calendar dropdown. Click the input to open "
        "the calendar and select a date. The picker closes automatically after selection.",
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
        "Custom Format",
        P("Use a different date format for display:"),
        ComponentShowcase(example_datepicker_format),
    ),
    TitledSection(
        "Disabled State",
        P("The date picker can be disabled:"),
        ComponentShowcase(example_datepicker_disabled),
    ),

    # DateRangePicker Section
    H2("DateRangePicker", cls="text-3xl font-bold mt-8 mb-4"),
    P(
        "For selecting a date range with start and end dates. The two inputs are "
        "linked - the end date picker automatically constrains to dates after the "
        "selected start date.",
        cls="text-muted-foreground mb-6"
    ),

    TitledSection(
        "Date Range Selection",
        P("Select a start and end date:"),
        ComponentShowcase(example_daterangepicker),
    ),
    TitledSection(
        "Constrained Range",
        P("Date range with min/max constraints:"),
        ComponentShowcase(example_daterangepicker_constrained),
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
    value: str = "",             # Initial date (YYYY-MM-DD format)
    placeholder: str = "Select date",
    format: str = "yyyy-mm-dd",  # Display format
    min_date: str = None,        # Minimum selectable date (YYYY-MM-DD)
    max_date: str = None,        # Maximum selectable date (YYYY-MM-DD)
    autohide: bool = True,       # Hide picker on selection
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
    id: str = None,               # Unique identifier prefix
    bind_start: Signal | str = None,  # Signal for start date
    bind_end: Signal | str = None,    # Signal for end date
    start_value: str = "",        # Initial start date (YYYY-MM-DD)
    end_value: str = "",          # Initial end date (YYYY-MM-DD)
    start_placeholder: str = "Start date",
    end_placeholder: str = "End date",
    format: str = "yyyy-mm-dd",   # Display format
    min_date: str = None,         # Minimum selectable date
    max_date: str = None,         # Maximum selectable date
    autohide: bool = True,        # Hide picker on selection
    disabled: bool = False,       # Whether picker is disabled
    cls: str = "",                # Additional CSS classes
    **attrs                       # Additional HTML attributes
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
from nitro.infrastructure.html.components import DatePicker, DateRangePicker

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

# With custom format
DatePicker(
    bind=sigs.selected_date,
    format="mm/dd/yyyy",
    placeholder="MM/DD/YYYY",
)

# Date Range Picker
DateRangePicker(
    bind_start=sigs.start,
    bind_end=sigs.end,
    start_placeholder="Check-in",
    end_placeholder="Check-out",
)
""",
            code_cls="language-python",
        ),
    ),

    # Implementation Notes
    TitledSection(
        "Implementation Notes",
        Alert(
            AlertTitle("Dependencies"),
            AlertDescription(
                Ul(
                    Li("Uses vanillajs-datepicker library (loaded via CDN)"),
                    Li("Styled with BaseCoat CSS variables for shadcn theme compatibility"),
                    Li("Supports Datastar two-way binding via the bind parameter"),
                    cls="list-disc list-inside space-y-1"
                )
            ),
            variant="info",
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
