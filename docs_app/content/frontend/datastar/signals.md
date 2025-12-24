# Signals

Signals are the foundation of Datastar's reactive state management. In Nitro, we provide Python classes that generate JavaScript signal references and manage reactive state.

**Source:** `RustyTags/rusty_tags/datastar.py:466-524` (Signal), `1294-1365` (Signals)

## Quick Start

```python
from rusty_tags import Div, Button, Span
from rusty_tags.datastar import Signals

# Create signals container
sigs = Signals(count=0, name="Alice")

# Use in components
counter = Div(
    Span(data_text=sigs.count),          # Access Signal object
    Button("+", on_click=sigs.count.add(1)),
    data_signals=sigs.to_dict()          # Initialize: {"count": 0, "name": "Alice"}
)
```

## Signal Class

The `Signal` class represents a single reactive value with type inference and JavaScript generation.

### Constructor

```python
class Signal(Expr):
    def __init__(
        self,
        name: str,                    # Signal name (e.g., "count")
        initial: Any = None,          # Initial value
        type_: type | None = None,    # Explicit type (auto-inferred if None)
        namespace: str | None = None, # Optional namespace prefix
        _ref_only: bool = False,      # Internal: reference only
    )
```

### Basic Usage

```python
from rusty_tags.datastar import Signal

# Create a signal
counter = Signal("count", 0)

# Use in expressions
counter.add(1)        # → "$count++"
counter > 10          # → "($count > 10)"
counter.to_js()       # → "$count"
```

### Type Inference

Signals automatically infer types from initial values:

```python
Signal("count", 0)              # type: int
Signal("name", "John")          # type: str
Signal("active", True)          # type: bool
Signal("items", [1, 2, 3])      # type: list
Signal("user", {"id": 1})       # type: dict
Signal("price", 19.99)          # type: float
Signal("value", None)           # type: str (default)
```

### Explicit Type

Override type inference when needed:

```python
# Initial value is int, but we want float
Signal("price", 0, type_=float)

# Initial value is None, but we want int
Signal("count", None, type_=int)
```

### Namespace Support

Organize signals into namespaces:

```python
# Without namespace
email = Signal("email", "")
email.to_js()  # → "$email"

# With namespace
email = Signal("email", "", namespace="form")
email.to_js()  # → "$form.email"
```

## Signals Container

The `Signals` class is a dictionary-like container that creates and manages multiple signals.

### Constructor

```python
class Signals(AttrDict):
    def __init__(self, namespace: str | None = None, **kwargs)
```

### Creating Signals

```python
from rusty_tags.datastar import Signals

# Basic signals
sigs = Signals(count=0, name="", active=True)

# With namespace
form_sigs = Signals(
    namespace="form",
    email="",
    password="",
    remember_me=False
)

# Complex initial values
sigs = Signals(
    user={"id": 1, "name": "Alice"},
    items=[],
    settings={"theme": "dark", "notifications": True}
)
```

### Accessing Signals

Signals can be accessed as attributes or dictionary items:

```python
sigs = Signals(count=0, name="Alice")

# Attribute access → Signal object (for expressions)
sigs.count              # → Signal("count", 0)
sigs.count.add(1)       # → "$count++"
sigs.name.upper()       # → "$name.toUpperCase()"

# Dictionary access → raw value
sigs["count"]           # → 0
sigs["name"]            # → "Alice"

# to_dict() → all raw values
sigs.to_dict()          # → {"count": 0, "name": "Alice"}
```

### Using in Components

```python
sigs = Signals(count=0, message="")

component = Div(
    # Display signal values
    Span(data_text=sigs.count),
    Span(data_text=sigs.message),

    # Modify signals
    Button("+", on_click=sigs.count.add(1)),
    Input(on_input=sigs.message.set(js("evt.target.value"))),

    # Initialize state
    data_signals=sigs.to_dict()  # REQUIRED!
)
```

**Important:** Always include `data_signals=sigs.to_dict()` on the root element to initialize state.

### Namespace Example

