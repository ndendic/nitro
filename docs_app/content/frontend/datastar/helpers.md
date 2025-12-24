# Datastar Helpers

This document covers the comprehensive suite of helper functions in Nitro's Datastar integration. These helpers generate JavaScript expressions from Python code, making it easy to build reactive UIs without writing raw JavaScript.

**Source:** `RustyTags/rusty_tags/datastar.py` (lines 568-815, 958-1275)

---

## Overview

Datastar helpers fall into several categories:

1. **General Purpose** - `js()`, `value()`, `f()`, `regex()`
2. **Conditional Logic** - `match()`, `switch()`, `collect()`, `classes()`
3. **Logical Aggregation** - `all_()`, `any_()`
4. **Action Helpers** - `post()`, `get()`, `put()`, `patch()`, `delete()`
5. **Utility Helpers** - `clipboard()`, timeout functions, `seq()`
6. **DS Class** - Alternative imperative API

All helpers return JavaScript expressions as strings or `_JSRaw` objects that integrate seamlessly with Datastar attributes.

---

## General Purpose Helpers

### js() - Raw JavaScript

Mark a string as raw JavaScript code that should not be escaped or quoted.

```python
from rusty_tags.datastar import js

# Raw JS expressions
js("console.log('hello')")
js("window.scrollTo(0, 0)")
js("evt.target.value")
js("document.getElementById('myId')")

# As callable (generates function calls)
js("myFunction")(sigs.value, "arg2")
# → myFunction($value, 'arg2')

js("Math.max")(sigs.a, sigs.b, 10)
# → Math.max($a, $b, 10)
```

**Use cases:**
- Accessing browser APIs
- Calling JavaScript libraries
- Working with DOM APIs
- Event object properties

---

### value() / expr() - Python to JavaScript Literals

Convert Python values to JavaScript literals safely.

```python
from rusty_tags.datastar import value, expr

# Primitives
value([1, 2, 3])           # [1, 2, 3]
value({"a": 1, "b": 2})    # {'a': 1, 'b': 2}
value("hello")             # 'hello'
value(True)                # true
value(None)                # null

# Complex structures
value({
    "items": [1, 2, 3],
    "nested": {"key": "val"}
})
# → {'items': [1, 2, 3], 'nested': {'key': 'val'}}
```

**Note:** `expr()` is an alias for `value()` with identical behavior.

**Common mistake:**
```python
# ❌ Don't wrap Signal objects
value(sigs.count)  # TypeError!

# ✅ Use Signal objects directly
sigs.count  # Correct
```

---

### f() - Template Strings

Create JavaScript template literals (backtick strings) with Python f-string syntax.

```python
from rusty_tags.datastar import f

# Basic interpolation
f("Hello, {name}!", name=sigs.name)
# → `Hello, ${$name}!`

# Multiple variables
f("Item {id}: {title}", id=sigs.id, title=sigs.title)
# → `Item ${$id}: ${$title}`

# With expressions
f("Total: ${amount} USD", amount=sigs.price.mul(sigs.quantity))
# → `Total: ${$price * $quantity} USD`

# Complex templates
f("User {user} has {count} {item}",
  user=sigs.username,
  count=sigs.items.length,
  item="items")
# → `User ${$username} has ${$items.length} items`
```

**Usage in attributes:**
```python
Div(data_text=f("Score: {score}/100", score=sigs.score))
Button("Submit",
       data_on_click=f("submitForm('{id}')", id=sigs.form_id))
```

---

### regex() - JavaScript Regular Expressions

Create JavaScript regex literals.

```python
from rusty_tags.datastar import regex

regex("^todo_")        # /^todo_/
regex("[a-z]+")        # /[a-z]+/
regex("\\d{3}-\\d{4}") # /\d{3}-\d{4}/

# Use with match() or JavaScript methods
Input(data_validate=regex("^[A-Z][a-z]+$"))
```

