---
title: Datastar Expressions
category: Frontend
order: 6
---

# Expressions

The `Expr` system is the foundation of Datastar's Python API, enabling you to build complex JavaScript expressions using Python syntax with operator overloading.

**Source:** `RustyTags/rusty_tags/datastar.py:118-310`

## Quick Start

```python
from rusty_tags.datastar import Signals

sigs = Signals(count=0, name="Alice", active=True)

# Python operators generate JavaScript
sigs.count + 10              # → "($count + 10)"
sigs.name.upper()            # → "$name.toUpperCase()"
sigs.active & (sigs.count > 0)  # → "($active && ($count > 0))"

# Use in components
Button(
    "Increment",
    on_click=sigs.count.add(1),  # → "$count++"
    disabled=sigs.count >= 10     # → data-attr:disabled="($count >= 10)"
)
```

## Expr Base Class

All Datastar expressions inherit from `Expr`:

```python
from abc import ABC, abstractmethod

class Expr(ABC):
    @abstractmethod
    def to_js(self) -> str:
        """Compile the expression to a JavaScript string."""
        pass

    def __str__(self) -> str:
        return self.to_js()
```

**Key types that are `Expr` instances:**
- `Signal` - Reactive state references
- `BinaryOp` - Binary operations (`+`, `-`, `==`, etc.)
- `UnaryOp` - Unary operations (`!`)
- `Conditional` - Ternary expressions
- `Assignment` - Value assignments
- `MethodCall` - Method calls
- `PropertyAccess` - Property access
- All expressions built from these

## Arithmetic Operators

### Addition (+)

```python
sigs = Signals(a=10, b=5, price=100)

# Number addition
sigs.a + sigs.b        # → "($a + $b)"
sigs.a + 10            # → "($a + 10)"
5 + sigs.a             # → "(5 + $a)"

# String concatenation (creates template literal)
sigs.name + " Smith"   # → TemplateLiteral
"Mr. " + sigs.name     # → TemplateLiteral

# Multiple additions
sigs.a + sigs.b + 10   # → "(($a + $b) + 10)"
```

### Subtraction (-)

```python
sigs.a - sigs.b        # → "($a - $b)"
sigs.a - 10            # → "($a - 10)"
100 - sigs.a           # → "(100 - $a)"
```

### Multiplication (*)

```python
sigs.price * sigs.quantity   # → "($price * $quantity)"
sigs.price * 1.5             # → "($price * 1.5)"
2 * sigs.price               # → "(2 * $price)"
```

### Division (/)

```python
sigs.total / sigs.count      # → "($total / $count)"
sigs.total / 2               # → "($total / 2)"
100 / sigs.divisor           # → "(100 / $divisor)"
```

### Modulo (%)

```python
sigs.count % 2         # → "($count % 2)"
sigs.value % 10        # → "($value % 10)"
100 % sigs.divisor     # → "(100 % $divisor)"
```

### Complex Arithmetic

```python
# Order of operations preserved
result = (sigs.a + sigs.b) * sigs.c
# → "(($a + $b) * $c)"

# Compute total with tax
subtotal = sigs.price * sigs.quantity
tax = subtotal * 0.08
total = subtotal + tax
# → Multiple chained expressions
```

## Comparison Operators

### Equality (==, !=)

```python
sigs = Signals(count=0, name="Alice", status="active")

# Equality
sigs.count == 0           # → "($count === 0)"
sigs.name == "Alice"      # → "($name === 'Alice')"
sigs.status == sigs.target_status  # → "($status === $target_status)"

# Inequality
sigs.count != 0           # → "($count !== 0)"
sigs.name != ""           # → "($name !== '')"
```

**Note:** Python `==` generates JavaScript `===` (strict equality)

### Relational (<, <=, >, >=)

