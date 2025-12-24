---
title: Datastar Attributes
category: Frontend
order: 5
---

# Datastar Attributes

Datastar uses special `data-*` attributes to bind reactive behavior to HTML elements. Nitro provides Pythonic keyword arguments that generate these attributes automatically.

**Source:** `RustyTags/rusty_tags/datastar.py:833-935`

## Quick Start

```python
from rusty_tags import Div, Button, Input, Span
from rusty_tags.datastar import Signals

sigs = Signals(count=0, name="", show=False)

component = Div(
    # Text content
    Span(data_text=sigs.count),

    # Event handler
    Button("+", on_click=sigs.count.add(1)),

    # Input binding
    Input(on_input=sigs.name.set(js("evt.target.value"))),

    # Conditional display
    Div("Hidden content", data_show=sigs.show),

    # Initialize state
    data_signals=sigs.to_dict()
)
```

## Naming Convention

Python uses underscores (`_`), Datastar v1.0+ uses colons (`:`):

```python
# Python                    # HTML output
data_signals={}         →   data-signals="{}"
data_on_click=""        →   data-on:click=""
data_attr_class=""      →   data-attr:class=""
data_computed_total=""  →   data-computed:total=""
data_text=""            →   data-text=""
data_show=""            →   data-show=""
```

Nitro handles this conversion automatically.

## Core Attributes

### data_signals

**Purpose:** Initialize reactive state on an element

**Syntax:** `data_signals=dict` or `data_signals=sigs.to_dict()`

```python
# Dictionary syntax
Div(
    data_signals={"count": 0, "name": "Alice"}
)
# → <div data-signals="{count: 0, name: 'Alice'}">

# Signals object syntax (recommended)
sigs = Signals(count=0, name="Alice")
Div(
    data_signals=sigs.to_dict()
)
```

**With namespaces:**

```python
form = Signals(namespace="form", email="", password="")
ui = Signals(namespace="ui", loading=False)

Div(
    data_signals={**form.to_dict(), **ui.to_dict()}
)
# → <div data-signals="{form: {email: '', password: ''}, ui: {loading: false}}">
```

**Best practice:** Place on the root element of your component:

```python
# Good
Div(
    child1,
    child2,
    data_signals=sigs.to_dict()  # Root element
)

# Bad - multiple initializations
Div(
    Div(child1, data_signals=sigs.to_dict()),
    Div(child2, data_signals=sigs.to_dict())
)
```

### data_text

**Purpose:** Bind text content to a signal or expression

**Syntax:** `data_text=signal_or_expression`

```python
sigs = Signals(count=0, name="Alice")

# Simple signal
Span(data_text=sigs.count)
# → <span data-text="$count">

# String signal
Span(data_text=sigs.name)
# → <span data-text="$name">

# Expression
Span(data_text=sigs.count * 2)
# → <span data-text="($count * 2)">

# Template literal
Span(data_text=f"`Count: ${sigs.count}`")
# → <span data-text="`Count: ${$count}`">

# Conditional
Span(data_text=sigs.count.if_("Many", "Few"))
# → <span data-text="($count ? 'Many' : 'Few')">
```

**Common patterns:**

```python
# Display formatted numbers
Span(data_text=f"`$${sigs.price.round(2)}`")

# Conditional text
Span(data_text=(sigs.count > 0).if_("Items available", "Out of stock"))

# Uppercase transformation
Span(data_text=sigs.name.upper())
```

### data_on_*

**Purpose:** Attach event handlers to elements

**Syntax:** `data_on_<event>=action` or `on_<event>=action` (shorthand)

**Common events:**