---

## Conditional Logic Helpers

### match() - Pattern Matching

Like Python's `match`/`case` but for JavaScript ternary chains.

```python
from rusty_tags.datastar import match

# Basic pattern matching
match(sigs.status,
    pending="Waiting...",
    processing="Working...",
    done="Complete!",
    default="Unknown"
)
# → $status === 'pending' ? 'Waiting...' :
#   ($status === 'processing' ? 'Working...' :
#   ($status === 'done' ? 'Complete!' : 'Unknown'))

# With expressions as values
match(sigs.level,
    easy=sigs.base_score,
    medium=sigs.base_score.mul(2),
    hard=sigs.base_score.mul(3),
    default=0
)

# In attributes
Div(data_text=match(sigs.status,
    active="🟢 Active",
    inactive="🔴 Inactive",
    pending="🟡 Pending",
    default="⚪ Unknown"
))
```

---

### switch() - Sequential Conditions

If/elif/else chain - first true condition wins.

```python
from rusty_tags.datastar import switch

# Grade calculator
switch([
    (sigs.score >= 90, "A"),
    (sigs.score >= 80, "B"),
    (sigs.score >= 70, "C"),
    (sigs.score >= 60, "D"),
], default="F")
# → $score >= 90 ? 'A' : ($score >= 80 ? 'B' : ...)

# Priority-based messages
switch([
    (sigs.error, "Error occurred!"),
    (sigs.warning, "Warning"),
    (sigs.info, "Information"),
], default="")

# Usage
Div(data_text=switch([
    (sigs.items.length.eq(0), "No items"),
    (sigs.items.length.eq(1), "1 item"),
], default=f("{count} items", count=sigs.items.length)))
```

---

### collect() - Filter and Join

Collect values from true conditions - perfect for building CSS class strings.

```python
from rusty_tags.datastar import collect

# CSS classes based on state
collect([
    (sigs.is_active, "active"),
    (sigs.is_large, "text-lg"),
    (sigs.is_bold, "font-bold"),
])
# → ['active', 'text-lg', 'font-bold'].filter(Boolean).join(' ')

# Custom separator
collect([
    (sigs.first_name, sigs.first_name),
    (sigs.last_name, sigs.last_name),
], join_with=", ")
# → Full name with comma separator

# Usage in attributes
Button("Click",
    cls=collect([
        (True, "btn"),
        (sigs.is_primary, "btn-primary"),
        (sigs.is_disabled, "btn-disabled"),
    ])
)
```

---

### classes() - Dynamic Class Objects

Generate JavaScript object literals for Datastar's `data-class` attribute.

```python
from rusty_tags.datastar import classes

# Basic usage
classes(
    active=sigs.is_active,
    hidden=sigs.is_hidden,
    large=sigs.is_large
)
# → {active: $is_active, hidden: $is_hidden, large: $is_large}

# With hyphenated class names
classes(**{
    "font-bold": sigs.is_bold,
    "text-red-500": sigs.has_error,
    "bg-green-100": sigs.is_success
})
# → {'font-bold': $is_bold, 'text-red-500': $has_error, ...}

# Usage with data-class
Div("Content",
    data_class=classes(
        active=sigs.is_active,
        loading=sigs.is_loading,
        **{"text-lg": sigs.large_text}
    )
)
```

**How it works:**
```html
<!-- When $is_active is true, 'active' class is applied -->
<div data-class="{active: $is_active, hidden: $is_hidden}">
```

---

### seq() - Comma Operator Sequence

Evaluate multiple expressions in sequence, return the last value.

```python
from rusty_tags.datastar import seq

# Execute multiple actions
seq(sigs.count.add(1), sigs.updated.set(True))
# → ($count++, $updated = true)

# With side effects
seq(
    sigs.loading.set(True),
    sigs.error.set(None),
    sigs.fetch_data()
)

# Usage
Button("Submit",
    data_on_click=seq(
        sigs.submitted.set(True),
        sigs.validate(),
        sigs.send()
    )
)
```

