---
title: Component Library
category: Frontend
order: 9
---

# Component Library Overview

Nitro provides a comprehensive library of 40+ production-ready components that follow a consistent philosophy: **convention over configuration with escape hatches**. Components look great immediately but remain fully customizable.

## Core Philosophy

Components in Nitro are designed with these principles:

- **Zero-config beautiful** - Work out of the box with sensible defaults
- **Fully customizable** - Override any aspect through clear, documented mechanisms
- **Consistent API** - All components follow the same parameter patterns
- **Framework-agnostic** - Work with any Python web framework
- **Accessible by default** - ARIA attributes and keyboard navigation built-in
- **Theme-aware** - Respond to CSS variables and data-theme attributes

## Component API Pattern

Every component follows this structure:

```python
from nitro.infrastructure.html.components import Button

Button(
    *children,                   # Content (text, icons, other elements)
    variant: str = "default",    # Visual variant
    size: str = "md",            # Size variant
    cls: str = "",               # Additional CSS classes (merged with base)
    **attrs                      # HTML attributes (type, disabled, etc.)
)
```

### Key Patterns

**Data Attributes for Variants**

Components use `data-variant` and `data-size` attributes instead of class explosions:

```python
# Clean HTML output
Button("Submit", variant="primary", size="lg")
# → <button class="btn" data-variant="primary" data-size="lg">Submit</button>

# Not this
Button("Submit", cls="btn-primary btn-lg")  # Avoid
```

**Class Merging with `cls`**

The `cls` parameter always merges with base classes - user classes win for specificity:

```python
# Adds custom classes while keeping base styling
Button("Click", cls="mt-4 w-full")
# → <button class="btn mt-4 w-full" data-variant="default" data-size="md">

# Complete override
Button("Custom", cls="bg-gradient-to-r from-blue-500 to-purple-500")
```

**Attribute Pass-through**

All HTML attributes can be passed directly:

```python
Button("Submit", type="submit", disabled=True, aria_label="Submit form")
Button("Link", on_click="handleClick()", data_test="submit-btn")
```

## Component Categories

### Form Controls (12 components)

Interactive input components for forms and data entry.

| Component | Import | Description |
|-----------|--------|-------------|
| `Button` | `from nitro.infrastructure.html.components import Button` | Primary action button |
| `ButtonGroup` | `from nitro.infrastructure.html.components import ButtonGroup` | Group of related buttons |
| `Input` | `from nitro.infrastructure.html.components import Input` | Text input field |
| `Textarea` | `from nitro.infrastructure.html.components import Textarea` | Multi-line text input |
| `Select` | `from nitro.infrastructure.html.components import Select` | Dropdown select menu |
| `Checkbox` | `from nitro.infrastructure.html.components import Checkbox` | Checkbox input |
| `Radio` | `from nitro.infrastructure.html.components import Radio` | Radio button input |
| `Switch` | `from nitro.infrastructure.html.components import Switch` | Toggle switch |
| `Label` | `from nitro.infrastructure.html.components import Label` | Form field label |
| `Field` | `from nitro.infrastructure.html.components import Field` | Form field wrapper |
| `InputGroup` | `from nitro.infrastructure.html.components import InputGroup` | Input with addons |
| `Combobox` | `from nitro.infrastructure.html.components import Combobox` | Autocomplete input |

**Example:**

```python
from nitro.infrastructure.html.components import Field, Label, Input, Button

Field(
    Label("Email Address", for_="email"),
    Input(type="email", id="email", placeholder="you@example.com"),
    Button("Subscribe", variant="primary")
)
```

### Interactive Overlays (7 components)

Modal dialogs, dropdowns, and overlay components.

| Component | Import | Description |
|-----------|--------|-------------|
| `Dialog` | `from nitro.infrastructure.html.components import Dialog` | Modal dialog/popup |
| `AlertDialog` | `from nitro.infrastructure.html.components import AlertDialog` | Confirmation dialog |
| `Dropdown` | `from nitro.infrastructure.html.components import Dropdown` | Dropdown menu |
| `Popover` | `from nitro.infrastructure.html.components import Popover` | Contextual popover |
| `Tooltip` | `from nitro.infrastructure.html.components import Tooltip` | Hover tooltip |
| `Sheet` | `from nitro.infrastructure.html.components import Sheet` | Slide-over panel |
| `Command` | `from nitro.infrastructure.html.components import Command` | Command palette |

**Example:**

```python
from nitro.infrastructure.html.components import Dialog, DialogTrigger, DialogContent
from rusty_tags import H2, P, Button

Dialog(
    DialogTrigger(Button("Open Dialog")),
    DialogContent(
        H2("Confirmation", cls="dialog-title"),
        P("Are you sure you want to proceed?"),
        Button("Cancel", variant="ghost"),
        Button("Confirm", variant="primary")
    )
)
```

### Display Components (7 components)

Components for displaying content and data.

| Component | Import | Description |
|-----------|--------|-------------|
| `Card` | `from nitro.infrastructure.html.components import Card` | Content card container |
| `Table` | `from nitro.infrastructure.html.components import Table` | Data table |
| `Badge` | `from nitro.infrastructure.html.components import Badge` | Label badge |
| `Avatar` | `from nitro.infrastructure.html.components import Avatar` | User avatar |
| `Alert` | `from nitro.infrastructure.html.components import Alert` | Alert message |
| `Toast` | `from nitro.infrastructure.html.components import Toast` | Toast notification |
| `CodeBlock` | `from nitro.infrastructure.html.components import CodeBlock` | Syntax-highlighted code |

**Example:**

```python
from nitro.infrastructure.html.components import Card, CardHeader, CardTitle, CardBody
from rusty_tags import P

Card(
    CardHeader(
        CardTitle("Featured Article")
    ),
    CardBody(
        P("This is the card content with some description text.")
    ),
    variant="elevated"
)
```

