"""Example demonstrating DatePicker and Calendar components."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from nitro.infrastructure.html import page_template
from nitro.infrastructure.html.components import (
    DatePicker,
    DateRangePicker,
    Calendar,
    Card,
    CardHeader,
    CardTitle,
    CardContent,
    Field,
)
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.html import Div, H1, P, Pre, Code, Link, Script, Style

# Calendar component CSS (normally loaded from basecoat components)
CALENDAR_CSS = """
/* Calendar container */
.calendar {
    border-radius: 0.375rem;
    border: 1px solid hsl(var(--border));
    background-color: hsl(var(--background));
    width: fit-content;
}

/* Calendar header */
.calendar-header {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid hsl(var(--border));
    text-align: center;
}

.calendar-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: hsl(var(--foreground));
}

/* Calendar grid */
.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 0.125rem;
    padding: 0 0.5rem 0.5rem;
}

/* Weekday headers */
.calendar-head-cell {
    color: hsl(var(--muted-foreground));
    font-size: 0.75rem;
    font-weight: 500;
    text-align: center;
    width: 2rem;
    padding: 0.375rem 0;
}

/* First calendar-grid (weekday headers) needs top padding */
.calendar > .calendar-grid:first-of-type {
    padding-top: 0.5rem;
}

/* Day cells */
.calendar-day {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    font-size: 0.875rem;
    font-weight: 400;
    border-radius: 0.375rem;
    transition: background-color 0.2s, color 0.2s;
    cursor: pointer;
    border: none;
    background: transparent;
}

.calendar-day:hover {
    background-color: hsl(var(--accent));
    color: hsl(var(--accent-foreground));
}

.calendar-day:focus-visible {
    outline: none;
    box-shadow: 0 0 0 2px hsl(var(--ring)), 0 0 0 4px hsl(var(--background));
}

.calendar-day:disabled {
    pointer-events: none;
    opacity: 0.5;
}

/* Today */
.calendar-day[data-today="true"] {
    background-color: hsl(var(--accent));
    color: hsl(var(--accent-foreground));
}

/* Selected date - supports both data attribute and class for reactive binding */
.calendar-day[data-selected="true"],
.calendar-day.selected {
    background-color: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
}

.calendar-day[data-selected="true"]:hover,
.calendar-day.selected:hover {
    background-color: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
}

/* Outside current month */
.calendar-day[data-outside-month="true"] {
    color: hsl(var(--muted-foreground));
    opacity: 0.5;
}

/* Disabled dates */
.calendar-day[data-disabled="true"] {
    color: hsl(var(--muted-foreground));
    opacity: 0.3;
    cursor: not-allowed;
}

/* Navigation buttons */
.calendar-nav-button {
    padding: 0.25rem;
}

/* Popover styling for calendar - remove default popover padding */
[data-popover]:has(.calendar) {
    padding: 0;
    width: auto;
}
"""

app = FastAPI()
page = page_template(
    hdrs=(
        Link(rel='stylesheet', href='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.9/dist/basecoat.cdn.min.css'),
        Script(src='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.9/dist/js/all.min.js', defer=''),
        Style(CALENDAR_CSS),  # Include calendar-specific CSS
    ),
    datastar=True,
    lucide=True,
    tailwind4=True,
)

@app.get("/")
@page(title="DatePicker Examples",wrap_in=HTMLResponse)
def index():
    """DatePicker examples."""

    # Create signals for date selection
    sigs = Signals(
        appointment_date="2025-12-25",
        event_date="",
        start_date="2025-12-01",
        end_date="2025-12-31",
    )

    return Div(
            H1("DatePicker Component Examples", cls="text-3xl font-bold mb-8"),

            # Example 1: Basic DatePicker
            Card(
                CardHeader(
                    CardTitle("Basic DatePicker"),
                ),
                CardContent(
                    Field(
                        DatePicker(
                            bind=sigs.appointment_date,
                            placeholder="Select appointment date",
                        ),
                        label="Appointment Date",
                        description="Choose a date for your appointment",
                    ),
                    P("Selected date:", cls="mt-4 text-sm text-muted-foreground"),
                    Pre(
                        Code(
                            "",
                            **{"data-text": "$appointment_date || 'No date selected'"},
                            cls="text-sm",
                        ),
                        cls="mt-2 p-2 bg-muted rounded",
                    ),
                ),
                cls="mb-8",
            ),

            # Example 2: DatePicker with constraints
            Card(
                CardHeader(
                    CardTitle("DatePicker with Min/Max"),
                ),
                CardContent(
                    Field(
                        DatePicker(
                            bind=sigs.event_date,
                            placeholder="Select event date",
                            min_date="2025-01-01",
                            max_date="2025-12-31",
                            disabled_dates=["2025-07-04", "2025-12-25"],  # Holidays
                        ),
                        label="Event Date",
                        description="Only dates in 2025 are available (excluding holidays)",
                    ),
                    P("Selected date:", cls="mt-4 text-sm text-muted-foreground"),
                    Pre(
                        Code(
                            "",
                            **{"data-text": "$event_date || 'No date selected'"},
                            cls="text-sm",
                        ),
                        cls="mt-2 p-2 bg-muted rounded",
                    ),
                ),
                cls="mb-8",
            ),

            # Example 3: Date Range Picker
            Card(
                CardHeader(
                    CardTitle("Date Range Picker"),
                ),
                CardContent(
                    Field(
                        DateRangePicker(
                            bind_start=sigs.start_date,
                            bind_end=sigs.end_date,
                            placeholder="Select date range",
                        ),
                        label="Project Duration",
                        description="Select start and end dates for your project",
                    ),
                    Div(
                        P("Start date:", cls="text-sm text-muted-foreground"),
                        Pre(
                            Code(
                                "",
                                **{"data-text": "$start_date || 'No start date'"},
                                cls="text-sm",
                            ),
                            cls="p-2 bg-muted rounded",
                        ),
                        cls="mt-4",
                    ),
                    Div(
                        P("End date:", cls="text-sm text-muted-foreground"),
                        Pre(
                            Code(
                                "",
                                **{"data-text": "$end_date || 'No end date'"},
                                cls="text-sm",
                            ),
                            cls="p-2 bg-muted rounded",
                        ),
                        cls="mt-2",
                    ),
                ),
                cls="mb-8",
            ),

            # Example 4: Standalone Calendar
            Card(
                CardHeader(
                    CardTitle("Standalone Calendar"),
                ),
                CardContent(
                    Calendar(
                        bind=sigs.appointment_date,
                        value="2025-12-23",
                    ),
                    P("Selected from calendar:", cls="mt-4 text-sm text-muted-foreground"),
                    Pre(
                        Code(
                            "",
                            **{"data-text": "$appointment_date || 'No date selected'"},
                            cls="text-sm",
                        ),
                        cls="mt-2 p-2 bg-muted rounded",
                    ),
                ),
            ),

            signals=sigs,
            cls="container mx-auto max-w-4xl p-8",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