```python
sigs = Signals(count=0, age=25, price=100)

# Less than
sigs.count < 10           # → "($count < 10)"
sigs.age < sigs.min_age   # → "($age < $min_age)"

# Less than or equal
sigs.count <= 10          # → "($count <= 10)"

# Greater than
sigs.price > 100          # → "($price > 100)"
sigs.age > 18             # → "($age > 18)"

# Greater than or equal
sigs.age >= 21            # → "($age >= 21)"
```

## Logical Operators

### AND (&)

```python
sigs = Signals(active=True, verified=False, count=0)

# Logical AND
sigs.active & sigs.verified
# → "($active && $verified)"

# With comparisons
(sigs.count > 0) & (sigs.count < 10)
# → "(($count > 0) && ($count < 10))"

# Multiple conditions
sigs.active & sigs.verified & (sigs.age >= 18)
# → "(($active && $verified) && ($age >= 18))"
```

**Note:** Use `&` for logical AND (not Python `and`)

### OR (|)

```python
# Logical OR
sigs.is_admin | sigs.is_moderator
# → "($is_admin || $is_moderator)"

# With comparisons
(sigs.status == "active") | (sigs.status == "pending")
# → "(($status === 'active') || ($status === 'pending'))"

# Multiple alternatives
sigs.is_admin | sigs.is_moderator | sigs.is_owner
# → "(($is_admin || $is_moderator) || $is_owner)"
```

**Note:** Use `|` for logical OR (not Python `or`)

### NOT (~)

```python
# Logical NOT
~sigs.active              # → "!($active)"
~(sigs.count > 0)         # → "!(($count > 0))"
~sigs.verified & sigs.active  # → "(!($verified) && $active)"
```

**Note:** Use `~` for logical NOT (not Python `not`)

### Complex Logical Expressions

```python
# Compound conditions
is_valid = (
    sigs.email.contains("@") &
    (sigs.password.length >= 8) &
    ~sigs.submitting
)
# → "(($email.includes('@') && ($password.length >= 8)) && !($submitting))"

# Button disabled condition
Button(
    "Submit",
    data_attr_disabled=(
        sigs.loading |
        (sigs.email == "") |
        ~sigs.terms_accepted
    )
)
```

## String Methods

### Case Conversion

```python
sigs = Signals(name="alice", code="ABC123")

# Lowercase
sigs.name.lower()         # → "$name.toLowerCase()"

# Uppercase
sigs.name.upper()         # → "$name.toUpperCase()"
sigs.code.upper()         # → "$code.toUpperCase()"

# Use in text
Span(data_text=sigs.name.upper())
```

### Whitespace

```python
sigs = Signals(text="  hello  ")

# Trim whitespace
sigs.text.strip()         # → "$text.trim()"

# Use in expressions
trimmed_empty = sigs.text.strip() == ""
```

### Contains

```python
sigs = Signals(email="alice@example.com", tags=["python", "web"])

# String contains
sigs.email.contains("@")       # → "$email.includes('@')"
sigs.email.contains("example") # → "$email.includes('example')"

# Use in conditions
Div(
    "Invalid email",
    data_show=~sigs.email.contains("@"),
    cls="text-red-500"
)
```

## Math Methods

### Round

```python
sigs = Signals(price=19.999, value=42.567)

# Round to integer
sigs.price.round()        # → "Math.round($price)"

# Round to decimals
sigs.price.round(2)       # → "Math.round($price * 100) / 100"
sigs.value.round(1)       # → "Math.round($value * 10) / 10"

# Display formatted price
Span(data_text=f"`$${sigs.price.round(2)}`")
# → <span data-text="`$${Math.round($price * 100) / 100}`">
```

### Absolute Value

```python
sigs = Signals(delta=-42, offset=-10)

sigs.delta.abs()          # → "Math.abs($delta)"
sigs.offset.abs()         # → "Math.abs($offset)"

# Distance calculation
distance = (sigs.x2 - sigs.x1).abs()
```

### Min/Max