```python
# Click events
Button("Click me", on_click=sigs.count.add(1))
# → <button data-on:click="$count++">

# Input events
Input(on_input=sigs.search.set(js("evt.target.value")))
# → <input data-on:input="$search = evt.target.value">

# Submit events
Form(on_submit__prevent=post("/api/submit"))
# → <form data-on:submit.prevent="@post('/api/submit')">

# Change events
Input(type="checkbox", on_change=sigs.active.toggle())
# → <input type="checkbox" data-on:change="$active = !$active">

# Focus events
Input(
    on_focus=sigs.focused.set(True),
    on_blur=sigs.focused.set(False)
)

# Mouse events
Div(
    on_mouseenter=sigs.hover.set(True),
    on_mouseleave=sigs.hover.set(False)
)

# Keyboard events
Input(on_keyup=sigs.key_pressed.set(js("evt.key")))
```

**Multiple actions:**

```python
# List of actions (executed in sequence)
Button(
    "Submit",
    on_click=[
        sigs.loading.set(True),
        sigs.error.set(""),
        post("/api/submit")
    ]
)
# → data-on:click="$loading = true; $error = ''; @post('/api/submit')"
```

### Event Modifiers

**Syntax:** `on_<event>__<modifier>=action`

**Available modifiers:**

#### prevent
Calls `event.preventDefault()`:

```python
# Prevent form submission
Form(on_submit__prevent=post("/api/login"))
# → data-on:submit.prevent="@post('/api/login')"

# Prevent link navigation
A("Click", href="#", on_click__prevent=sigs.modal.set(True))
```

#### stop
Calls `event.stopPropagation()`:

```python
# Stop event bubbling
Button(on_click__stop=sigs.count.add(1))
# → data-on:click.stop="$count++"
```

#### debounce
Debounce event handler by milliseconds:

```python
# Debounce search by 300ms
Input(
    placeholder="Search...",
    on_input__debounce__300=sigs.search.set(js("evt.target.value"))
)
# → data-on:input.debounce.300ms="$search = evt.target.value"
```

#### throttle
Throttle event handler by milliseconds:

```python
# Throttle scroll events by 100ms
Div(
    on_scroll__throttle__100=sigs.scroll_pos.set(js("window.scrollY"))
)
# → data-on:scroll.throttle.100ms="$scroll_pos = window.scrollY"
```

#### Multiple modifiers

Combine modifiers with double underscores:

```python
# Prevent default + debounce
Input(
    on_input__prevent__debounce__500=sigs.query.set(js("evt.target.value"))
)
# → data-on:input.prevent.debounce.500ms="$query = evt.target.value"

# Stop propagation + prevent default
Form(
    on_submit__prevent__stop=post("/api/submit")
)
# → data-on:submit.prevent.stop="@post('/api/submit')"
```

### data_attr_*

**Purpose:** Bind element attributes to signals or expressions

**Syntax:** `data_attr_<attribute>=signal_or_expression`

```python
sigs = Signals(url="/home", disabled=False, title="Click me")

# Bind href
A(data_attr_href=sigs.url)
# → <a data-attr:href="$url">

# Bind disabled
Button(data_attr_disabled=sigs.disabled)
# → <button data-attr:disabled="$disabled">

# Bind title
Span(data_attr_title=sigs.title)
# → <span data-attr:title="$title">

# Dynamic URL
A(data_attr_href=f"`/users/${sigs.user_id}`")
# → <a data-attr:href="`/users/${$user_id}`">
```

**Common patterns:**

```python
# Dynamic image src
Img(data_attr_src=f"`/images/${sigs.image_name}.jpg`")

# Conditional disabled
Button(data_attr_disabled=sigs.loading | (sigs.count == 0))

# Dynamic placeholder
Input(data_attr_placeholder=(sigs.mode == "search").if_("Search...", "Enter text..."))

# Bind value (for controlled inputs)
Input(data_attr_value=sigs.name)
```

### data_show

**Purpose:** Conditionally show/hide elements (with display: none)

**Syntax:** `data_show=boolean_expression`

```python
sigs = Signals(loading=False, error="", count=0)

# Simple boolean
Div("Loading...", data_show=sigs.loading)
# → <div data-show="$loading">

# Inverted
Div("Content", data_show=~sigs.loading)
# → <div data-show="!($loading)">

# Comparison
Div("No items", data_show=sigs.count == 0)
# → <div data-show="($count === 0)">

# String not empty
Div(data_text=sigs.error, data_show=sigs.error != "")
# → <div data-text="$error" data-show="($error !== '')">

# Complex condition
Div(
    "Warning",
    data_show=(sigs.count > 10) & ~sigs.dismissed
)
# → <div data-show="(($count > 10) && !($dismissed))">
```

