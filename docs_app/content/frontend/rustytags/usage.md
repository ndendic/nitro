---
title: RustyTags Usage
category: Frontend
order: 2
---

# RustyTags Usage

This guide covers practical usage patterns for RustyTags, including tag nesting, the Page component, class handling, and attribute management.

## Tag Nesting

RustyTags tags accept child elements as positional arguments, making nested HTML structures intuitive:

### Basic Nesting

```python
from rusty_tags import Div, H1, P

# Simple nesting
content = Div(
    H1("Welcome"),
    P("This is a paragraph"),
    P("Another paragraph")
)

# Output:
# <div>
#   <h1>Welcome</h1>
#   <p>This is a paragraph</p>
#   <p>Another paragraph</p>
# </div>
```

### Deep Nesting

```python
from rusty_tags import Div, Section, Article, H2, P

page_content = Div(
    Section(
        Article(
            H2("Article Title"),
            P("Article content goes here"),
            cls="article"
        ),
        cls="content-section"
    ),
    cls="container"
)
```

### Dynamic Content with List Comprehensions

```python
from rusty_tags import Ul, Li, Div, H3

# Generate list items dynamically
items = ["Apple", "Banana", "Cherry", "Date"]

shopping_list = Div(
    H3("Shopping List"),
    Ul(
        *[Li(item) for item in items],
        cls="list-disc pl-5"
    )
)

# Output:
# <div>
#   <h3>Shopping List</h3>
#   <ul class="list-disc pl-5">
#     <li>Apple</li>
#     <li>Banana</li>
#     <li>Cherry</li>
#     <li>Date</li>
#   </ul>
# </div>
```

### Conditional Rendering

```python
from rusty_tags import Div, H1, P, Button

def user_dashboard(user, is_admin=False):
    return Div(
        H1(f"Welcome, {user.name}"),
        P("Your dashboard", cls="subtitle"),
        # Conditional elements - None values are filtered out
        Button("Admin Panel", cls="btn-admin") if is_admin else None,
        P("Access level: Admin") if is_admin else P("Access level: User"),
        cls="dashboard"
    )

# None values are automatically filtered out
dashboard = user_dashboard(user, is_admin=True)
```

### Spreading Elements with Unpacking

```python
from rusty_tags import Div, P

# Generate multiple elements
def create_paragraphs(texts):
    return [P(text) for text in texts]

paragraphs = create_paragraphs(["First", "Second", "Third"])

# Spread into parent
content = Div(
    *paragraphs,  # Unpack list into individual arguments
    cls="content"
)
```

## The Page Component

Nitro's `Page` component extends RustyTags with a complete HTML page structure and convenient CDN integrations.

### Import Location

```python
# Import from Nitro (enhanced version)
from nitro.infrastructure.html import Page

# Or from RustyTags (basic version)
from rusty_tags import Page
```

> **Note**: Nitro's `Page` component includes additional features like Basecoat components, theme support, and more CDN options. The examples below use Nitro's enhanced version.

### Basic Usage

```python
from nitro.infrastructure.html import Page
from rusty_tags import Div, H1, P

page = Page(
    Div(
        H1("Welcome to My Site"),
        P("This is a complete HTML page"),
        cls="container"
    ),
    title="Home"
)

html_string = str(page)
```

This generates a complete HTML document:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Home</title>
</head>
<body>
    <div class="container">
        <h1>Welcome to My Site</h1>
        <p>This is a complete HTML page</p>
    </div>
</body>
</html>
```

### Page Component Parameters

**Source**: `nitro/nitro/infrastructure/html/templating.py:136`

```python
Page(
    *content,                    # Body content elements
    title: str = "Nitro",        # Page title
    hdrs: tuple | None = None,   # Additional <head> elements
    ftrs: tuple | None = None,   # Additional footer scripts/elements
    htmlkw: dict | None = None,  # <html> tag attributes
    bodykw: dict | None = None,  # <body> tag attributes
    datastar: bool = True,       # Include Datastar SDK
    ds_version: str = "1.0.0-RC.6",  # Datastar version
    nitro_components: bool = True,   # Include Nitro component styles
    monsterui: bool = False,     # Include MonsterUI (FrankenUI)
    tailwind4: bool = False,     # Include Tailwind v4 CDN
    lucide: bool = False,        # Include Lucide icons
    highlightjs: bool = False,   # Include Highlight.js for code
)
```

### Including CDN Libraries

```python
from nitro.infrastructure.html import Page
from rusty_tags import Div, H1, Pre, Code