---

### if_() - Ternary Conditional

Simple ternary operator helper.

```python
from rusty_tags.datastar import if_

# Basic conditional
if_(sigs.is_logged_in, "Welcome!", "Please login")
# → $is_logged_in ? 'Welcome!' : 'Please login'

# With expressions
if_(sigs.count.gt(0), sigs.count, "None")
# → $count > 0 ? $count : 'None'

# Usage
Span(data_text=if_(sigs.loading, "Loading...", "Ready"))
```

---

## Logical Aggregation Helpers

### all_() - Check All Truthy

Returns true if all arguments are truthy (AND logic).

```python
from rusty_tags.datastar import all_

# Basic usage
all_(sigs.a, sigs.b, sigs.c)
# → !!$a && !!$b && !!$c

# With list
all_([sigs.name, sigs.email, sigs.password])
# → !!$name && !!$email && !!$password

# Form validation
Button("Submit",
    data_disabled=all_(sigs.name, sigs.email).not_()
)
# Disabled unless both name and email are filled
```

---

### any_() - Check Any Truthy

Returns true if any argument is truthy (OR logic).

```python
from rusty_tags.datastar import any_

# Basic usage
any_(sigs.a, sigs.b, sigs.c)
# → !!$a || !!$b || !!$c

# With list
any_([sigs.error, sigs.warning])
# → !!$error || !!$warning

# Show alert if any message exists
Div("Alert!",
    data_show=any_(sigs.error, sigs.warning, sigs.info)
)
```

---

## Action Helpers

These helpers generate Datastar action expressions for HTTP requests.

### get() - GET Request

```python
from rusty_tags.datastar import get

# Simple GET
get("/api/data")
# → @get('/api/data')

# With query parameters
get("/api/users", page=1, limit=10)
# → @get('/api/users', {page: 1, limit: 10})

# With signal values
get("/api/user", id=sigs.user_id)
# → @get('/api/user', {id: $user_id})

# Usage
Button("Load Data", data_on_click=get("/api/todos"))
Div(data_on_load=get("/api/profile", id=sigs.current_user))
```

---

### post() - POST Request

```python
from rusty_tags.datastar import post

# Simple POST
post("/api/submit")
# → @post('/api/submit')

# With data
post("/api/users", name=sigs.name, email=sigs.email)
# → @post('/api/users', {name: $name, email: $email})

# With data dict
post("/api/create", data={"type": "todo", "priority": "high"})
# → @post('/api/create', {type: 'todo', priority: 'high'})

# Mix static and dynamic data
post("/api/update",
     id=sigs.todo_id,
     completed=sigs.is_done,
     updated_at=js("new Date().toISOString()")
)

# Usage
Button("Save",
    data_on_click=post("/api/todos",
        text=sigs.todo_text,
        priority=sigs.priority
    )
)
```

---

### put() - PUT Request

```python
from rusty_tags.datastar import put

# Update resource
put("/api/users/123", name="New Name", active=True)
# → @put('/api/users/123', {name: 'New Name', active: true})

# With signals
put("/api/profile", data={
    "bio": sigs.bio,
    "avatar": sigs.avatar_url
})

# Usage
Button("Update Profile",
    data_on_click=put(f"/api/users/{sigs.user_id}",
        name=sigs.name,
        email=sigs.email
    )
)
```

---

### patch() - PATCH Request

```python
from rusty_tags.datastar import patch

# Partial update
patch("/api/todos/5", completed=True)
# → @patch('/api/todos/5', {completed: true})

# Usage
Checkbox(
    data_on_change=patch(
        f"/api/todos/{sigs.id}",
        completed=sigs.completed
    )
)
```

---

### delete() - DELETE Request

