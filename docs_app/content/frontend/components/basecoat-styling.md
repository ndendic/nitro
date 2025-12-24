# Basecoat CSS Styling System

Basecoat is Nitro's component styling system built on CSS variables, data attributes, and semantic class names. It provides a consistent, themeable foundation for all UI components.

## Core Principles

**Semantic Class Names** - Not framework-specific

```css
/* ✅ Good - portable, understandable */
.btn, .card, .input, .dialog-content

/* ❌ Avoid - framework-locked */
.uk-btn, .ui-card, .n-input
```

**Data Attributes for Variants** - Not class explosions

```html
<!-- ✅ Clean, declarative -->
<button class="btn" data-variant="primary" data-size="lg">

<!-- ❌ Messy, hard to override -->
<button class="btn btn-primary btn-lg">
```

**CSS Variables for Theming** - Not hardcoded values

```css
/* ✅ Themeable */
background: var(--color-primary);

/* ❌ Not themeable */
background: #18181b;
```

## CSS Variable System

Basecoat uses a two-tier CSS variable system: **base tokens** and **component tokens**.

### Base Color Tokens

Location: `nitro/docs_app/static/css/basecoat/base/base.css`

```css
:root {
  /* Base color tokens */
  --background: oklch(1 0 0);
  --foreground: oklch(0.1450 0 0);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.1450 0 0);
  --primary: oklch(0.2050 0 0);
  --primary-foreground: oklch(0.9850 0 0);
  --secondary: oklch(0.9700 0 0);
  --secondary-foreground: oklch(0.2050 0 0);
  --muted: oklch(0.9700 0 0);
  --muted-foreground: oklch(0.5560 0 0);
  --accent: oklch(0.9700 0 0);
  --accent-foreground: oklch(0.2050 0 0);
  --destructive: oklch(0.5770 0.2450 27.3250);
  --destructive-foreground: oklch(1 0 0);
  --border: oklch(0.9220 0 0);
  --input: oklch(0.9220 0 0);
  --ring: oklch(0.7080 0 0);
}
```

### Component Tokens

```css
:root {
  /* Spacing & Layout */
  --radius: 0.625rem;
  --spacing: 0.25rem;

  /* Shadows */
  --shadow-sm: 0 1px 3px 0px hsl(0 0% 0% / 0.10);
  --shadow-md: 0 2px 4px -1px hsl(0 0% 0% / 0.10);
  --shadow-lg: 0 4px 6px -1px hsl(0 0% 0% / 0.10);

  /* Typography */
  --font-sans: ui-sans-serif, system-ui, -apple-system, sans-serif;
  --font-serif: ui-serif, Georgia, "Times New Roman", serif;
  --font-mono: ui-monospace, SFMono-Regular, Consolas, monospace;
  --tracking-normal: 0em;
}
```

### Dark Mode Variables

Dark mode is activated via `.dark` class or `[data-theme="dark"]` attribute:

```css
.dark {
  --background: oklch(0.1450 0 0);
  --foreground: oklch(0.9850 0 0);
  --card: oklch(0.2050 0 0);
  --card-foreground: oklch(0.9850 0 0);
  --primary: oklch(0.9220 0 0);
  --primary-foreground: oklch(0.2050 0 0);
  --border: oklch(0.2750 0 0);
  --muted-foreground: oklch(0.7080 0 0);
}
```

## Data Attribute Variants

Components use `data-variant` and `data-size` attributes for styling variations.

### Variant Patterns

Location: `nitro/docs_app/static/css/basecoat/components/button.css`

```css
/* Base button styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  border-radius: var(--radius);
  transition: all 150ms ease;
}

/* Variant via data-variant attribute */
.btn[data-variant="default"] {
  background: var(--secondary);
  color: var(--secondary-foreground);
}

.btn[data-variant="primary"] {
  background: var(--primary);
  color: var(--primary-foreground);
}

.btn[data-variant="destructive"] {
  background: var(--destructive);
  color: var(--destructive-foreground);
}

.btn[data-variant="ghost"] {
  background: transparent;
  color: var(--foreground);
}

.btn[data-variant="outline"] {
  border: 1px solid var(--border);
  background: transparent;
}
```

### Size Patterns

```css
/* Size via data-size attribute */
.btn[data-size="sm"] {
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  height: 2rem;
}

.btn[data-size="md"] {
  padding: 0.625rem 1rem;
  font-size: 1rem;
  height: 2.25rem;
}

.btn[data-size="lg"] {
  padding: 0.75rem 1.5rem;
  font-size: 1.125rem;
  height: 2.5rem;
}
```

### Using Data Attributes in Python

```python
from nitro.infrastructure.html.components import Button

# Variants
Button("Default")                           # data-variant="default"
Button("Primary", variant="primary")        # data-variant="primary"
Button("Danger", variant="destructive")     # data-variant="destructive"

# Sizes
Button("Small", size="sm")                  # data-size="sm"
Button("Medium", size="md")                 # data-size="md" (default)
Button("Large", size="lg")                  # data-size="lg"

# Combined
Button("Save", variant="primary", size="lg")
```

## The `cn()` Utility

Location: `nitro/nitro/infrastructure/html/components/utils.py`

The `cn()` (class names) utility intelligently merges multiple class sources.

### Basic Usage