**Common patterns:**

```python
# Loading spinner
Div(
    Spinner(),
    data_show=sigs.loading
)

# Error message
Div(
    data_text=sigs.error,
    data_show=sigs.error != "",
    cls="text-red-500"
)

# Empty state
Div(
    "No items found",
    data_show=sigs.items.length == 0
)

# Success message
Div(
    "Saved!",
    data_show=sigs.saved,
    cls="text-green-500"
)
```

### data_class

**Purpose:** Conditionally apply CSS classes

**Syntax:** `data_class=object_literal` or `data_class=classes(**conditions)`

```python
from rusty_tags.datastar import classes

sigs = Signals(active=False, loading=False, error="")

# Object literal syntax (JavaScript style)
Div(data_class="{'active': $active, 'loading': $loading}")
# → <div data-class="{'active': $active, 'loading': $loading}">

# Helper function (Python style - recommended)
Div(data_class=classes(active=sigs.active, loading=sigs.loading))
# → <div data-class="{active: $active, loading: $loading}">

# Classes with hyphens
Div(data_class=classes(
    **{"font-bold": sigs.active, "text-red-500": sigs.error != ""}
))
# → <div data-class="{'font-bold': $active, 'text-red-500': ($error !== '')}">
```

**Common patterns:**

```python
# Active tab
Button(
    "Home",
    cls="tab",  # Static classes
    data_class=classes(active=sigs.active_tab == "home")
)

# Loading state
Button(
    "Submit",
    data_class=classes(
        opacity_50=sigs.loading,
        cursor_wait=sigs.loading
    )
)

# Error styling
Input(
    data_class=classes(
        **{"border-red-500": sigs.error != "", "border-gray-300": sigs.error == ""}
    )
)

# Multiple conditions
Div(
    data_class=classes(
        hidden=~sigs.visible,
        **{"bg-blue-500": sigs.active, "bg-gray-200": ~sigs.active},
        **{"text-white": sigs.active, "text-black": ~sigs.active}
    )
)
```

**Combining static and reactive classes:**

```python
# Static classes in cls, reactive in data_class
Button(
    "Click me",
    cls="px-4 py-2 rounded",  # Always applied
    data_class=classes(
        **{"bg-blue-500": ~sigs.disabled, "bg-gray-300": sigs.disabled}
    )
)
```

### data_computed_*

**Purpose:** Define computed values that update automatically

**Syntax:** `data_computed_<name>=expression`

```python
sigs = Signals(price=100, quantity=1, tax_rate=0.08)

# Computed values
Div(
    data_computed_subtotal=sigs.price * sigs.quantity,
    data_computed_tax=js("$subtotal * $tax_rate"),
    data_computed_total=js("$subtotal + $tax"),

    data_signals=sigs.to_dict()
)
# → <div
#      data-computed:subtotal="$price * $quantity"
#      data-computed:tax="$subtotal * $tax_rate"
#      data-computed:total="$subtotal + $tax"
#    >
```

**Using Signal class for computed:**

```python
from rusty_tags.datastar import Signal

sigs = Signals(price=100, quantity=1)

# Create computed signal
total = Signal("total", sigs.price * sigs.quantity)

# Add to component
Div(
    Span("Total: ", data_text=total),
    data_signals=sigs.to_dict(),
    **dict([total.get_computed_attr()])  # Generates data_computed_total
)
```

**Chained computations:**

```python
sigs = Signals(celsius=0)

converter = Div(
    Input(
        type="number",
        value=sigs.celsius,
        on_input=sigs.celsius.set(js("evt.target.value"))
    ),

    # Compute Fahrenheit from Celsius
    data_computed_fahrenheit=js("($celsius * 9/5) + 32"),

    Span(data_text=js("`${$celsius}°C = ${$fahrenheit.toFixed(1)}°F`")),

    data_signals=sigs.to_dict()
)
```