```python
from rusty_tags.datastar import delete

# Simple delete
delete("/api/todos/5")
# → @delete('/api/todos/5')

# With confirmation
Button("Delete",
    data_on_click=if_(
        js("confirm('Are you sure?')"),
        delete(f"/api/todos/{sigs.id}"),
        ""
    )
)

# Usage
Button("Remove",
    data_on_click=delete(f"/api/items/{sigs.item_id}")
)
```

---

## Utility Helpers

### clipboard() - Copy to Clipboard

Copy text or element content to the clipboard.

```python
from rusty_tags.datastar import clipboard

# Copy static text
clipboard(text="Hello, world!")
# → @clipboard('Hello, world!')

# Copy from element
clipboard(element="#code-block")
# → @clipboard(document.getElementById('code-block').textContent)

# Copy with selector
clipboard(element=".output")
# → @clipboard(document.querySelector('.output').textContent)

# With feedback signal
clipboard(text="Copied!", signal="copied_status")
# Updates $copied_status after copy

# Usage examples
Button("Copy Code",
    data_on_click=clipboard(element="#code-example")
)

Button("Copy Link",
    data_on_click=seq(
        clipboard(text=sigs.share_url),
        sigs.copied.set(True)
    )
)
```

---

### set_timeout() - Schedule Delayed Actions

Execute actions after a delay.

```python
from rusty_tags.datastar import set_timeout

# Basic timeout
set_timeout(sigs.show.set(False), 3000)
# Hide after 3 seconds

# Multiple actions
set_timeout([
    sigs.step.set(2),
    sigs.loading.set(False)
], 1000)

# Store timer reference
set_timeout(
    sigs.loading.set(False),
    2000,
    store=sigs.timer
)
# Saves timer ID in $timer for later cancellation

# Usage - auto-hide notification
Div("Saved!",
    id="notification",
    data_on_load=set_timeout(
        sigs.notification_visible.set(False),
        5000
    )
)
```

---

### clear_timeout() - Cancel Timeout

Cancel a previously scheduled timeout.

```python
from rusty_tags.datastar import clear_timeout

# Simple clear
clear_timeout(sigs.timer)
# → clearTimeout($timer)

# Clear and run actions
clear_timeout(sigs.timer,
    sigs.open.set(False),
    sigs.loading.set(False)
)
# → clearTimeout($timer); $open = false; $loading = false

# Usage - cancel auto-hide on hover
Div("Notification",
    data_on_mouseenter=clear_timeout(sigs.hide_timer),
    data_on_mouseleave=set_timeout(
        sigs.visible.set(False),
        3000,
        store=sigs.hide_timer
    )
)
```

---

### reset_timeout() - Debounce Pattern

Clear existing timeout and schedule new one (perfect for debouncing).

```python
from rusty_tags.datastar import reset_timeout

# Debounced search
reset_timeout(sigs.search_timer, 500, sigs.perform_search())
# → clearTimeout($search_timer);
#   $search_timer = setTimeout(() => $perform_search(), 500)

# Debounced input
Input(
    data_on_input=reset_timeout(
        sigs.debounce_timer,
        700,
        sigs.validate_input()
    )
)

# Multiple actions with debounce
reset_timeout(sigs.timer, 300,
    sigs.loading.set(True),
    sigs.fetch_results()
)
```

**Common debounce pattern:**
```python
# Search input with 300ms debounce
Input(
    type="text",
    placeholder="Search...",
    data_model="search_query",
    data_on_input=reset_timeout(
        sigs.search_timer,
        300,
        get("/api/search", q=sigs.search_query)
    )
)
```

---

## DS Class - Alternative API

The `DS` class provides an alternative, more imperative API for common operations.

### HTTP Actions