```python
# Create namespaced signals
form = Signals(namespace="form", email="", password="")
ui = Signals(namespace="ui", loading=False, error="")

# Signals are automatically namespaced
login_form = Form(
    Input(
        type="email",
        on_input=form.email.set(js("evt.target.value"))  # → "$form.email = evt.target.value"
    ),
    Input(
        type="password",
        on_input=form.password.set(js("evt.target.value"))  # → "$form.password = evt.target.value"
    ),

    Button(
        "Login",
        disabled=ui.loading,  # → data-attr:disabled="$ui.loading"
        on_click=ui.loading.set(True)
    ),

    Div(
        data_text=ui.error,
        data_show=ui.error != "",
        cls="text-red-500"
    ),

    # Initialize both namespaces
    data_signals={**form.to_dict(), **ui.to_dict()}
    # → {form: {email: '', password: ''}, ui: {loading: false, error: ''}}
)
```

## Computed Signals

Signals can have computed initial values using expressions:

```python
from rusty_tags.datastar import Signals, Signal

sigs = Signals(price=100, quantity=1)

# Computed signal - recalculates automatically
total = Signal("total", sigs.price * sigs.quantity)

# Generates: data-computed:total="$price * $quantity"
component = Div(
    Input(
        type="number",
        value=sigs.quantity,
        on_input=sigs.quantity.set(js("evt.target.value"))
    ),
    Span("Total: ", data_text=total),  # Updates automatically!

    data_signals=sigs.to_dict(),
    **dict([total.get_computed_attr()])  # Add computed attribute
)
```

### How Computed Signals Work

```python
# Regular signal - static initial value
regular = Signal("count", 0)
regular.to_dict()              # → {"count": 0}
regular.get_computed_attr()    # → None

# Computed signal - expression as initial value
computed = Signal("total", sigs.price * sigs.quantity)
computed.to_dict()             # → {} (not in data-signals)
computed.get_computed_attr()   # → ("data_computed_total", Expr(...))
```

**Computed signals:**
- Are NOT included in `data_signals` (no initial value)
- Generate `data-computed:name` attributes instead
- Automatically recalculate when dependencies change

### Complex Computed Example

```python
sigs = Signals(
    price=100,
    quantity=1,
    discount_rate=0.1,
    tax_rate=0.08
)

# Computed values
subtotal = Signal("subtotal", sigs.price * sigs.quantity)
discount = Signal("discount", subtotal * sigs.discount_rate)
taxable = Signal("taxable", subtotal - discount)
tax = Signal("tax", taxable * sigs.tax_rate)
total = Signal("total", taxable + tax)

checkout = Div(
    Div("Subtotal: ", Span(data_text=subtotal)),
    Div("Discount: ", Span(data_text=discount)),
    Div("Tax: ", Span(data_text=tax)),
    Div("Total: ", Span(data_text=total), cls="font-bold"),

    data_signals=sigs.to_dict(),
    # Add all computed attributes
    **dict([
        subtotal.get_computed_attr(),
        discount.get_computed_attr(),
        taxable.get_computed_attr(),
        tax.get_computed_attr(),
        total.get_computed_attr(),
    ])
)
```

## Entity Signals

Nitro entities have a `.signals` property that creates a Signals container from entity fields:

```python
from nitro import Entity, Field

class Todo(Entity, table=True):
    title: str
    completed: bool = False
    priority: int = 1

# Create entity instance
todo = Todo(id="1", title="Buy milk", completed=False, priority=2)

# Get signals from entity
sigs = todo.signals

# Equivalent to:
# Signals(id="1", title="Buy milk", completed=False, priority=2)

# Use in templates
todo_item = Div(
    Input(
        type="checkbox",
        checked=sigs.completed,
        on_click=sigs.completed.toggle()
    ),
    Span(data_text=sigs.title),
    Span(data_text=f"`Priority: ${sigs.priority}`"),

    data_signals=sigs.to_dict()
)
```

### Entity List Example