### Navigation Components (6 components)

Components for navigation and page structure.

| Component | Import | Description |
|-----------|--------|-------------|
| `Tabs` | `from nitro.infrastructure.html.components import Tabs` | Tab navigation |
| `Breadcrumb` | `from nitro.infrastructure.html.components import Breadcrumb` | Breadcrumb trail |
| `Sidebar` | `from nitro.infrastructure.html.components import Sidebar` | Sidebar navigation |
| `Pagination` | `from nitro.infrastructure.html.components import Pagination` | Page pagination |
| `Accordion` | `from nitro.infrastructure.html.components import Accordion` | Collapsible sections |
| `ThemeSwitcher` | `from nitro.infrastructure.html.components import ThemeSwitcher` | Light/dark mode toggle |

**Example:**

```python
from nitro.infrastructure.html.components import Tabs, TabsList, TabsTrigger, TabsContent
from rusty_tags import P

Tabs(
    TabsList(
        TabsTrigger("Overview", id="overview"),
        TabsTrigger("Details", id="details"),
        TabsTrigger("Settings", id="settings")
    ),
    TabsContent(P("Overview content here"), id="overview"),
    TabsContent(P("Details content here"), id="details"),
    TabsContent(P("Settings content here"), id="settings"),
    default_tab="overview"
)
```

### Advanced Components (6 components)

Specialized components for complex interactions.

| Component | Import | Description |
|-----------|--------|-------------|
| `Calendar` | `from nitro.infrastructure.html.components import Calendar` | Date calendar |
| `DatePicker` | `from nitro.infrastructure.html.components import DatePicker` | Date picker input |
| `Dropzone` | `from nitro.infrastructure.html.components import Dropzone` | File upload dropzone |
| `Progress` | `from nitro.infrastructure.html.components import Progress` | Progress bar |
| `Spinner` | `from nitro.infrastructure.html.components import Spinner` | Loading spinner |
| `Skeleton` | `from nitro.infrastructure.html.components import Skeleton` | Content placeholder |

**Example:**

```python
from nitro.infrastructure.html.components import Progress, Spinner

# Progress bar
Progress(value=65, max=100)

# Loading spinner
Spinner(size="lg")
```

### Layout & Typography (2 components)

Layout utilities and text styling.

| Component | Import | Description |
|-----------|--------|-------------|
| `Container` | `from nitro.infrastructure.html.components import Container` | Content container |
| `Kbd` | `from nitro.infrastructure.html.components import Kbd` | Keyboard shortcut display |

**Example:**

```python
from nitro.infrastructure.html.components import Kbd
from rusty_tags import P

P("Press ", Kbd("Ctrl"), " + ", Kbd("S"), " to save")
```

## Composition Patterns

### Simple Composition

Independent component parts:

```python
from nitro.infrastructure.html.components import Card, CardHeader, CardTitle, CardBody, CardFooter
from rusty_tags import P, Button

Card(
    CardHeader(CardTitle("Card Title")),
    CardBody(P("Card content goes here")),
    CardFooter(Button("Action", variant="primary"))
)
```

### Compound Components (Closure Pattern)

Components with shared state use closures:

```python
from nitro.infrastructure.html.components import Tabs, TabsList, TabsTrigger, TabsContent

# Parent provides context to children
Tabs(
    TabsList(
        TabsTrigger("Tab 1", id="tab1"),  # Children receive signal from parent
        TabsTrigger("Tab 2", id="tab2")
    ),
    TabsContent("Content 1", id="tab1"),
    TabsContent("Content 2", id="tab2"),
    default_tab="tab1"
)
```

## Customization

All components support three levels of customization:

### 1. Variants

Use built-in variants via parameters:

```python
Button("Click", variant="primary", size="lg")
Card("Content", variant="elevated")
Alert("Warning", variant="warning")
```

### 2. Additional Classes

Add utility classes via `cls` parameter:

```python
Button("Click", cls="mt-4 w-full shadow-lg")
Card("Content", cls="border-2 border-blue-500")
```

### 3. Complete Override

Override base classes entirely with Tailwind utilities:

```python
Button(
    "Custom Button",
    cls="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full px-8 py-4"
)
```

## Accessibility Features

All components include:

- **ARIA attributes** - Proper roles, labels, and states
- **Keyboard navigation** - Tab, Enter, Escape, Arrow keys
- **Focus management** - Visible focus indicators
- **Screen reader support** - Descriptive labels and live regions

Example:

```python
Dialog(
    DialogTrigger(Button("Open", aria_label="Open settings dialog")),
    DialogContent(
        H2("Settings", id="dialog-title"),
        # Dialog automatically includes:
        # - role="dialog"
        # - aria-modal="true"
        # - aria-labelledby="dialog-title"
    )
)
```

## Importing Components

Import components from the infrastructure layer:

```python
# Single import
from nitro.infrastructure.html.components import Button

# Multiple imports
from nitro.infrastructure.html.components import (
    Button, Card, Dialog, Input, Table
)

# Import utilities
from nitro.infrastructure.html.components.utils import cn, cva, uniq
```

## Related Documentation

- [Basecoat Styling](./basecoat-styling.md) - CSS variables, data attributes, and the `cn()` utility
- [Custom Themes](./custom-themes.md) - Creating and applying custom themes
- [Nitro TW CLI](./nitro-tw-cli.md) - Building CSS with Tailwind CLI

## Source Code Reference

Component implementations: `nitro/nitro/infrastructure/html/components/`

All components are built on RustyTags (Rust-powered HTML generation) and follow the patterns documented in `nitro/docs_app/content/COMPONENT_GUIDELINES.md`.