```python
from rusty_tags.datastar import DS

# GET request
DS.get("/api/data")
# → @get('/api/data')

DS.get("/api/users", page=1)
# → @get('/api/users?page=1')

# POST request
DS.post("/api/submit", data={"name": "John"})
# → @post('/api/submit', {'name': 'John'})

# Other verbs
DS.put("/api/update", data={"status": "active"})
DS.patch("/api/partial", data={"field": "value"})
DS.delete("/api/remove")
```

---

### Signal Manipulation

```python
from rusty_tags.datastar import DS

# Set signal value
DS.set("count", 0)
# → $count = 0

DS.set("name", "Alice")
# → $name = 'Alice'

DS.set("items", [1, 2, 3])
# → $items = [1, 2, 3]

# Toggle boolean
DS.toggle("active")
# → $active = !$active

# Increment/decrement
DS.increment("count", 5)
# → $count += 5

DS.decrement("count", 1)
# → $count -= 1

# Array operations
DS.append("items", "new item")
# → $items.push('new item')

DS.remove("items", index=2)
# → $items.splice(2, 1)

DS.remove("items", value="old item")
# → $items.splice($items.indexOf('old item'), 1)
```

---

### Control Flow

```python
from rusty_tags.datastar import DS

# Chain multiple actions
DS.chain(
    DS.set("loading", True),
    DS.get("/api/data"),
    DS.set("loading", False)
)
# → $loading = true; @get('/api/data'); $loading = false

# Conditional execution
DS.conditional(
    "$count > 10",
    DS.set("large", True),
    DS.set("large", False)
)
# → $count > 10 ? ($large = true) : ($large = false)
```

---

### Usage Examples

```python
from rusty_tags import Button, Input, Div
from rusty_tags.datastar import DS

# Counter with DS
Button("Increment",
    data_on_click=DS.increment("count", 1)
)

# Form submission
Button("Submit",
    data_on_click=DS.chain(
        DS.set("submitting", True),
        DS.post("/api/form", data={"name": "$name"}),
        DS.set("submitting", False)
    )
)

# Toggle visibility
Button("Toggle",
    data_on_click=DS.toggle("visible")
)

# Conditional action
Button("Save",
    data_on_click=DS.conditional(
        "$is_valid",
        DS.post("/api/save"),
        DS.set("error", "Invalid data")
    )
)
```

---

## Practical Patterns

### Pattern 1: Debounced Search

```python
from rusty_tags import Input, Div
from rusty_tags.datastar import reset_timeout, get, Signals

sigs = Signals(
    search_query="",
    search_timer=0,
    results=[]
)

search_input = Input(
    type="text",
    placeholder="Search...",
    data_model="search_query",
    data_on_input=reset_timeout(
        sigs.search_timer,
        500,
        get("/api/search", q=sigs.search_query)
    )
)
```

### Pattern 2: Auto-Hide Notification

```python
from rusty_tags import Div
from rusty_tags.datastar import set_timeout, Signals

sigs = Signals(notification_visible=True)

notification = Div("Saved successfully!",
    data_show=sigs.notification_visible,
    data_on_load=set_timeout(
        sigs.notification_visible.set(False),
        3000
    ),
    cls="notification"
)
```

### Pattern 3: Conditional CSS Classes

```python
from rusty_tags import Button
from rusty_tags.datastar import classes, collect, Signals

sigs = Signals(
    is_active=False,
    is_loading=False,
    has_error=False
)

# Using classes()
button = Button("Action",
    data_class=classes(
        active=sigs.is_active,
        loading=sigs.is_loading,
        **{"text-red-500": sigs.has_error}
    )
)

# Using collect()
button2 = Button("Action",
    cls=collect([
        (True, "btn"),
        (sigs.is_active, "btn-active"),
        (sigs.is_loading, "btn-loading"),
    ])
)
```

### Pattern 4: Form Validation

