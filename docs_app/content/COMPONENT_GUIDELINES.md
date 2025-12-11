# Nitro Component Guidelines

This document defines the patterns and principles for creating UI components in the Nitro framework.

## Core Philosophy

**Convention over Configuration with Escape Hatches** - Components should look great immediately, but every aspect must be customizable through clear, documented mechanisms.

---

## 1. Component Structure

### Basic Pattern

Every component follows this structure:

```python
from rusty_tags import Button as HTMLButton, HtmlString
from .utils import cn

def Button(
    *children,
    variant: str = "default",   # primary, secondary, ghost, destructive
    size: str = "md",           # sm, md, lg
    cls: str = "",              # User's additional classes (always wins)
    **attrs                     # Pass-through HTML attributes
) -> HtmlString:
    """Button component with sensible defaults.
    
    Args:
        *children: Button content (text, icons, etc.)
        variant: Visual style variant
        size: Size variant
        cls: Additional CSS classes (merged with base classes)
        **attrs: Any valid HTML button attributes (type, disabled, etc.)
    
    Example:
        Button("Click me", variant="primary", size="lg")
        Button("Submit", type="submit", disabled=True)
        Button("Custom", cls="bg-gradient-to-r from-purple-500 to-pink-500")
    """
    return HTMLButton(
        *children,
        cls=cn("btn", cls),        # Base class + user classes
        data_variant=variant,       # Variant via data attribute
        data_size=size,            # Size via data attribute
        **attrs                    # Pass through all other attributes
    )
```

### Key Rules

1. **`cls` parameter always merges** - User classes are appended to base classes
2. **Variants via data attributes** - Not class explosions like `btn-primary btn-lg`
3. **Pass-through attributes** - `**attrs` allows any HTML attribute
4. **Sensible defaults** - Components work without any parameters

---

## 2. Naming Conventions

### Class Names

Use **semantic names**, not framework-specific prefixes:

```python
# ✅ Good - semantic, portable, understandable
cls="btn"
cls="card"
cls="input"
cls="dialog-content"
cls="sheet-overlay"

# ❌ Avoid - framework-locked
cls="uk-btn"
cls="ui-card"
cls="n-input"
```

### Data Attributes

Use consistent naming for component state and variants:

```html
<!-- Pattern: data-{property}="{value}" -->
<button class="btn" data-variant="primary" data-size="lg">
<div class="card" data-variant="elevated">
<input class="input" data-state="error">
```

### Component Parts

For compound components, use BEM-like naming:

```python
# Dialog component parts
cls="dialog"           # Root
cls="dialog-trigger"   # Trigger button
cls="dialog-content"   # Content wrapper
cls="dialog-header"    # Header section
cls="dialog-title"     # Title element
cls="dialog-body"      # Body content
cls="dialog-footer"    # Footer section
cls="dialog-close"     # Close button
```

---

## 3. Using the Utility Functions

### `cn()` - Class Name Merger

Located in `nitro/infrastructure/html/components/utils.py`

```python
from .utils import cn

# Combines multiple class sources
cn("btn", "mt-4")                    # "btn mt-4"
cn("btn", None, "mt-4")              # "btn mt-4" (None ignored)
cn("btn", {"active": is_active})     # Conditional classes
cn("btn", ["flex", "gap-2"])         # Lists/tuples flattened

# In components - user classes always added last (higher specificity)
cls=cn("btn", user_cls)
```

### `cva()` - Class Variant Authority

For complex variant logic (alternative to data attributes for Tailwind-heavy styling):

```python
from .utils import cva

button_variants = cva(
    base="inline-flex items-center justify-center font-medium transition-colors",
    config={
        "variants": {
            "variant": {
                "default": "bg-zinc-900 text-white hover:bg-zinc-800",
                "secondary": "bg-zinc-100 text-zinc-900 hover:bg-zinc-200",
                "ghost": "hover:bg-zinc-100",
                "destructive": "bg-red-500 text-white hover:bg-red-600",
            },
            "size": {
                "sm": "h-8 px-3 text-sm",
                "md": "h-10 px-4",
                "lg": "h-12 px-6 text-lg",
            },
        },
        "defaultVariants": {
            "variant": "default",
            "size": "md",
        },
    }
)

# Usage
def Button(*children, variant="default", size="md", cls="", **attrs):
    return HTMLButton(
        *children,
        cls=cn(button_variants(variant=variant, size=size), cls),
        **attrs
    )
```

**When to use `cva()` vs data attributes:**
- Use **data attributes** when CSS handles variants (recommended for theming)
- Use **`cva()`** when you need Tailwind utility classes for variants