```python
sigs = Signals(value=150, input=5)

# Minimum (clamp to lower bound)
sigs.value.min(100)       # → "Math.min($value, 100)"

# Maximum (clamp to upper bound)
sigs.value.max(0)         # → "Math.max($value, 0)"

# Ensure positive
positive = sigs.input.max(0)

# Ensure within range
capped = sigs.value.min(100)  # No more than 100
```

### Clamp

```python
sigs = Signals(slider=50, percentage=150)

# Clamp between min and max
sigs.slider.clamp(0, 100)
# → "Math.max(Math.min($slider, 100), 0)"

sigs.percentage.clamp(0, 100)
# → "Math.max(Math.min($percentage, 100), 0)"

# Use in input
Input(
    type="range",
    on_input=sigs.value.set(
        js("evt.target.value").clamp(0, 100)
    )
)
```

## Array Methods

### Append/Prepend

```python
sigs = Signals(items=[], todos=[])

# Append to end
sigs.items.append("new item")
# → "$items.push('new item')"

sigs.todos.append(sigs.new_todo)
# → "$todos.push($new_todo)"

# Prepend to beginning
sigs.items.prepend("first")
# → "$items.unshift('first')"

# Multiple items
sigs.items.append("a", "b", "c")
# → "$items.push('a', 'b', 'c')"
```

### Remove/Pop

```python
sigs = Signals(items=["a", "b", "c"])

# Remove last item
sigs.items.pop()
# → "$items.pop()"

# Remove by index
sigs.items.remove(1)
# → "$items.splice(1, 1)"

sigs.items.remove(sigs.selected_index)
# → "$items.splice($selected_index, 1)"
```

### Join

```python
sigs = Signals(tags=["python", "web", "framework"])

# Join with separator
sigs.tags.join(", ")
# → "$tags.join(', ')"

sigs.tags.join(" | ")
# → "$tags.join(' | ')"

# Display joined array
Span(data_text=sigs.tags.join(", "))
```

### Slice

```python
sigs = Signals(items=[1, 2, 3, 4, 5])

# Slice range
sigs.items.slice(0, 3)
# → "$items.slice(0, 3)"

sigs.items.slice(2)
# → "$items.slice(2)"

# First 5 items
first_five = sigs.items.slice(0, 5)
```

### Length

```python
sigs = Signals(items=[], todos=[])

# Array length
sigs.items.length
# → "$items.length"

# Use in conditions
Div(
    "No items",
    data_show=sigs.items.length == 0
)

# Count display
Span(data_text=f"`${sigs.todos.length} items`")
```

## Assignment Methods

### Set

```python
sigs = Signals(count=0, name="", active=False)

# Set value
sigs.count.set(0)         # → "$count = 0"
sigs.name.set("Alice")    # → "$name = 'Alice'"
sigs.active.set(True)     # → "$active = true"

# Set from event
Input(on_input=sigs.name.set(js("evt.target.value")))
# → data-on:input="$name = evt.target.value"

# Set from another signal
Button(on_click=sigs.target.set(sigs.source))
# → data-on:click="$target = $source"
```

### Add

```python
sigs = Signals(count=0, score=100)

# Add 1 (increment)
sigs.count.add(1)
# → "$count++"

# Add custom amount
sigs.count.add(5)
# → "$count = $count + 5"

sigs.score.add(sigs.bonus)
# → "$score = $score + $bonus"

# Use in click handler
Button("+", on_click=sigs.count.add(1))
Button("+5", on_click=sigs.count.add(5))
```

### Subtract

```python
sigs = Signals(count=10, lives=3)

# Subtract 1 (decrement)
sigs.count.sub(1)
# → "$count--"

# Subtract custom amount
sigs.count.sub(5)
# → "$count = $count - 5"

sigs.lives.sub(1)
# → "$lives--"

# Use in click handler
Button("-", on_click=sigs.count.sub(1))
```