```python
from rusty_tags import Form, Input, Button
from rusty_tags.datastar import all_, post, Signals

sigs = Signals(
    name="",
    email="",
    password=""
)

form = Form(
    Input(type="text", data_model="name", placeholder="Name"),
    Input(type="email", data_model="email", placeholder="Email"),
    Input(type="password", data_model="password", placeholder="Password"),

    Button("Submit",
        data_disabled=all_(sigs.name, sigs.email, sigs.password).not_(),
        data_on_click=post("/api/register",
            name=sigs.name,
            email=sigs.email,
            password=sigs.password
        )
    )
)
```

### Pattern 5: Multi-Step Wizard

```python
from rusty_tags import Div, Button
from rusty_tags.datastar import match, Signals

sigs = Signals(step=1)

wizard = Div(
    # Step indicator
    Div(data_text=f("Step {step} of 3", step=sigs.step)),

    # Step content (conditional rendering)
    Div(data_show=sigs.step.eq(1), "Step 1 content"),
    Div(data_show=sigs.step.eq(2), "Step 2 content"),
    Div(data_show=sigs.step.eq(3), "Step 3 content"),

    # Navigation
    Button("Previous",
        data_show=sigs.step.gt(1),
        data_on_click=sigs.step.sub(1)
    ),
    Button("Next",
        data_show=sigs.step.lt(3),
        data_on_click=sigs.step.add(1)
    ),
    Button("Finish",
        data_show=sigs.step.eq(3),
        data_on_click=post("/api/submit")
    )
)
```

### Pattern 6: Copy with Feedback

```python
from rusty_tags import Button, Span
from rusty_tags.datastar import clipboard, seq, set_timeout, Signals

sigs = Signals(copied=False)

copy_button = Button(
    Span(data_show=sigs.copied.not_(), "Copy"),
    Span(data_show=sigs.copied, "✓ Copied!"),
    data_on_click=seq(
        clipboard(element="#code-block"),
        sigs.copied.set(True),
        set_timeout(sigs.copied.set(False), 2000)
    )
)
```

---

## Performance Considerations

### 1. Avoid Over-Reactive Bindings

```python
# ❌ Triggers on every keystroke
Input(data_on_input=post("/api/save", text=sigs.text))

# ✅ Debounced
Input(data_on_input=reset_timeout(sigs.timer, 500,
    post("/api/save", text=sigs.text)
))
```

### 2. Use collect() Wisely

```python
# ✅ Good - few conditions
collect([
    (sigs.active, "active"),
    (sigs.large, "text-lg")
])

# ⚠️ Consider data-class for many conditions
classes(
    active=sigs.active,
    large=sigs.large,
    bold=sigs.bold,
    # ... many more
)
```

### 3. Prefer Signal Operations Over JS

```python
# ❌ Avoid raw JS when possible
data_on_click=js("$count = $count + 1")

# ✅ Use signal methods
data_on_click=sigs.count.add(1)
```

---

## Related Documentation

- [Datastar Signals](/frontend/datastar/signals) - Signal operations and methods
- [Datastar Attributes](/frontend/datastar/attributes) - DOM binding reference
- [Datastar Expressions](/frontend/datastar/expressions) - Expression syntax
- [SSE Integration](/frontend/datastar/sse-integration) - Server-sent events

---

## Reference

**Source:** `RustyTags/rusty_tags/datastar.py`

**Key Functions:**
- `js()`, `value()`, `f()`, `regex()` - General purpose
- `match()`, `switch()`, `collect()`, `classes()` - Conditionals
- `all_()`, `any_()` - Logic
- `get()`, `post()`, `put()`, `patch()`, `delete()` - HTTP
- `clipboard()` - Clipboard API
- `set_timeout()`, `clear_timeout()`, `reset_timeout()` - Timers
- `seq()`, `if_()` - Control flow

**DS Class Methods:**
- HTTP: `get()`, `post()`, `put()`, `patch()`, `delete()`
- Signals: `set()`, `toggle()`, `increment()`, `decrement()`, `append()`, `remove()`
- Control: `chain()`, `conditional()`
