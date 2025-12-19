"""Combobox component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi import APIRouter
from fastapi.requests import Request
from nitro.infrastructure.events import on, emit_elements

from nitro.infrastructure.html.components import (
    Combobox,
    ComboboxItem,
    ComboboxGroup,
    ComboboxSeparator,
    LucideIcon,
)
from rusty_tags.datastar import Signals

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Combobox(
            ComboboxItem("React", value="react"),
            ComboboxItem("Vue", value="vue"),
            ComboboxItem("Svelte", value="svelte"),
            ComboboxItem("Angular", value="angular"),
            ComboboxItem("Solid", value="solid"),
            id="framework-basic",
            placeholder="Select a framework...",
        ),
        cls="w-full max-w-sm",
    )


def example_with_binding():
    form = Signals(fruit="")
    return Div(
        Combobox(
            ComboboxItem("Apple", value="apple"),
            ComboboxItem("Banana", value="banana"),
            ComboboxItem("Orange", value="orange"),
            ComboboxItem("Strawberry", value="strawberry"),
            ComboboxItem("Mango", value="mango"),
            ComboboxItem("Grape", value="grape"),
            id="fruit-binding",
            placeholder="Select a fruit...",
            bind=form.fruit,
        ),
        P(
            "Selected value: ",
            Span(
                data_text="$fruit || 'None'",
                cls="font-semibold",
            ),
            cls="mt-4 text-sm text-muted-foreground",
        ),
        signals=form,
        cls="w-full max-w-sm",
    )


def example_with_groups():
    return Div(
        Combobox(
            ComboboxGroup(
                ComboboxItem("Apple", value="apple"),
                ComboboxItem("Banana", value="banana"),
                ComboboxItem("Orange", value="orange"),
                label="Fruits"
            ),
            ComboboxSeparator(),
            ComboboxGroup(
                ComboboxItem("Carrot", value="carrot"),
                ComboboxItem("Broccoli", value="broccoli"),
                ComboboxItem("Spinach", value="spinach"),
                label="Vegetables"
            ),
            id="food-groups",
            placeholder="Select a food...",
        ),
        cls="w-full max-w-sm",
    )


def example_with_icons():
    return Div(
        Combobox(
            ComboboxItem(LucideIcon("palette"), "Light", value="light"),
            ComboboxItem(LucideIcon("moon"), "Dark", value="dark"),
            ComboboxItem(LucideIcon("laptop"), "System", value="system"),
            id="theme-icons",
            placeholder="Select a theme...",
        ),
        cls="w-full max-w-sm",
    )


def example_disabled_items():
    return Div(
        Combobox(
            ComboboxItem("Available option", value="option1"),
            ComboboxItem("Another available option", value="option2"),
            ComboboxItem("Disabled option", value="option3", disabled=True),
            ComboboxItem("Also disabled", value="option4", disabled=True),
            ComboboxItem("Yet another available option", value="option5"),
            id="disabled-options",
            placeholder="Select an option...",
        ),
        cls="w-full max-w-sm",
    )


def example_long_list():
    # List of countries
    countries = [
        "Argentina", "Australia", "Austria", "Belgium", "Brazil",
        "Canada", "China", "Denmark", "Egypt", "Finland",
        "France", "Germany", "Greece", "India", "Indonesia",
        "Ireland", "Italy", "Japan", "Mexico", "Netherlands",
        "New Zealand", "Norway", "Poland", "Portugal", "Russia",
        "South Africa", "South Korea", "Spain", "Sweden", "Switzerland",
        "Thailand", "Turkey", "United Kingdom", "United States", "Vietnam",
    ]
    return Div(
        Combobox(
            *[ComboboxItem(country, value=country.lower().replace(" ", "-")) for country in countries],
            id="country-list",
            placeholder="Search countries...",
            empty_text="No countries found",
        ),
        cls="w-full max-w-sm",
    )


page = Div(
        H1("Combobox Component"),
        P(
            "A searchable dropdown that combines an input field with a filterable list "
            "of options. Uses Datastar signals for state management and real-time filtering. "
            "Built on Basecoat's .select CSS for consistent styling."
        ),
        TitledSection(
            "Design Philosophy",
            P("Combobox follows these principles:"),
            Ul(
                Li("Compound component pattern - Combobox, ComboboxItem, ComboboxGroup work together"),
                Li("Datastar-powered filtering - client-side search without page reload"),
                Li("Basecoat CSS - uses existing .select styles for consistency"),
                Li("ARIA attributes - role='combobox', role='listbox', role='option' for accessibility"),
                Li("Keyboard navigation - Escape to close, click outside to close"),
            ),
        ),
        TitledSection(
            "Basic Usage",
            P("A simple combobox with a list of options:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "With Datastar Binding",
            P("Bind the selected value to a Datastar signal for reactive updates:"),
            ComponentShowcase(example_with_binding),
        ),
        TitledSection(
            "With Groups",
            P("Organize options into groups with labels:"),
            ComponentShowcase(example_with_groups),
        ),
        TitledSection(
            "With Icons",
            P("Items can include icons for visual distinction:"),
            ComponentShowcase(example_with_icons),
        ),
        TitledSection(
            "Disabled Items",
            P("Some options can be disabled while others remain interactive:"),
            ComponentShowcase(example_disabled_items),
        ),
        TitledSection(
            "Long List with Search",
            P("The combobox excels at searching through long lists. Try typing to filter:"),
            ComponentShowcase(example_long_list),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
# Combobox - Container with search and dropdown
def Combobox(
    *children,                   # ComboboxItem elements
    id: str = "",                # Unique identifier (auto-generated if not provided)
    placeholder: str = "Search...",  # Placeholder for search input
    empty_text: str = "No results found",  # Text when no matches
    bind: Any = None,            # Datastar Signal for two-way binding
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString

# ComboboxItem - Individual selectable option (closure pattern)
def ComboboxItem(
    *children,                   # Item content (text, icons, etc.)
    value: str,                  # The value when selected
    search_text: str = None,     # Custom text for filtering (defaults to first text child)
    disabled: bool = False,      # Whether item is disabled
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> Callable

# ComboboxGroup - Group of items with label (closure pattern)
def ComboboxGroup(
    *children,                   # ComboboxItem elements
    label: str,                  # Group heading text
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> Callable

# ComboboxSeparator - Visual divider between groups
def ComboboxSeparator(
    cls: str = "",               # Additional CSS classes
    **attrs                      # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Key Behaviors",
            Ul(
                Li("Click trigger button to open dropdown"),
                Li("Type in search input to filter options"),
                Li("Click an option to select it"),
                Li("Click outside or press Escape to close"),
                Li("Selected option shows checkmark indicator"),
                Li("Empty state shows custom message when no results"),
            ),
        ),
        TitledSection(
            "Accessibility",
            Ul(
                Li("role='combobox' on trigger and search input"),
                Li("role='listbox' on options container"),
                Li("role='option' on each item"),
                Li("aria-expanded indicates open state"),
                Li("aria-selected indicates selected option"),
                Li("aria-disabled for disabled options"),
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/combobox")
@template(title="Combobox Component Documentation")
def combobox_page():
    return page

@on("page.combobox")
async def get_combobox(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.combobox")