# Include Datastar for reactivity
page_with_datastar = Page(
    Div("Reactive content"),
    title="Reactive App",
    datastar=True  # Includes Datastar SDK
)

# Include Tailwind CSS v4
page_with_tailwind = Page(
    Div("Styled content", cls="bg-blue-500 text-white p-4"),
    title="Styled App",
    tailwind4=True
)

# Include Highlight.js for code highlighting
page_with_code = Page(
    Pre(Code("print('Hello, World!')", cls="language-python")),
    title="Code Demo",
    highlightjs=True
)

# Combine multiple CDNs
full_featured_page = Page(
    Div("Full-featured app"),
    title="Full App",
    datastar=True,
    tailwind4=True,
    lucide=True,      # Lucide icons
    highlightjs=True  # Code highlighting
)
```

### Custom Headers and Footers

```python
from nitro.infrastructure.html import Page
from rusty_tags import Div, Meta, Link, Script

page = Page(
    Div("Content"),
    title="Custom Page",
    # Additional <head> elements
    hdrs=(
        Meta(name="description", content="My awesome page"),
        Meta(name="keywords", content="python, web, framework"),
        Link(rel="stylesheet", href="/custom.css"),
        Script(src="/analytics.js"),
    ),
    # Additional footer scripts
    ftrs=(
        Script("console.log('Page loaded');"),
    )
)
```

### HTML and Body Attributes

```python
from nitro.infrastructure.html import Page
from rusty_tags import Div

page = Page(
    Div("Content"),
    title="Custom Attributes",
    # Add attributes to <html> tag
    htmlkw={"lang": "en", "data_theme": "dark"},
    # Add attributes to <body> tag
    bodykw={"data_controller": "app", "cls": "bg-gray-100"}
)

# Output includes:
# <html lang="en" data-theme="dark">
# <body data-controller="app" class="bg-gray-100">
```

## Class Handling

The `cls` parameter is RustyTags' standard way to add CSS classes to elements.

### Basic Class Usage

```python
from rusty_tags import Div, Button

# Single class
element = Div("Content", cls="container")
# <div class="container">Content</div>

# Multiple classes
element = Div("Content", cls="container mx-auto p-4")
# <div class="container mx-auto p-4">Content</div>

# Tailwind utility classes
button = Button(
    "Click me",
    cls="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
)
```

### Dynamic Classes

```python
from rusty_tags import Div

# Build classes dynamically
base_classes = "btn"
variant_class = "btn-primary"
size_class = "btn-lg"

button = Div(
    "Submit",
    cls=f"{base_classes} {variant_class} {size_class}"
)
# <div class="btn btn-primary btn-lg">Submit</div>
```

### Conditional Classes

```python
from rusty_tags import Div, Button

def render_alert(message, is_error=False):
    alert_classes = f"alert {'alert-error' if is_error else 'alert-info'}"
    return Div(message, cls=alert_classes)

# Usage
info_alert = render_alert("Success!", is_error=False)
# <div class="alert alert-info">Success!</div>

error_alert = render_alert("Failed!", is_error=True)
# <div class="alert alert-error">Failed!</div>
```

### Class Utilities in Nitro

Nitro provides the `cn()` utility for conditional class merging:

```python
from nitro.infrastructure.html.components.utils import cn
from rusty_tags import Button

def CustomButton(label, variant="primary", disabled=False):
    return Button(
        label,
        cls=cn(
            "btn",  # base classes
            variant == "primary" and "btn-primary",
            variant == "secondary" and "btn-secondary",
            disabled and "opacity-50 cursor-not-allowed"
        )
    )

# Usage
button1 = CustomButton("Click", variant="primary")
# <button class="btn btn-primary">Click</button>