### data_ref

**Purpose:** Create a reference to an element for JavaScript access

**Syntax:** `data_ref="name"`

```python
# Create reference
email_input = Input(
    type="email",
    data_ref="emailInput"
)
# → <input type="email" data-ref="emailInput">

# Access from JavaScript (in event handlers)
Button(
    "Focus Email",
    on_click=js("document.querySelector('[data-ref=\"emailInput\"]').focus()")
)
```

**Common use cases:**

```python
# Auto-focus on load
Input(
    data_ref="searchInput",
    # Can be referenced in other handlers
)

# Scroll into view
Div(
    id="section",
    data_ref="targetSection"
)

Button(
    "Scroll to Section",
    on_click=js("document.querySelector('[data-ref=\"targetSection\"]').scrollIntoView()")
)
```

## Advanced Patterns

### Form with Validation

```python
sigs = Signals(
    email="",
    password="",
    password_confirm="",
    submitting=False,
    error=""
)

# Computed validation
passwords_match = Signal(
    "passwords_match",
    sigs.password == sigs.password_confirm
)

form = Form(
    Input(
        type="email",
        placeholder="Email",
        on_input=sigs.email.set(js("evt.target.value")),
        data_class=classes(
            **{"border-red-500": (sigs.email != "") & ~sigs.email.contains("@")}
        )
    ),

    Input(
        type="password",
        placeholder="Password",
        on_input=sigs.password.set(js("evt.target.value"))
    ),

    Input(
        type="password",
        placeholder="Confirm Password",
        on_input=sigs.password_confirm.set(js("evt.target.value")),
        data_class=classes(
            **{"border-red-500": (sigs.password_confirm != "") & ~passwords_match}
        )
    ),

    Div(
        "Passwords must match",
        cls="text-red-500 text-sm",
        data_show=(sigs.password_confirm != "") & ~passwords_match
    ),

    Button(
        "Sign Up",
        type="submit",
        data_attr_disabled=sigs.submitting | ~passwords_match,
        data_class=classes(
            **{"opacity-50": sigs.submitting | ~passwords_match}
        )
    ),

    Div(
        data_text=sigs.error,
        data_show=sigs.error != "",
        cls="text-red-500 mt-2"
    ),

    on_submit__prevent=[
        sigs.submitting.set(True),
        sigs.error.set(""),
        post("/api/signup")
    ],

    data_signals=sigs.to_dict(),
    **dict([passwords_match.get_computed_attr()])
)
```

### Tab Component

```python
sigs = Signals(active_tab="home")

tabs = Div(
    # Tab buttons
    Div(
        Button(
            "Home",
            on_click=sigs.active_tab.set("home"),
            cls="px-4 py-2",
            data_class=classes(
                **{"bg-blue-500 text-white": sigs.active_tab == "home"},
                **{"bg-gray-200": sigs.active_tab != "home"}
            )
        ),
        Button(
            "Profile",
            on_click=sigs.active_tab.set("profile"),
            cls="px-4 py-2",
            data_class=classes(
                **{"bg-blue-500 text-white": sigs.active_tab == "profile"},
                **{"bg-gray-200": sigs.active_tab != "profile"}
            )
        ),
        Button(
            "Settings",
            on_click=sigs.active_tab.set("settings"),
            cls="px-4 py-2",
            data_class=classes(
                **{"bg-blue-500 text-white": sigs.active_tab == "settings"},
                **{"bg-gray-200": sigs.active_tab != "settings"}
            )
        ),
        cls="flex gap-2"
    ),

    # Tab content
    Div(
        Div("Home content...", data_show=sigs.active_tab == "home"),
        Div("Profile content...", data_show=sigs.active_tab == "profile"),
        Div("Settings content...", data_show=sigs.active_tab == "settings"),
        cls="mt-4 p-4 border"
    ),

    data_signals=sigs.to_dict()
)
```