```python
from nitro.infrastructure.html.components.utils import cn

# Combine strings
cn("btn", "mt-4")                    # → "btn mt-4"

# Ignore falsy values
cn("btn", None, "mt-4")              # → "btn mt-4"
cn("btn", False, "mt-4")             # → "btn mt-4"
cn("btn", "", "mt-4")                # → "btn mt-4"

# Conditional classes (dictionary)
is_active = True
cn("btn", {"active": is_active})     # → "btn active"
cn("btn", {"active": False})         # → "btn"

# Flatten lists/tuples
cn("btn", ["flex", "gap-2"])         # → "btn flex gap-2"
cn("btn", ("text-sm", "font-bold"))  # → "btn text-sm font-bold"
```

### In Components

User classes always come last (higher specificity):

```python
def Button(*children, cls="", **attrs):
    return HTMLButton(
        *children,
        cls=cn("btn", cls),  # Base classes + user classes
        **attrs
    )

# Usage
Button("Click", cls="mt-4 w-full")
# → <button class="btn mt-4 w-full">Click</button>
```

### Complex Conditions

```python
cn(
    "btn",
    {
        "btn-loading": is_loading,
        "btn-disabled": is_disabled,
        "w-full": is_full_width
    },
    user_cls
)
```

## Component CSS Structure

Basecoat organizes component styles in a hierarchical structure:

```
nitro/docs_app/static/css/basecoat/
├── base/
│   └── base.css              # CSS variables, reset, typography
├── components/
│   ├── button.css            # Button styles
│   ├── card.css              # Card styles
│   ├── dialog.css            # Dialog styles
│   ├── form/
│   │   ├── input.css         # Input field styles
│   │   ├── checkbox.css      # Checkbox styles
│   │   ├── select.css        # Select dropdown styles
│   │   └── switch.css        # Toggle switch styles
│   └── ...                   # Other component styles
├── basecoat.css              # Main bundle (base + components)
└── basecoat.all.css          # Complete bundle with all variants
```

### Loading Basecoat CSS

**Option 1: Include in Page**

```python
from nitro.infrastructure.html import Page
from rusty_tags import Link

page = Page(
    content,
    hdrs=(
        Link(rel="stylesheet", href="/static/css/basecoat/basecoat.css"),
    ),
    title="My App"
)
```

**Option 2: CDN Link**

```python
from rusty_tags import Link

Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/@nitro/basecoat@latest/basecoat.css"
)
```

## Customization Patterns

### Level 1: Override CSS Variables

Create a custom stylesheet to override variables:

```css
/* custom.css */
:root {
  --primary: oklch(0.45 0.24 264);        /* Purple */
  --primary-foreground: oklch(1 0 0);
  --radius: 0.375rem;                      /* Smaller radius */
  --font-sans: 'Inter', sans-serif;        /* Custom font */
}
```

### Level 2: Additional Classes via `cls`

```python
from nitro.infrastructure.html.components import Button

# Add utility classes
Button("Click", cls="mt-4 shadow-lg hover:shadow-xl")

# Add custom animation
Button("Pulse", cls="animate-pulse")

# Combine with variants
Button("Primary", variant="primary", cls="w-full text-lg")
```

### Level 3: Complete Override

Replace component classes entirely:

```python
Button(
    "Gradient Button",
    cls="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-4 rounded-full shadow-lg hover:shadow-xl transition-all"
)
```

### Level 4: Custom Component CSS

Create new component styles that use Basecoat variables:

```css
/* custom-components.css */
.my-special-card {
  background: var(--card);
  color: var(--card-foreground);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: calc(var(--spacing) * 4);
  box-shadow: var(--shadow-md);
}

.my-special-card[data-variant="highlighted"] {
  border-color: var(--primary);
  background: color-mix(in oklch, var(--primary) 10%, var(--card));
}
```

```python
from rusty_tags import Div

Div(
    "Custom card content",
    cls="my-special-card",
    data_variant="highlighted"
)
```

## Using with Tailwind CSS

Basecoat works alongside Tailwind CSS:

```python
from nitro.infrastructure.html.components import Button, Card

# Mix Basecoat components with Tailwind utilities
Card(
    Button("Click", variant="primary"),
    cls="max-w-md mx-auto mt-8 space-y-4"
)

# Use Tailwind for layout, Basecoat for components
Div(
    Card("Card 1", cls="col-span-1"),
    Card("Card 2", cls="col-span-1"),
    Card("Card 3", cls="col-span-2"),
    cls="grid grid-cols-2 gap-4 p-4"
)
```

## Component State Attributes

Beyond variants and sizes, components use data attributes for state:

```css
/* State via data-state attribute */
.input[data-state="error"] {
  border-color: var(--destructive);
}

.input[data-state="success"] {
  border-color: var(--success);
}

/* Loading state */
.btn[data-loading="true"] {
  opacity: 0.6;
  pointer-events: none;
}

/* Disabled state (use disabled attribute) */
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

```python
from nitro.infrastructure.html.components import Input

Input(data_state="error", placeholder="Email")
Input(data_state="success", placeholder="Email")
```

## Related Documentation

- [Component Library Overview](./overview.md) - All available components
- [Custom Themes](./custom-themes.md) - Creating custom color schemes
- [Nitro TW CLI](./nitro-tw-cli.md) - Building CSS with Tailwind

## Source Code Reference

- CSS Variables: `nitro/docs_app/static/css/basecoat/base/base.css`
- Component Styles: `nitro/docs_app/static/css/basecoat/components/`
- `cn()` Utility: `nitro/nitro/infrastructure/html/components/utils.py:6-24`