### Multiply/Divide

```python
sigs = Signals(value=10, scale=2)

# Multiply
sigs.value.mul(2)
# → "$value = $value * 2"

sigs.value.mul(sigs.scale)
# → "$value = $value * $scale"

# Divide
sigs.value.div(2)
# → "$value = $value / 2"

# Halve
Button("Half", on_click=sigs.value.div(2))
```

### Modulo

```python
sigs = Signals(counter=0)

# Modulo operation
sigs.counter.mod(10)
# → "$counter = $counter % 10"

# Cycle through values 0-9
Button(
    "Next",
    on_click=[
        sigs.counter.add(1),
        sigs.counter.mod(10)
    ]
)
```

## Control Flow

### Ternary (if_)

```python
sigs = Signals(count=0, active=False, status="pending")

# Conditional value
sigs.count.if_("Many", "Few")
# → "($count ? 'Many' : 'Few')"

sigs.active.if_("Active", "Inactive")
# → "($active ? 'Active' : 'Inactive')"

# With comparison
(sigs.count > 10).if_("High", "Low")
# → "(($count > 10) ? 'High' : 'Low')"

# Complex condition
(sigs.status == "active").if_("✓ Active", "✗ Inactive")
# → "(($status === 'active') ? '✓ Active' : '✗ Inactive')"

# Use in display
Span(data_text=sigs.count.if_("Items available", "Out of stock"))

# Nested ternary
(sigs.count == 0).if_(
    "None",
    (sigs.count == 1).if_("One", "Many")
)
# → "(($count === 0) ? 'None' : (($count === 1) ? 'One' : 'Many'))"
```

### Then (conditional execution)

```python
sigs = Signals(count=0, reset_needed=False)

# Execute when condition is true
(sigs.count > 10).then(sigs.count.set(0))
# → "if (($count > 10)) { $count = 0 }"

# Multiple actions
(sigs.reset_needed).then([
    sigs.count.set(0),
    sigs.reset_needed.set(False)
])
# → "if ($reset_needed) { $count = 0; $reset_needed = false }"

# Use in event handlers
Button(
    "Increment",
    on_click=[
        sigs.count.add(1),
        (sigs.count >= 10).then(sigs.count.set(0))
    ]
)
```

### Toggle

```python
sigs = Signals(active=False, mode="light")

# Boolean toggle
sigs.active.toggle()
# → "$active = !$active"

# Value toggle (cycle between values)
sigs.mode.toggle("light", "dark")
# → "$mode = ($mode === 'light' ? 'dark' : 'light')"

# Multiple values (cycle)
sigs.size.toggle("small", "medium", "large")
# → Cycles: small → medium → large → small

# Use in buttons
Button("Toggle", on_click=sigs.active.toggle())
Button("Switch Theme", on_click=sigs.mode.toggle("light", "dark"))
```

## Property and Index Access

### Property Access

```python
sigs = Signals(
    user={"name": "Alice", "email": "alice@example.com"},
    config={"theme": "dark", "lang": "en"}
)

# Access object property
sigs.user.name
# → "$user.name"

sigs.config.theme
# → "$config.theme"

# Nested properties
sigs.user.address.city
# → "$user.address.city"

# Use in display
Span(data_text=sigs.user.name)
Span(data_text=sigs.config.theme)
```

### Index Access

```python
sigs = Signals(
    items=["a", "b", "c"],
    selected=0
)

# Array index
sigs.items[0]
# → "$items[0]"

sigs.items[sigs.selected]
# → "$items[$selected]"

# Object key
sigs.config["theme"]
# → "$config['theme']"

# Use in display
Span(data_text=sigs.items[sigs.selected])
```

### Method Calls on Properties

```python
sigs = Signals(user={"name": "alice"})

# Call method on property
sigs.user.name.upper()
# → "$user.name.toUpperCase()"

sigs.user.email.contains("@")
# → "$user.email.includes('@')"

# Chained calls
sigs.text.trim().upper()
# → "$text.trim().toUpperCase()"
```