```python
todos = Todo.all()

todo_list = Div(
    *[
        Div(
            # Each todo has its own signals
            todo_item_component(todo.signals),
            data_signals=todo.signals.to_dict(),
            id=f"todo-{todo.id}"
        )
        for todo in todos
    ]
)
```

## Operator Overloading

Signals inherit from `Expr`, so they support all operator overloading:

```python
sigs = Signals(count=0, name="Alice", active=True)

# Arithmetic
sigs.count + 10           # → "($count + 10)"
sigs.count * 2            # → "($count * 2)"

# Comparison
sigs.count > 0            # → "($count > 0)"
sigs.name == "Alice"      # → "($name === 'Alice')"

# Logical
sigs.active & (sigs.count > 0)   # → "($active && ($count > 0))"
~sigs.active              # → "!($active)"

# String methods
sigs.name.upper()         # → "$name.toUpperCase()"
sigs.name.contains("ice") # → "$name.includes('ice')"

# Math methods
sigs.count.round()        # → "Math.round($count)"
sigs.count.clamp(0, 100)  # → "Math.max(Math.min($count, 100), 0)"

# Assignment
sigs.count.set(0)         # → "$count = 0"
sigs.count.add(1)         # → "$count++"
sigs.active.toggle()      # → "$active = !$active"
```

See [Expressions Documentation](expressions.md) for complete operator reference.

## Advanced Patterns

### Conditional Initialization

```python
# Initialize based on entity state
user = current_user()

sigs = Signals(
    username=user.username if user else "",
    is_admin=user.is_admin if user else False,
    theme=user.settings.get("theme", "light") if user else "light"
)
```

### Signal References

Create references to signals from other components:

```python
# Main signals
main_sigs = Signals(count=0)

# Reference in child component (don't initialize again)
child_count = Signal("count", 0, _ref_only=True)

child = Div(
    Span(data_text=child_count),  # References $count from parent
    # NO data_signals here - uses parent's
)

parent = Div(
    child,
    Button("+", on_click=main_sigs.count.add(1)),
    data_signals=main_sigs.to_dict()  # Initialize once at parent
)
```

### Dynamic Signal Names

```python
# Create signals dynamically
signal_names = ["email", "password", "remember_me"]
signal_values = {"email": "", "password": "", "remember_me": False}

sigs = Signals(**signal_values)

# Or with namespace
form_sigs = Signals(namespace="form", **signal_values)
```

### Merging Signal Containers

```python
# Multiple signal containers
user_sigs = Signals(username="", email="")
ui_sigs = Signals(loading=False, error="")

# Merge for data_signals
component = Div(
    # ... UI elements

    data_signals={**user_sigs.to_dict(), **ui_sigs.to_dict()}
)

# Or with namespaces (cleaner)
user_sigs = Signals(namespace="user", username="", email="")
ui_sigs = Signals(namespace="ui", loading=False, error="")

component = Div(
    # Access: $user.username, $ui.loading
    data_signals={**user_sigs.to_dict(), **ui_sigs.to_dict()}
)
```

## Common Patterns

### Toggle Pattern

```python
sigs = Signals(menu_open=False, dark_mode=False)

menu_button = Button(
    "Menu",
    on_click=sigs.menu_open.toggle()
)

theme_toggle = Button(
    "Toggle Theme",
    on_click=sigs.dark_mode.toggle()
)
```

### Counter Pattern

```python
sigs = Signals(count=0)

counter = Div(
    Button("-", on_click=sigs.count.sub(1)),
    Span(data_text=sigs.count),
    Button("+", on_click=sigs.count.add(1)),
    data_signals=sigs.to_dict()
)
```

### Form State Pattern

```python
sigs = Signals(
    email="",
    password="",
    remember_me=False,
    submitting=False,
    error=""
)

form = Form(
    Input(
        type="email",
        on_input=sigs.email.set(js("evt.target.value"))
    ),
    Input(
        type="password",
        on_input=sigs.password.set(js("evt.target.value"))
    ),
    Input(
        type="checkbox",
        on_change=sigs.remember_me.toggle()
    ),

    Button(
        "Login",
        disabled=sigs.submitting,
        type="submit"
    ),

    Div(
        data_text=sigs.error,
        data_show=sigs.error != "",
        cls="text-red-500"
    ),

    on_submit__prevent=[
        sigs.submitting.set(True),
        sigs.error.set(""),
        post("/api/login")
    ],

    data_signals=sigs.to_dict()
)
```