### Modal Component

```python
sigs = Signals(modal_open=False, modal_title="", modal_content="")

def open_modal(title, content):
    return [
        sigs.modal_title.set(title),
        sigs.modal_content.set(content),
        sigs.modal_open.set(True)
    ]

modal = Div(
    # Backdrop
    Div(
        on_click=sigs.modal_open.set(False),
        cls="fixed inset-0 bg-black bg-opacity-50",
        data_show=sigs.modal_open
    ),

    # Modal
    Div(
        Div(
            H2(data_text=sigs.modal_title),
            Button(
                "×",
                on_click=sigs.modal_open.set(False),
                cls="absolute top-2 right-2"
            ),
            cls="flex justify-between items-center mb-4"
        ),
        Div(data_text=sigs.modal_content),
        cls="fixed inset-1/4 bg-white p-6 rounded shadow-lg",
        data_show=sigs.modal_open
    ),

    data_signals=sigs.to_dict()
)

# Trigger modal
trigger = Button(
    "Open Modal",
    on_click=open_modal("Hello", "This is modal content")
)
```

### Search with Debounce

```python
sigs = Signals(search="", results=[], loading=False)

search_box = Div(
    Input(
        type="search",
        placeholder="Search...",
        on_input__debounce__300=[
            sigs.search.set(js("evt.target.value")),
            sigs.loading.set(True),
            get(f"/api/search?q={sigs.search}")
        ]
    ),

    Div(
        Spinner(),
        data_show=sigs.loading
    ),

    Div(
        id="search-results",
        data_show=~sigs.loading
    ),

    data_signals=sigs.to_dict()
)
```

## Best Practices

### 1. Use Shorthand Event Handlers

```python
# Good - shorthand
Button(on_click=sigs.count.add(1))

# Verbose - full attribute name
Button(data_on_click=sigs.count.add(1))
```

### 2. Combine Static and Reactive Classes

```python
# Good - clear separation
Button(
    "Click",
    cls="px-4 py-2 rounded",  # Static
    data_class=classes(       # Reactive
        **{"bg-blue-500": sigs.active, "bg-gray-300": ~sigs.active}
    )
)

# Bad - mixing in data_class
Button(
    data_class=classes(
        px_4=True,  # Should be static
        py_2=True,  # Should be static
        **{"bg-blue-500": sigs.active}
    )
)
```

### 3. Use Helper Functions

```python
from rusty_tags.datastar import classes

# Good - readable
data_class=classes(active=sigs.active, hidden=sigs.hidden)

# Bad - manual object literal
data_class="{'active': $active, 'hidden': $hidden}"
```

### 4. Debounce Expensive Operations

```python
# Good - debounced search
Input(
    on_input__debounce__300=get("/api/search")
)

# Bad - fires on every keystroke
Input(
    on_input=get("/api/search")
)
```

## Troubleshooting

### Attribute Not Working

**Problem:** Datastar attribute has no effect

**Solution:** Check initialization:

```python
# Missing data_signals
Div(
    Span(data_text=sigs.count),  # Won't work!
)

# Fixed
Div(
    Span(data_text=sigs.count),
    data_signals=sigs.to_dict()  # Required!
)
```

### Classes Not Toggling

**Problem:** `data_class` not applying classes

**Solution:** Use proper object syntax:

```python
# Wrong - string value
data_class="active"

# Correct - object with condition
data_class=classes(active=sigs.active)
```

### Event Handler Not Firing

**Problem:** Click handler doesn't work

**Solution:** Check expression syntax:

```python
# Wrong - Python boolean
on_click=sigs.active == True  # Will generate "($active === true)"

# Correct - use signal method
on_click=sigs.active.toggle()

# Or set directly
on_click=sigs.active.set(True)
```

## Next Steps

- [Expressions Documentation](expressions.md) - Build complex expressions
- [Signals Documentation](signals.md) - Master signal management
- [SSE Integration](sse-integration.md) - Server-sent updates
- [Helpers Documentation](helpers.md) - Advanced helper functions