## Complex Expressions

### Computed Properties

```python
sigs = Signals(
    items=[{"price": 10}, {"price": 20}, {"price": 30}],
    discount=0.1,
    tax_rate=0.08
)

# Complex calculation
subtotal = sigs.items[0].price + sigs.items[1].price + sigs.items[2].price
discount = subtotal * sigs.discount
taxable = subtotal - discount
tax = taxable * sigs.tax_rate
total = taxable + tax

# Use in display
Div(
    Span("Subtotal: ", data_text=subtotal.round(2)),
    Span("Discount: ", data_text=discount.round(2)),
    Span("Tax: ", data_text=tax.round(2)),
    Span("Total: ", data_text=total.round(2), cls="font-bold")
)
```

### Form Validation

```python
sigs = Signals(
    email="",
    password="",
    password_confirm=""
)

# Validation expressions
email_valid = sigs.email.contains("@") & (sigs.email.length >= 5)
password_valid = sigs.password.length >= 8
passwords_match = sigs.password == sigs.password_confirm
form_valid = email_valid & password_valid & passwords_match

# Use in UI
Input(
    type="email",
    data_class=classes(
        **{"border-red-500": ~email_valid & (sigs.email != "")}
    )
)

Button(
    "Submit",
    data_attr_disabled=~form_valid,
    type="submit"
)
```

### Conditional Classes

```python
sigs = Signals(
    count=0,
    loading=False,
    error=""
)

# Complex class conditions
Button(
    "Submit",
    cls="px-4 py-2 rounded",
    data_class=classes(
        **{
            "bg-blue-500": ~sigs.loading & (sigs.error == ""),
            "bg-gray-300": sigs.loading | (sigs.error != ""),
            "opacity-50": sigs.loading,
            "cursor-wait": sigs.loading,
            "cursor-not-allowed": (sigs.count == 0) & ~sigs.loading
        }
    )
)
```

### Template Literals

```python
sigs = Signals(count=0, name="Alice", price=19.99)

# String interpolation
Span(data_text=f"`Count: ${sigs.count}`")
# → <span data-text="`Count: ${$count}`">

Span(data_text=f"`Hello, ${sigs.name}!`")
# → <span data-text="`Hello, ${$name}!`">

# With formatting
Span(data_text=f"`Price: $${sigs.price.round(2)}`")
# → <span data-text="`Price: $${Math.round($price * 100) / 100}`">

# Multiple interpolations
Span(data_text=f"`${sigs.name} has ${sigs.count} items`")

# With expressions
Span(data_text=f"`${sigs.count.if_('Many', 'Few')} items remaining`")
```

## JavaScript Helpers

### js() - Raw JavaScript

```python
from rusty_tags.datastar import js

# Raw JavaScript code
js("console.log('Hello')")
# → "console.log('Hello')"

js("evt.target.value")
# → "evt.target.value"

js("window.scrollY")
# → "window.scrollY"

# Use in handlers
Input(on_input=sigs.search.set(js("evt.target.value")))
Div(on_scroll=sigs.scroll_pos.set(js("window.scrollY")))
```

### value() - Literal Values

```python
from rusty_tags.datastar import value

# Force literal encoding
value("text")     # → "'text'"
value(123)        # → "123"
value(True)       # → "true"
value([1, 2, 3])  # → "[1, 2, 3]"

# Useful when you need explicit control
sigs.items.append(value({"id": 1, "name": "Item"}))
```

### JavaScript Global Objects

```python
from rusty_tags.datastar import Math, console, JSON, Date

# Math operations
Math.random()           # → "Math.random()"
Math.floor(sigs.value)  # → "Math.floor($value)"

# Console logging
console.log(sigs.count) # → "console.log($count)"

# JSON operations
JSON.stringify(sigs.user)  # → "JSON.stringify($user)"

# Date operations
Date.now()              # → "Date.now()"
```