---

## 4. CSS Variables for Theming

### Defining Component Variables

In your CSS file (`nitro/css/variables.css`):

```css
:root {
  /* Base color tokens */
  --color-primary: #18181b;
  --color-primary-fg: #ffffff;
  --color-secondary: #f4f4f5;
  --color-muted: #71717a;
  --color-border: #e4e4e7;
  --color-background: #ffffff;
  --color-foreground: #09090b;
  
  /* Button tokens */
  --btn-radius: 0.375rem;
  --btn-font-weight: 500;
  
  /* Card tokens */
  --card-radius: 0.5rem;
  --card-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
}

/* Dark mode */
.dark, [data-theme="dark"] {
  --color-primary: #fafafa;
  --color-primary-fg: #18181b;
  --color-background: #09090b;
  --color-foreground: #fafafa;
  --color-border: #27272a;
}
```

### Using Variables in Component CSS

In your component CSS (`nitro/css/components.css`):

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--btn-font-weight);
  border-radius: var(--btn-radius);
  transition: all 150ms ease;
  cursor: pointer;
}

.btn[data-variant="default"] {
  background: var(--color-secondary);
  color: var(--color-foreground);
}

.btn[data-variant="primary"] {
  background: var(--color-primary);
  color: var(--color-primary-fg);
}

.btn[data-size="sm"] { 
  padding: 0.5rem 0.75rem; 
  font-size: 0.875rem; 
}

.btn[data-size="md"] { 
  padding: 0.625rem 1rem; 
  font-size: 1rem; 
}

.btn[data-size="lg"] { 
  padding: 0.75rem 1.5rem; 
  font-size: 1.125rem; 
}
```

---

## 5. Interactivity Strategy

### Layer 1: Native HTML (Preferred)

Use native HTML elements and attributes when possible:

```python
# Native dialog element
from rusty_tags import Dialog as NativeDialog

def Dialog(*children, id, **attrs):
    return NativeDialog(
        *children,
        id=id,
        cls="dialog",
        **attrs
    )

# Native details/summary for accordions
def Accordion(*children, **attrs):
    return Details(*children, cls="accordion", **attrs)
```

### Layer 2: CSS Features

Use modern CSS for interactions:

```css
/* @starting-style for enter animations */
dialog {
  opacity: 0;
  transition: opacity 200ms ease;
}

dialog[open] {
  opacity: 1;
  
  @starting-style {
    opacity: 0;
  }
}

/* :has() for parent styling based on child state */
.accordion:has([open]) .accordion-icon {
  transform: rotate(180deg);
}

/* Popover API */
[popover] {
  /* styles */
}
```

### Layer 3: Datastar

For reactive state that CSS can't handle:

```python
from rusty_tags.datastar import Signals

def Tabs(*children, default_tab, signal=None, **attrs):
    signal = signal or f"tabs_{uniq()}"
    
    return Div(
        *children,
        signals=Signals(**{signal: default_tab}),
        cls="tabs",
        **attrs
    )

def TabsTrigger(*children, id, **attrs):
    # Returns a closure that receives signal context
    def create_trigger(signal, default_tab):
        return Button(
            *children,
            on_click=f"${signal} = '{id}'",
            data_class=f"{{'active': ${signal} === '{id}'}}",
            cls="tabs-trigger",
            **attrs
        )
    return create_trigger
```

### Layer 4: Minimal JavaScript

Only for edge cases (focus traps, complex animations, clipboard):

```python
def DialogTrigger(*children, dialog_id, **attrs):
    return Button(
        *children,
        on_click=f"document.getElementById('{dialog_id}').showModal()",
        cls="dialog-trigger",
        **attrs
    )
```

---

## 6. Accessibility Requirements

### Required ARIA Attributes

```python
def Dialog(*children, id, **attrs):
    return NativeDialog(
        *children,
        id=id,
        aria_modal="true",
        role="dialog",
        aria_labelledby=f"{id}-title",
        **attrs
    )

def DialogTitle(*children, dialog_id, **attrs):
    return H2(
        *children,
        id=f"{dialog_id}-title",
        cls="dialog-title",
        **attrs
    )
```

### Keyboard Navigation

Ensure components support:
- **Tab** - Move between focusable elements
- **Enter/Space** - Activate buttons, toggle accordions
- **Escape** - Close dialogs, dropdowns
- **Arrow keys** - Navigate within tabs, menus, lists

### Focus Management

```python
# Auto-focus first focusable element in dialogs
def DialogContent(*children, **attrs):
    return Div(
        *children,
        data_on_load="this.querySelector('button, input, [tabindex]')?.focus()",
        cls="dialog-content",
        **attrs
    )