### List Management Pattern

```python
sigs = Signals(
    items=["Apple", "Banana", "Cherry"],
    new_item=""
)

list_manager = Div(
    Input(
        placeholder="Add item",
        on_input=sigs.new_item.set(js("evt.target.value"))
    ),
    Button(
        "Add",
        on_click=[
            sigs.items.append(sigs.new_item),
            sigs.new_item.set("")
        ]
    ),

    Div(
        # Display items (would need SSE for reactive list updates)
        id="items-list"
    ),

    data_signals=sigs.to_dict()
)
```

## Best Practices

### 1. Initialize at Root

Always initialize signals at the root of your component tree:

```python
# Good
parent = Div(
    child1,
    child2,
    data_signals=sigs.to_dict()  # Initialize once at root
)

# Bad - multiple initializations
parent = Div(
    child1,
    Div(
        child2,
        data_signals=sigs.to_dict()  # Don't reinitialize!
    ),
    data_signals=sigs.to_dict()
)
```

### 2. Use Namespaces for Complex UIs

Organize related signals with namespaces:

```python
# Good - organized
form = Signals(namespace="form", email="", password="")
ui = Signals(namespace="ui", loading=False, error="")
user = Signals(namespace="user", id="", name="")

# Bad - flat namespace collisions
sigs = Signals(
    form_email="",
    form_password="",
    ui_loading=False,
    ui_error="",
    user_id="",
    user_name=""
)
```

### 3. Type Hints for Clarity

Use type hints when creating signals dynamically:

```python
from typing import TypedDict

class FormSignals(TypedDict):
    email: str
    password: str
    remember_me: bool

form_data: FormSignals = {
    "email": "",
    "password": "",
    "remember_me": False
}

sigs = Signals(**form_data)
```

### 4. Minimal State

Only include reactive values in signals:

```python
# Bad - static values in signals
sigs = Signals(
    user_id=123,        # Never changes
    api_url="/api",     # Constant
    theme="dark"        # Changes - should be signal
)

# Good - only reactive state
sigs = Signals(theme="dark")
USER_ID = 123
API_URL = "/api"
```

## Troubleshooting

### Signal Not Updating

**Problem:** Signal changes but UI doesn't update

**Solution:** Check that `data_signals` is initialized:

```python
# Missing initialization
Div(
    Span(data_text=sigs.count),
    # data_signals missing!
)

# Fixed
Div(
    Span(data_text=sigs.count),
    data_signals=sigs.to_dict()  # Required!
)
```

### Namespace Not Working

**Problem:** Getting `$email` instead of `$form.email`

**Solution:** Pass `namespace` to Signals constructor:

```python
# Wrong
sigs = Signals(email="")
sigs.email.to_js()  # → "$email"

# Correct
sigs = Signals(namespace="form", email="")
sigs.email.to_js()  # → "$form.email"
```

### Computed Signal Not Computing

**Problem:** Computed signal shows initial value only

**Solution:** Use `get_computed_attr()` to generate the attribute:

```python
total = Signal("total", sigs.price * sigs.quantity)

# Missing computed attribute
Div(
    Span(data_text=total),
    data_signals=sigs.to_dict()
)

# Fixed
Div(
    Span(data_text=total),
    data_signals=sigs.to_dict(),
    **dict([total.get_computed_attr()])  # Add this!
)
```

## Next Steps

- [Expressions Documentation](expressions.md) - Learn all Signal operators
- [Attributes Documentation](attributes.md) - Use signals in data-* attributes
- [SSE Integration](sse-integration.md) - Update signals from server
- [Philosophy](philosophy.md) - Understand reactive principles