## Best Practices

### 1. Use Python Operators

```python
# Good - Pythonic
(sigs.count > 0) & sigs.active

# Bad - Manual strings
js("($count > 0) && $active")
```

### 2. Chain Methods Fluently

```python
# Good - readable chain
sigs.email.strip().lower().contains("@")

# Bad - nested
contains(lower(strip(sigs.email)), "@")
```

### 3. Break Complex Expressions

```python
# Good - intermediate variables
email_valid = sigs.email.contains("@")
password_valid = sigs.password.length >= 8
form_valid = email_valid & password_valid

# Bad - one giant expression
form_valid = (sigs.email.contains("@")) & ((sigs.password.length >= 8))
```

### 4. Use Computed Signals

```python
# Good - computed signal
from rusty_tags.datastar import Signal

total = Signal("total", sigs.price * sigs.quantity)

# Better than - recalculating inline
Span(data_text=sigs.price * sigs.quantity)  # Duplicated logic
```

## Common Patterns

### Validation Pattern

```python
sigs = Signals(email="", password="")

email_valid = sigs.email.contains("@") & (sigs.email.length >= 5)
password_valid = sigs.password.length >= 8

Input(
    type="email",
    on_input=sigs.email.set(js("evt.target.value")),
    data_class=classes(
        **{"border-red-500": ~email_valid & (sigs.email != "")}
    )
)
```

### Counter with Limits

```python
sigs = Signals(count=0)

Div(
    Button(
        "-",
        on_click=sigs.count.sub(1),
        data_attr_disabled=sigs.count <= 0
    ),
    Span(data_text=sigs.count),
    Button(
        "+",
        on_click=sigs.count.add(1),
        data_attr_disabled=sigs.count >= 10
    )
)
```

### Progress Bar

```python
sigs = Signals(completed=0, total=100)

percentage = (sigs.completed / sigs.total * 100).clamp(0, 100)

Div(
    Div(
        style=f"width: {percentage}%",
        cls="bg-blue-500 h-full"
    ),
    Span(data_text=f"`${percentage.round(0)}%`"),
    cls="w-full h-4 bg-gray-200"
)
```

### Search Filter

```python
sigs = Signals(search="", items=[])

# Client-side filtering would need custom JS
# But we can show/hide based on conditions
Input(
    placeholder="Search...",
    on_input__debounce__300=sigs.search.set(js("evt.target.value"))
)

# Clear button
Button(
    "Clear",
    on_click=sigs.search.set(""),
    data_show=sigs.search != ""
)
```

## Troubleshooting

### Operator Precedence

**Problem:** Expression not evaluating as expected

**Solution:** Use parentheses:

```python
# Wrong - unclear precedence
result = sigs.a + sigs.b * sigs.c

# Clear - explicit grouping
result = sigs.a + (sigs.b * sigs.c)
result = (sigs.a + sigs.b) * sigs.c
```

### Type Errors

**Problem:** `TypeError` when combining expressions

**Solution:** Ensure both sides are Expr objects:

```python
from rusty_tags.datastar import value

# Wrong - mixing types
sigs.items + "text"  # May fail

# Correct - both are expressions
sigs.items.join(", ")
```

### Logical Operators

**Problem:** Using Python `and`/`or`/`not` doesn't work

**Solution:** Use `&`/`|`/`~`:

```python
# Wrong - Python operators
if sigs.active and sigs.verified:  # Won't work in Datastar

# Correct - bitwise operators
sigs.active & sigs.verified
```

## Next Steps

- [Signals Documentation](signals.md) - Create Signal objects
- [Attributes Documentation](attributes.md) - Use expressions in attributes
- [Helpers Documentation](helpers.md) - Advanced expression helpers
- [Philosophy](philosophy.md) - Understand reactive principles