```

---

## 7. Component Composition Patterns

### Compound Components (Closure Pattern)

For components with coordinated parts:

```python
def Tabs(*children, default_tab, signal=None, **attrs):
    """Parent that provides context to children via closures."""
    signal = signal or f"tabs_{uniq()}"
    
    # Process children - call them if they're closures
    processed = [
        child(signal, default_tab) if callable(child) else child
        for child in children
    ]
    
    return Div(
        *processed,
        signals=Signals(**{signal: default_tab}),
        cls="tabs",
        **attrs
    )

def TabsTrigger(*children, id, **attrs):
    """Returns a closure that receives context from parent."""
    def create(signal, default_tab):
        return Button(
            *children,
            on_click=f"${signal} = '{id}'",
            cls="tabs-trigger",
            **attrs
        )
    return create
```

### Simple Composition

For independent pieces:

```python
def Card(*children, cls="", **attrs):
    return Div(*children, cls=cn("card", cls), **attrs)

def CardHeader(*children, cls="", **attrs):
    return Div(*children, cls=cn("card-header", cls), **attrs)

def CardTitle(*children, cls="", **attrs):
    return H3(*children, cls=cn("card-title", cls), **attrs)

def CardBody(*children, cls="", **attrs):
    return Div(*children, cls=cn("card-body", cls), **attrs)

# Usage
Card(
    CardHeader(CardTitle("My Card")),
    CardBody("Content here"),
)
```

---

## 8. File Organization

```
nitro/infrastructure/html/components/
├── __init__.py          # Public exports
├── utils.py             # cn(), cva(), uniq(), helpers
├── button.py            # Button component
├── card.py              # Card, CardHeader, CardBody, etc.
├── dialog.py            # Dialog components
├── tabs.py              # Tabs components
├── sheet.py             # Sheet (slide-over panel)
├── accordion.py         # Accordion components
├── inputs.py            # Input, Select, Textarea, etc.
└── ...
```

### Export Pattern

In `__init__.py`:

```python
from .utils import cn, cva, uniq
from .button import Button
from .card import Card, CardHeader, CardTitle, CardBody, CardFooter
from .dialog import Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogBody, DialogFooter, DialogClose
# ... etc
```

---

## 9. Documentation Requirements

Every component should have:

1. **Docstring** with description, args, and example
2. **Type hints** for all parameters
3. **Default values** that produce a working component

```python
def Button(
    *children: Any,
    variant: str = "default",
    size: str = "md",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """A clickable button component.
    
    Args:
        *children: Button content (text, icons, other elements)
        variant: Visual style - "default", "primary", "secondary", "ghost", "destructive"
        size: Size variant - "sm", "md", "lg"
        cls: Additional CSS classes to apply
        **attrs: HTML attributes (type, disabled, on_click, etc.)
    
    Returns:
        HtmlString of the rendered button
    
    Example:
        # Basic usage
        Button("Click me")
        
        # With variant and size
        Button("Submit", variant="primary", size="lg")
        
        # With custom classes
        Button("Gradient", cls="bg-gradient-to-r from-blue-500 to-purple-500")
        
        # Form submit
        Button("Save", type="submit")
        
        # With icon
        Button(Icon("plus"), "Add Item", variant="secondary")
    """
```

---

## 10. Checklist for New Components

Before merging a new component, verify:

- [ ] **Semantic class names** (no `uk-*` or framework prefixes)
- [ ] **Data attributes for variants** (`data-variant`, `data-size`, `data-state`)
- [ ] **CSS variables for themeable properties**
- [ ] **`cls` parameter** that merges with base classes
- [ ] **`**attrs` pass-through** for HTML attributes
- [ ] **Sensible defaults** - works with zero configuration
- [ ] **Accessibility** - ARIA attributes, keyboard support
- [ ] **Docstring** with description, args, and examples
- [ ] **Type hints** for all parameters
- [ ] **CSS in components.css** (not inline styles)
- [ ] **Tested** - renders correctly, variants work, customization works

---

## Quick Reference

| Aspect | Pattern |
|--------|---------|
| Class names | Semantic: `btn`, `card`, `dialog-content` |
| Variants | Data attributes: `data-variant="primary"` |
| Theming | CSS variables: `var(--btn-radius)` |
| Class merging | `cn("base", user_cls)` - user wins |
| Interactivity | CSS → Datastar → minimal JS |
| Compound components | Closure pattern for shared state |
| Accessibility | ARIA attributes, keyboard support |

