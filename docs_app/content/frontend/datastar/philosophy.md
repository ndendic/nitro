# Datastar Philosophy

Datastar is a reactive JavaScript library that brings signal-based state management to HTML. In Nitro, we provide a powerful Python API that generates Datastar-compatible JavaScript, allowing you to write reactive frontends using Python syntax.

## Core Principles

### 1. Signals as Reactive State

Datastar uses **signals** - reactive values that automatically update the UI when they change. Unlike React's virtual DOM diffing or manual DOM manipulation, signals provide direct reactive updates:

```python
from rusty_tags import Div, Button, Span
from rusty_tags.datastar import Signals

# Create reactive state
sigs = Signals(count=0)

# UI updates automatically when signals change
counter = Div(
    Span(data_text=sigs.count),           # Display updates reactively
    Button("+", on_click=sigs.count.add(1)),  # Increment on click
    Button("-", on_click=sigs.count.sub(1)),  # Decrement on click
    data_signals=sigs.to_dict()           # Initialize state
)
```

When the user clicks the "+" button, `$count` increments and the `Span` automatically updates - no manual DOM manipulation required.

### 2. Server-Side First

Datastar is designed for **server-side rendering (SSR)** with progressive enhancement:

1. **Initial render**: Server generates complete HTML
2. **Hydration**: Datastar adds reactivity to existing HTML
3. **Updates**: Server sends HTML fragments via SSE (Server-Sent Events)

```python
from fastapi import FastAPI
from rusty_tags import Page, Div, H1
from rusty_tags.datastar import Signals

app = FastAPI()

@app.get("/")
def index():
    sigs = Signals(counter=0)

    # Server renders complete HTML
    return Page(
        H1("Counter Demo"),
        Div(
            # ... interactive counter UI
            data_signals=sigs.to_dict()
        ),
        title="Counter App",
        datastar=True  # Include Datastar CDN
    )
```

This approach combines the benefits of SSR (fast initial load, SEO-friendly) with the interactivity of client-side frameworks.

### 3. HTML as the Source of Truth

State lives in **HTML attributes**, not separate JavaScript files:

```python
# State stored in data-signals attribute
Div(
    data_signals={"count": 0, "name": ""}  # <div data-signals="{count: 0, name: ''}">
)

# Expressions in data-* attributes
Span(data_text="$count")                    # <span data-text="$count">
Button(on_click=sigs.count.add(1))          # <button data-on:click="$count++">
```

No build step required - Datastar reads expressions directly from HTML attributes and evaluates them at runtime.

### 4. Progressive Enhancement

Datastar follows progressive enhancement principles:

- **Works without JavaScript**: Basic functionality via server-side rendering
- **Enhanced with Datastar**: Adds interactivity when JavaScript is available
- **Graceful degradation**: Falls back to server round-trips if needed

```python
# This form works with or without JavaScript
Form(
    Input(name="email", type="email", required=True),
    Button("Submit", type="submit"),

    # Enhanced with Datastar for instant feedback
    on_submit__prevent=post("/api/subscribe", email=sigs.email),
    data_signals=sigs.to_dict()
)
```

## When to Use Datastar

### Perfect Use Cases

#### 1. Real-Time Updates
Dashboards, notifications, live data feeds:

```python
from rusty_tags.datastar import Signals

sigs = Signals(notifications=[], unread_count=0)

# SSE endpoint pushes updates
notifications_panel = Div(
    Span("Notifications: ", data_text=sigs.unread_count),
    Div(id="notifications-list"),
    data_signals=sigs.to_dict()
)
```

#### 2. Form Interactions
Validation, conditional fields, dynamic forms:

```python
sigs = Signals(
    password="",
    confirm_password="",
    passwords_match=False
)

password_form = Div(
    Input(
        type="password",
        placeholder="Password",
        on_input=sigs.password.set(js("evt.target.value"))
    ),
    Input(
        type="password",
        placeholder="Confirm Password",
        on_input=sigs.confirm_password.set(js("evt.target.value"))
    ),
    # Show error when passwords don't match
    Span(
        "Passwords must match",
        cls="text-red-500",
        data_show=(sigs.password != sigs.confirm_password) & (sigs.confirm_password != "")
    ),
    data_signals=sigs.to_dict()
)
```

#### 3. UI State Management
Tabs, modals, dropdowns, accordions:

```python
sigs = Signals(active_tab="home", modal_open=False)

tabs = Div(
    # Tab buttons
    Button("Home", on_click=sigs.active_tab.set("home")),
    Button("Profile", on_click=sigs.active_tab.set("profile")),

    # Tab content
    Div("Home content", data_show=sigs.active_tab == "home"),
    Div("Profile content", data_show=sigs.active_tab == "profile"),

    data_signals=sigs.to_dict()
)
```

#### 4. Counter/Toggle Patterns
Simple interactive widgets:

```python
sigs = Signals(likes=42, liked=False)

like_button = Button(
    Span(data_text=sigs.likes),
    " ❤️",
    on_click=[
        sigs.liked.toggle(),
        sigs.liked.if_(sigs.likes.add(1), sigs.likes.sub(1))
    ],
    data_class=classes(
        **{"text-red-500": sigs.liked, "text-gray-500": ~sigs.liked}
    ),
    data_signals=sigs.to_dict()
)
```

#### 5. Filter/Search Interfaces
Instant client-side filtering:

```python
sigs = Signals(search="", items=[])

search_box = Div(
    Input(
        placeholder="Search...",
        on_input=sigs.search.set(js("evt.target.value"))
    ),
    # Results update as you type
    Div(id="results"),
    data_signals=sigs.to_dict()
)
```

### When to Use Server-Side Only

Avoid Datastar for:

1. **Static content pages** - No interactivity needed
2. **SEO-critical content** - Initial HTML is sufficient
3. **Simple form submissions** - Traditional POST is simpler
4. **Data that rarely changes** - No benefit from reactivity

```python
# Just use plain HTML/server rendering
@app.get("/about")
def about():
    return Page(
        H1("About Us"),
        P("We build amazing web apps..."),
        # No Datastar needed - static content
        title="About"
    )
```

## Comparison with Other Approaches

| Feature | Datastar | HTMX | Alpine.js | React |
|---------|----------|------|-----------|-------|
| **Reactivity** | Signals | None | Signals | Virtual DOM |
| **SSE Support** | Built-in | Partial extension | None | Manual |
| **Bundle Size** | ~14kb | ~14kb | ~15kb | ~40kb+ |
| **Learning Curve** | Low | Low | Low | High |
| **Python Integration** | Excellent (Nitro) | Good | Manual | Separate |
| **State Management** | Built-in signals | Server state | Built-in | Redux/Context |
| **Build Step** | None | None | None | Required |
| **SSR** | First-class | Yes | Manual | Complex |

### Datastar vs HTMX

**HTMX**: Server returns HTML fragments, no client-side state
**Datastar**: Server returns HTML fragments + has reactive client-side signals

Use **HTMX** when:
- You want pure server-side state
- No complex client-side logic needed
- Simpler mental model (stateless client)

Use **Datastar** when:
- You need reactive UI updates
- Form validation before server submission
- Real-time data via SSE
- Complex client-side interactions

### Datastar vs Alpine.js

Both use signals, but:

**Alpine.js**: Generic reactive framework, no SSE integration
**Datastar**: Built specifically for server-driven apps with SSE

Use **Alpine.js** when:
- You're using a non-Nitro framework
- You don't need SSE
- You prefer Alpine's syntax

Use **Datastar** in Nitro when:
- You want Python-first development
- You need SSE for real-time updates
- You want seamless server/client integration

### Datastar vs React

**React**: Client-side SPA, virtual DOM, separate API server
**Datastar**: Server-first, signals, HTML-driven

Use **React** when:
- Building a complex SPA
- Need extensive component ecosystem
- Client-side routing is essential

Use **Datastar** when:
- Server-side rendering is important
- Want simpler architecture
- Prefer Python over JavaScript
- Don't need complex component lifecycle

## Islands of Interactivity

Datastar excels at the **islands of interactivity** pattern:

```python
# Mostly static page
page = Page(
    Header(
        H1("Blog Post"),
        P("Published on Jan 1, 2025")
    ),

    Article(
        # Static content
        P("Long article text..."),
        P("More content..."),
    ),

    # Island 1: Interactive comments
    Div(
        H2("Comments"),
        comment_section,  # Reactive Datastar component
        data_signals=comment_sigs.to_dict()
    ),

    # Island 2: Like button
    Div(
        like_button,  # Reactive Datastar component
        data_signals=like_sigs.to_dict()
    ),

    title="Blog Post"
)
```

Most of the page is static HTML (fast, SEO-friendly), with small **islands** of interactivity where needed.

## Best Practices

### 1. Start Server-Side

Begin with server-rendered HTML, add Datastar only where needed:

```python
# Good: Progressive enhancement
@app.get("/dashboard")
def dashboard():
    data = get_dashboard_data()

    return Page(
        # Static header
        H1("Dashboard"),

        # Interactive chart (needs Datastar)
        chart_component(data),

        # Static footer
        Footer("© 2025"),

        title="Dashboard",
        datastar=True  # Only include where needed
    )
```

### 2. Keep State Minimal

Only make reactive what changes:

```python
# Bad: Everything in signals
sigs = Signals(
    user_id=123,           # Never changes
    user_name="Alice",     # Never changes
    theme="dark",          # Changes - needs signal
)

# Good: Only reactive data
sigs = Signals(theme="dark")

# Static data as variables
user_id = 123
user_name = "Alice"
```

### 3. Use Type Inference

Let Datastar infer types from initial values:

```python
# Good: Type inference
Signals(count=0, name="", active=True, items=[])

# Unnecessary: Explicit types
Signals(
    count=Signal("count", 0, type_=int),
    name=Signal("name", "", type_=str)
)
```

### 4. Namespace for Complex UIs

Use namespaces to organize related signals:

```python
# Good: Namespaced signals
form_sigs = Signals(namespace="form", email="", password="")
ui_sigs = Signals(namespace="ui", modal_open=False, loading=False)

# Access: $form.email, $ui.modal_open
```

## Summary

Datastar in Nitro provides:

- **Signal-based reactivity** without virtual DOM overhead
- **Server-first architecture** with progressive enhancement
- **Python API** that generates JavaScript
- **SSE integration** for real-time updates
- **Islands of interactivity** for optimal performance

Use it for interactive widgets within server-rendered pages. Avoid it for purely static content.

## Next Steps

- [Signals Documentation](signals.md) - Learn about Signal and Signals classes
- [Attributes Documentation](attributes.md) - Master data-* attributes
- [Expressions Documentation](expressions.md) - Build complex reactive expressions
- [SSE Integration](sse-integration.md) - Real-time server updates