button2 = CustomButton("Disabled", disabled=True)
# <button class="btn opacity-50 cursor-not-allowed">Disabled</button>
```

## Attribute Handling

RustyTags supports all standard HTML attributes through keyword arguments.

### Standard Attributes

```python
from rusty_tags import Input, A, Img, Div

# Form input attributes
email_input = Input(
    type="email",
    name="user_email",
    placeholder="Enter your email",
    required=True
)

# Link attributes
link = A(
    "Visit Example",
    href="https://example.com",
    target="_blank",
    rel="noopener noreferrer"
)

# Image attributes
image = Img(
    src="/logo.png",
    alt="Company Logo",
    width="200",
    height="100"
)

# Data attributes
widget = Div(
    "Widget content",
    data_id="widget-123",
    data_action="toggle"
)
```

### Python Reserved Words

Python reserved words like `for`, `class`, and `async` require a trailing underscore:

```python
from rusty_tags import Label, Input

# 'for' is a Python keyword, use 'for_'
label = Label(
    "Email Address",
    for_="email-input"  # References <input id="email-input">
)
# <label for="email-input">Email Address</label>

# 'class' is reserved, use 'class_' or 'cls'
div1 = Div("Content", class_="container")
div2 = Div("Content", cls="container")  # Preferred
```

**Common reserved word mappings:**
- `for` → `for_`
- `class` → `class_` or `cls` (use `cls` by preference)
- `async` → `async_`
- `is` → `is_`

### Boolean Attributes

```python
from rusty_tags import Input, Button

# Boolean attributes
checkbox = Input(
    type="checkbox",
    checked=True,      # Rendered as 'checked'
    disabled=False     # Omitted from output
)

button = Button(
    "Submit",
    disabled=True,     # Rendered as 'disabled'
    autofocus=True     # Rendered as 'autofocus'
)
```

### Data Attributes

Data attributes are commonly used for JavaScript frameworks and custom behavior:

```python
from rusty_tags import Div, Button

# Convert underscores to hyphens
widget = Div(
    "Content",
    data_widget_id="123",      # → data-widget-id="123"
    data_action="click",       # → data-action="click"
    data_target="modal"        # → data-target="modal"
)

# Datastar attributes (for reactive components)
counter = Button(
    "Increment",
    on_click="$count++",               # → data-on-click
    data_signals='{"count": 0}'        # Datastar signals
)
```

### Event Handlers (Datastar/HTMX)

```python
from rusty_tags import Button, Form, Input

# Datastar event handlers
button = Button(
    "Submit",
    on_click="$form.submit()"  # → data-on-click
)

# HTMX attributes
form = Form(
    Input(type="text", name="query"),
    Button("Search"),
    hx_post="/search",         # → hx-post
    hx_target="#results",      # → hx-target
    hx_swap="outerHTML"        # → hx-swap
)
```

### Arbitrary Attributes

You can pass any attribute name:

```python
from rusty_tags import Div

# Custom attributes
custom = Div(
    "Content",
    aria_label="Main content",        # → aria-label
    role="main",                       # → role
    custom_attr="value",               # → custom-attr
    x_data="{ open: false }"          # → x-data (Alpine.js)
)
```

### Dictionary Unpacking

Pass multiple attributes at once using dictionary unpacking:

```python
from rusty_tags import Div

attrs = {
    "id": "main-content",
    "data_controller": "app",
    "aria_label": "Main",
    "cls": "container"
}

element = Div("Content", **attrs)
# <div id="main-content" data-controller="app" aria-label="Main" class="container">
```

## HTML Rendering

### Converting to Strings

```python
from rusty_tags import Div, H1

# Create element
element = Div(H1("Hello"))

# Convert to HTML string
html = str(element)
print(html)
# Output: <div><h1>Hello</h1></div>
```

### In Web Frameworks

```python
from rusty_tags import Div, H1
from nitro.infrastructure.html import Page

# FastAPI
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def homepage():
    return HTMLResponse(str(Page(
        Div(H1("Home")),
        title="Home"
    )))

# Flask
from flask import Flask

app = Flask(__name__)

@app.route("/")
def homepage():
    return str(Page(
        Div(H1("Home")),
        title="Home"
    ))
```

### Fragments

Use `Fragment` to group elements without a wrapper:

```python
from rusty_tags import Fragment, H1, P, Div

# Fragment doesn't render a wrapper element
content = Fragment(
    H1("Title"),
    P("Paragraph 1"),
    P("Paragraph 2")
)

page = Div(content, cls="container")

# Output:
# <div class="container">
#   <h1>Title</h1>
#   <p>Paragraph 1</p>
#   <p>Paragraph 2</p>
# </div>
```

### Safe HTML Strings

Use `Safe` to mark trusted HTML strings:

```python
from rusty_tags import Div, Safe

# Raw HTML (use with caution!)
trusted_html = Safe("<strong>Trusted</strong> content")

element = Div(
    "Normal content",
    trusted_html,
    cls="wrapper"
)

# Output:
# <div class="wrapper">
#   Normal content
#   <strong>Trusted</strong> content
# </div>
```

> **Security Warning**: Only use `Safe` with HTML you trust. Never use it with user-generated content as it bypasses HTML escaping and can lead to XSS vulnerabilities.

## Custom Tags

Create custom tags with `CustomTag`:

```python
from rusty_tags import CustomTag

# Create a custom element
CustomElement = CustomTag("custom-element")

widget = CustomElement(
    "Widget content",
    data_widget="true",
    cls="my-widget"
)

# Output:
# <custom-element data-widget="true" class="my-widget">
#   Widget content
# </custom-element>
```

## Practical Examples

### Complete Form

```python
from rusty_tags import Form, Div, Label, Input, Button, P
from nitro.infrastructure.html import Page

def login_form():
    return Form(
        Div(
            Label("Email", for_="email", cls="block mb-2"),
            Input(
                type="email",
                id="email",
                name="email",
                placeholder="you@example.com",
                cls="w-full px-3 py-2 border rounded"
            ),
            cls="mb-4"
        ),
        Div(
            Label("Password", for_="password", cls="block mb-2"),
            Input(
                type="password",
                id="password",
                name="password",
                cls="w-full px-3 py-2 border rounded"
            ),
            cls="mb-4"
        ),
        Button(
            "Sign In",
            type="submit",
            cls="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-700"
        ),
        method="post",
        action="/login",
        cls="max-w-md mx-auto p-6 bg-white shadow-md rounded"
    )

page = Page(login_form(), title="Login")
```

### Card Component

```python
from rusty_tags import Div, H3, P, Button

def Card(title, content, action_label="Learn More"):
    return Div(
        Div(
            H3(title, cls="text-xl font-bold mb-2"),
            P(content, cls="text-gray-600 mb-4"),
            Button(
                action_label,
                cls="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-700"
            ),
            cls="p-6"
        ),
        cls="bg-white shadow-md rounded-lg"
    )

# Usage
cards = Div(
    Card("Feature 1", "Description of feature 1"),
    Card("Feature 2", "Description of feature 2", action_label="Try Now"),
    Card("Feature 3", "Description of feature 3"),
    cls="grid grid-cols-3 gap-4"
)
```

### Navigation Menu

```python
from rusty_tags import Nav, Ul, Li, A

def navbar(items):
    return Nav(
        Ul(
            *[Li(
                A(item["label"], href=item["url"], cls="hover:text-blue-500"),
                cls="inline-block mx-2"
            ) for item in items],
            cls="flex"
        ),
        cls="bg-gray-800 text-white p-4"
    )

menu = navbar([
    {"label": "Home", "url": "/"},
    {"label": "About", "url": "/about"},
    {"label": "Contact", "url": "/contact"}
])
```

## Source References

- **Page Component**: `nitro/nitro/infrastructure/html/templating.py:136`
- **RustyTags Core**: `RustyTags/rusty_tags/__init__.py`
- **Tag Implementations**: `RustyTags/src/lib.rs`

## Related Documentation

- [RustyTags Overview](./overview.md) - Performance benefits and architecture
- [Datastar Philosophy](../datastar/philosophy.md) - Reactive components
- [Datastar Attributes](../datastar/attributes.md) - Data attribute binding
- [Component Styling](../components/basecoat-styling.md) - Nitro component system
