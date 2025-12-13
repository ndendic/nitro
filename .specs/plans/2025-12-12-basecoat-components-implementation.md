# Basecoat UI Components Implementation Plan

## Overview

Implement 29 remaining Basecoat UI components in the Nitro framework, replacing Basecoat's vanilla JavaScript with Datastar SDK reactivity. Components will use a mixed styling approach (data attributes for theming, cva() for complex layout) with separate CSS files per component.

## Current State Analysis

**Implemented (8 components):**
- Dialog - Native HTML `<dialog>` + minimal JS
- Tabs - Compound component with closure pattern + Datastar signals
- Accordion - Native HTML `<details>`
- Sheet - Datastar signals for open/close state
- Inputs - Basic floating label inputs
- CodeBlock - Static component
- Sidebar - Partial implementation
- Icons - LucideIcon wrapper

**Key Patterns Established:**
- `cn()` for class merging (`utils.py:6-24`)
- `cva()` for variant classes (`utils.py:27-66`)
- Closure pattern for compound components (`tabs.py:63-84`)
- Datastar Signals for reactive state (`sheet.py:20-37`)
- Native HTML elements where possible (`dialog.py:95-99`)

## Datastar SDK Patterns (IMPORTANT)

Components MUST use the type-safe Datastar SDK instead of raw strings.

**Reference**: `docs_app/pages/rustytags.py` for complete examples.

### Signal Creation
```python
from nitro.infrastructure.html.datastar import Signal, Signals

# Named signals object (multiple signals)
form = Signals(name="", email="", accepted=False)

# Standalone signal
counter = Signal("counter", 0)
```

### Two-Way Binding
```python
# ✅ Correct - SDK bind parameter
Input(type="text", bind=form.name)

# ❌ Wrong - raw string
Input(type="text", data_bind="form_name")
```

### Event Handlers
```python
# ✅ Correct - SDK methods
Button("+", on_click=counter.add(1))
Button("-", on_click=counter.sub(1))
Button("Reset", on_click=counter.set(0))
Button("Toggle", on_click=is_open.toggle())

# ❌ Wrong - raw strings
Button("+", on_click="$counter++")
```

### Text Binding
```python
# ✅ Correct - SDK text parameter
Span(text=counter)
P(text="Count: " + counter)
P(text=form.name.upper())

# ❌ Wrong - raw strings
Span(data_text="$counter")
```

### Conditional Display
```python
from nitro.infrastructure.html.datastar import if_, match

# ✅ Correct - SDK expressions
Div("Hidden content", data_show=is_visible)
P(text=if_(score >= 90, "A", if_(score >= 80, "B", "C")))
Div(text=match(status, idle="Ready", loading="Wait...", default="Unknown"))
```

### Dynamic Classes
```python
from nitro.infrastructure.html.datastar import classes

# ✅ Correct - SDK classes helper
Div("Content", data_class=classes(active=is_active, large=is_large))
```

### Logical Operations
```python
from nitro.infrastructure.html.datastar import all_ as all_cond, any_ as any_cond

# Validation example
name_valid = form.name.length >= 3
email_valid = form.email.contains("@")
can_submit = all_cond(name_valid, email_valid, form.accepted)

Button("Submit", data_disabled=~can_submit)
```

## Desired End State

All 37 Basecoat components implemented with:
1. Consistent API following nitro-components skill guidelines
2. Datastar SDK replacing all vanilla JavaScript
3. **Basecoat CSS classes** - components output existing Basecoat class names
4. Users can override/extend styling via `cls` parameter (Tailwind classes)
5. Full accessibility (ARIA attributes, keyboard navigation)
6. **No new CSS files** - use existing `docs_app/static/css/basecoat/components/`

### Verification:
- Each component renders correctly in docs_app with Basecoat styling
- Components output correct Basecoat classes (e.g., `btn-sm-outline`, `badge-secondary`)
- All ARIA attributes present and valid
- Keyboard navigation works (Tab, Enter, Escape, Arrow keys)
- Dark mode theming works via Basecoat CSS variables
- TypeScript/Pyright type hints pass

## What We're NOT Doing

- Server-side form validation (use client-side Datastar)
- Complex animations beyond CSS transitions
- Legacy browser support (using modern CSS like `anchor()`, `:has()`)
- JavaScript-only positioning (CSS anchor positioning where available)
- Custom icon system (using existing LucideIcon wrapper)

## Implementation Approach

**Styling Strategy: Use Existing Basecoat CSS**

Components are **opinionated with Basecoat classes** but allow Tailwind overrides via `cls` parameter.

**Key Insight**: Basecoat CSS already exists at `docs_app/static/css/basecoat/components/`. We don't write new CSS - we output the correct Basecoat class names.

**Basecoat Class Patterns:**

| Component | Pattern | Example Classes |
|-----------|---------|-----------------|
| Button | Combined size+variant | `btn`, `btn-sm-outline`, `btn-lg-destructive` |
| Badge | Variant suffix | `badge`, `badge-secondary`, `badge-outline` |
| Card | Semantic children | `.card` with `header`, `section`, `footer` |
| Field | Context wrapper | `.field` wraps inputs for auto-styling |
| Tooltip | Data attributes | `data-tooltip="text"`, `data-side="top"` |
| Dropdown | ARIA roles | `.dropdown-menu` with `[role='menuitem']` |
| Switch | Role attribute | `input[type='checkbox'][role='switch']` |

**CSS Reference:**
```
docs_app/static/css/basecoat/components/
├── button.css          # .btn, .btn-sm-outline, etc.
├── badge.css           # .badge, .badge-secondary, etc.
├── card.css            # .card with semantic children
├── field.css           # .field wrapper
├── form/
│   ├── checkbox.css    # Styled inside .field or with .input
│   ├── input.css       # Text inputs
│   ├── switch.css      # [role='switch']
│   └── ...
├── dropdown-menu.css   # .dropdown-menu
├── tooltip.css         # [data-tooltip]
└── ...
```

**Component Patterns:**
1. **Simple** - Output Basecoat classes, user `cls` appends (Button, Badge)
2. **Compound** - Closure pattern + Basecoat classes (Tabs, Dropdown)
3. **Reactive** - Datastar signals + Basecoat classes (Sheet, Toast)
4. **Context-based** - Wrapper provides styling context (Field wraps inputs)

---

## Documentation Architecture

Every component MUST have a corresponding documentation page that serves as both documentation and testing ground.

### Documentation Page Location
```
nitro/docs_app/pages/components/
├── button.py
├── card.py
├── badge.py
└── ... (one per component)
```

### Documentation Page Structure

Each documentation page follows this pattern (based on `accordion.py` and `dialog.py`):

```python
"""Component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi import APIRouter
from nitro.infrastructure.html.components import ComponentName

router: APIRouter = APIRouter()


# Example functions - each demonstrates a different use case
def example_basic():
    """Basic usage example."""
    return ComponentName(
        # Basic implementation
    )


def example_with_variants():
    """Show variant options."""
    return Div(
        ComponentName(variant="primary"),
        ComponentName(variant="secondary"),
        ComponentName(variant="ghost"),
    )


def example_interactive():
    """Interactive/reactive example if applicable."""
    return ComponentName(
        # Datastar signals example
    )


@router.get("/components/{component-name}")
@template(title="ComponentName Component Documentation")
def component_docs():
    return Div(
        H1("ComponentName Component"),
        P("Brief description of what this component does."),

        Section(
            "Design Philosophy",
            P("Explain the component's purpose:"),
            Ul(
                Li("Key feature 1"),
                Li("Key feature 2"),
                Li("Accessibility notes"),
                Li("Framework patterns used"),
            ),
        ),

        Section(
            "Basic Usage Demo",
            P("Description of basic usage:"),
            ComponentShowcase(example_basic),
        ),

        Section(
            "Variants Demo",
            P("Available variants:"),
            ComponentShowcase(example_with_variants),
        ),

        # Add more Section blocks for additional demos

        Section(
            "API Reference",
            CodeBlock(
                \"\"\"
def ComponentName(
    *children,
    variant: str = "default",
    size: str = "md",
    cls: str = "",
    **attrs
) -> HtmlString:
    \"\"\"Docstring with args description.\"\"\"
\"\"\",
                code_cls="language-python",
            ),
        ),

        Section(
            "Accessibility",
            Ul(
                Li("ARIA attributes used"),
                Li("Keyboard support"),
                Li("Screen reader behavior"),
            ),
        ),

        BackLink(),
    )
```

### Documentation Requirements

1. **Route**: `/components/{component-name}` (kebab-case)
2. **Minimum 2 examples** showing different use cases
3. **ComponentShowcase** wrapper for Preview/Code tabs
4. **API Reference** section with full function signature
5. **Accessibility** section documenting ARIA and keyboard support
6. **Register router** in `docs_app/main.py`

### Key Utilities from `templates/base.py`

- `@template(title="...")` - Page decorator with sidebar/navbar
- `ComponentShowcase(example_fn)` - Tabs with Preview + Code
- `Section(title, *content)` - Documentation section wrapper
- `BackLink()` - Navigation back to home
- `CodeBlock(code, code_cls="language-python")` - Syntax highlighted code

---

## Phase 0: Foundation (No Reactivity)

### Overview
Pure styling components that establish visual patterns. No Datastar needed. These components output Basecoat CSS classes - no custom CSS files needed.

### Changes Required:

#### 1. Button Component
**File**: `nitro/nitro/infrastructure/html/components/button.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/button.css`

Basecoat button uses combined class names: `btn-{size}-{variant}` or `btn-{variant}` for default size.
- Sizes: `sm`, default (no prefix), `lg`, `icon`
- Variants: `primary` (default), `secondary`, `outline`, `ghost`, `link`, `destructive`
- Examples: `btn` (default), `btn-secondary`, `btn-sm-outline`, `btn-lg-ghost`, `btn-icon-destructive`

```python
from rusty_tags import Button as HTMLButton, HtmlString
from .utils import cn

def _build_btn_class(size: str, variant: str) -> str:
    """Build Basecoat button class from size and variant.

    Pattern: btn, btn-{variant}, btn-{size}, btn-{size}-{variant}
    Default size (md) has no size prefix.
    Default variant (primary) has no variant suffix.
    """
    parts = ["btn"]

    # Add size prefix (sm, lg, icon) - md is default, no prefix
    if size in ("sm", "lg", "icon"):
        parts.append(size)

    # Add variant suffix - primary is default, no suffix
    if variant not in ("default", "primary"):
        parts.append(variant)

    return "-".join(parts)

def Button(
    *children,
    variant: str = "primary",
    size: str = "md",
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Button component with Basecoat variants.

    Args:
        *children: Button content
        variant: primary (default), secondary, ghost, destructive, outline, link
        size: sm, md (default), lg, icon
        disabled: Whether button is disabled
        cls: Additional Tailwind classes to append
        **attrs: HTML attributes

    Examples:
        Button("Click me")                     # btn (primary, md)
        Button("Small", size="sm")             # btn-sm
        Button("Ghost", variant="ghost")       # btn-ghost
        Button("Small Outline", size="sm", variant="outline")  # btn-sm-outline
        Button(LucideIcon("settings"), size="icon")  # btn-icon
    """
    btn_class = _build_btn_class(size, variant)
    return HTMLButton(
        *children,
        cls=cn(btn_class, cls),
        disabled=disabled,
        **attrs
    )
```

**No CSS file needed** - uses existing `basecoat/components/button.css`

#### 2. Card Component
**File**: `nitro/nitro/infrastructure/html/components/card.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/card.css`

Basecoat card uses semantic HTML children for styling:
- `.card` wrapper with `header`, `section`, `footer` children
- `header` contains `h2` (title) and `p` (description)
- `section` for main content
- `footer` for actions

```python
from rusty_tags import Div, Header, Section, Footer, H2, P, HtmlString
from .utils import cn

def Card(*children, cls: str = "", **attrs) -> HtmlString:
    """Card container component using Basecoat styling.

    Uses semantic HTML children: header, section, footer.

    Example:
        Card(
            CardHeader(
                CardTitle("My Card"),
                CardDescription("A description"),
            ),
            CardContent("Main content here"),
            CardFooter(Button("Action")),
        )
    """
    return Div(*children, cls=cn("card", cls), **attrs)

def CardHeader(*children, cls: str = "", **attrs) -> HtmlString:
    """Card header - contains title and description."""
    return Header(*children, cls=cn(cls), **attrs)

def CardTitle(*children, cls: str = "", **attrs) -> HtmlString:
    """Card title (h2 for semantic HTML)."""
    return H2(*children, cls=cn(cls), **attrs)

def CardDescription(*children, cls: str = "", **attrs) -> HtmlString:
    """Card description text."""
    return P(*children, cls=cn(cls), **attrs)

def CardContent(*children, cls: str = "", **attrs) -> HtmlString:
    """Card main content section."""
    return Section(*children, cls=cn(cls), **attrs)

def CardFooter(*children, cls: str = "", **attrs) -> HtmlString:
    """Card footer for actions."""
    return Footer(*children, cls=cn(cls), **attrs)
```

**No CSS file needed** - uses existing `basecoat/components/card.css`

#### 3. Badge Component
**File**: `nitro/nitro/infrastructure/html/components/badge.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/badge.css`

Basecoat badge uses variant suffix pattern:
- `.badge` or `.badge-primary` (default)
- `.badge-secondary`, `.badge-destructive`, `.badge-outline`

```python
from rusty_tags import Span, HtmlString
from .utils import cn

def Badge(
    *children,
    variant: str = "primary",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Badge component for labels and status indicators.

    Args:
        *children: Badge content
        variant: primary (default), secondary, destructive, outline
        cls: Additional Tailwind classes
        **attrs: HTML attributes

    Examples:
        Badge("New")                          # badge (primary)
        Badge("Draft", variant="secondary")   # badge-secondary
        Badge("Error", variant="destructive") # badge-destructive
    """
    badge_class = "badge" if variant in ("default", "primary") else f"badge-{variant}"
    return Span(*children, cls=cn(badge_class, cls), **attrs)
```

**No CSS file needed** - uses existing `basecoat/components/badge.css`

#### 4. Label Component
**File**: `nitro/nitro/infrastructure/html/components/label.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/form/label.css`

Basecoat label is context-based (auto-styled inside `.field` or `.form`) or explicit with `.label` class.

```python
from rusty_tags import Label as HTMLLabel, Span, HtmlString
from .utils import cn

def Label(
    *children,
    for_id: str = "",
    required: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Label component for form inputs.

    Note: Labels inside Field component are auto-styled by Basecoat.
    Use this for standalone labels outside of Field.

    Args:
        *children: Label content
        for_id: ID of the input this label is for
        required: Show required indicator (*)
        cls: Additional Tailwind classes
        **attrs: HTML attributes
    """
    content = [*children]
    if required:
        content.append(Span(" *", cls="text-destructive"))

    return HTMLLabel(
        *content,
        htmlFor=for_id if for_id else None,
        cls=cn("label", cls),
        **attrs
    )
```

**No CSS file needed** - uses existing `basecoat/components/form/label.css`

#### 5. Alert Component
**File**: `nitro/nitro/infrastructure/html/components/alert.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/alert.css`

Basecoat alert uses variant suffix pattern:
- `.alert` (default)
- `.alert-destructive`
- Uses semantic children: `h2/h3` for title, `section` for description

```python
from rusty_tags import Div, H3, Section, P, HtmlString
from .utils import cn

def Alert(
    *children,
    variant: str = "default",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Alert component for contextual messages.

    Args:
        *children: Alert content (use AlertTitle and AlertDescription)
        variant: default, destructive
        cls: Additional Tailwind classes
        **attrs: HTML attributes

    Example:
        Alert(
            LucideIcon("info"),
            AlertTitle("Heads up!"),
            AlertDescription("You can add components to your app."),
        )
    """
    alert_class = "alert" if variant == "default" else f"alert-{variant}"
    return Div(*children, cls=cn(alert_class, cls), role="alert", **attrs)

def AlertTitle(*children, cls: str = "", **attrs) -> HtmlString:
    """Alert title element (h3)."""
    return H3(*children, cls=cn(cls), **attrs)

def AlertDescription(*children, cls: str = "", **attrs) -> HtmlString:
    """Alert description section."""
    return Section(P(*children), cls=cn(cls), **attrs)
```

**No CSS file needed** - uses existing `basecoat/components/alert.css`

#### 6. Kbd Component
**File**: `nitro/nitro/infrastructure/html/components/kbd.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/kbd.css`

```python
from rusty_tags import Kbd as HTMLKbd, HtmlString
from .utils import cn

def Kbd(*children, cls: str = "", **attrs) -> HtmlString:
    """Keyboard key component for displaying shortcuts.

    Example:
        Kbd("⌘"), Kbd("K")  # For ⌘K shortcut
    """
    return HTMLKbd(*children, cls=cn("kbd", cls), **attrs)
```

**No CSS file needed** - uses existing `basecoat/components/kbd.css`

#### 7. Spinner Component
**File**: `nitro/nitro/infrastructure/html/components/spinner.py`

**Note**: No Basecoat CSS - uses Tailwind animate classes.

```python
from rusty_tags import Div, HtmlString
from .utils import cn
from .icons import LucideIcon

def Spinner(size: str = "md", cls: str = "", **attrs) -> HtmlString:
    """Loading spinner component using Lucide loader icon.

    Args:
        size: sm (16px), md (24px), lg (32px)
        cls: Additional Tailwind classes
        **attrs: HTML attributes

    Example:
        Spinner()
        Spinner(size="lg", cls="text-primary")
    """
    sizes = {"sm": "size-4", "md": "size-6", "lg": "size-8"}
    size_class = sizes.get(size, "size-6")

    return Div(
        LucideIcon("loader-2", cls=cn(size_class, "animate-spin")),
        cls=cn("inline-flex items-center justify-center", cls),
        role="status",
        aria_label="Loading",
        **attrs
    )
```

**No CSS file needed** - uses Tailwind's built-in `animate-spin`

#### 8. Skeleton Component
**File**: `nitro/nitro/infrastructure/html/components/skeleton.py`

**Note**: No Basecoat CSS - uses Tailwind animate-pulse.

```python
from rusty_tags import Div, HtmlString
from .utils import cn

def Skeleton(cls: str = "", **attrs) -> HtmlString:
    """Skeleton loading placeholder component.

    Args:
        cls: Tailwind classes for sizing (e.g., "h-4 w-[200px]")
        **attrs: HTML attributes

    Example:
        Skeleton(cls="h-4 w-[250px]")  # Text line
        Skeleton(cls="h-12 w-12 rounded-full")  # Avatar
        Skeleton(cls="h-[125px] w-[250px] rounded-xl")  # Card
    """
    return Div(
        cls=cn("animate-pulse rounded-md bg-muted", cls),
        aria_hidden="true",
        **attrs
    )
```

**No CSS file needed** - uses Tailwind's built-in `animate-pulse`

#### 9. CSS Note
**No new CSS files needed** - All P0 components use existing Basecoat CSS.

Ensure `basecoat.css` or individual component CSS files are imported in your app's CSS entry point:
```css
/* In your input.css or main stylesheet */
@import "basecoat/basecoat.css";  /* or basecoat.all.css for everything */
```

#### 10. Update Component Exports
**File**: `nitro/nitro/infrastructure/html/components/__init__.py`

Add new exports:
```python
from .button import Button
from .card import Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
from .badge import Badge
from .label import Label
from .alert import Alert, AlertTitle, AlertDescription
from .kbd import Kbd
from .spinner import Spinner
from .skeleton import Skeleton
```

#### 11. Documentation Pages (Phase 0)

Create documentation pages for each P0 component:

**Files to create:**
- `nitro/docs_app/pages/components/button.py`
- `nitro/docs_app/pages/components/card.py`
- `nitro/docs_app/pages/components/badge.py`
- `nitro/docs_app/pages/components/label.py`
- `nitro/docs_app/pages/components/alert.py`
- `nitro/docs_app/pages/components/kbd.py`
- `nitro/docs_app/pages/components/spinner.py`
- `nitro/docs_app/pages/components/skeleton.py`

**Example: Button Documentation Page**
**File**: `nitro/docs_app/pages/components/button.py`

```python
"""Button component documentation page"""

from ..templates.base import *  # noqa: F403
from fastapi import APIRouter
from nitro.infrastructure.html.components import Button

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Button("Default Button"),
        Button("Primary", variant="primary"),
        Button("Secondary", variant="secondary"),
        cls="flex gap-2 flex-wrap"
    )


def example_sizes():
    return Div(
        Button("Small", size="sm"),
        Button("Medium", size="md"),
        Button("Large", size="lg"),
        Button(LucideIcon("settings"), size="icon"),
        cls="flex gap-2 items-center"
    )


def example_variants():
    return Div(
        Button("Default", variant="default"),
        Button("Primary", variant="primary"),
        Button("Secondary", variant="secondary"),
        Button("Ghost", variant="ghost"),
        Button("Destructive", variant="destructive"),
        Button("Outline", variant="outline"),
        Button("Link", variant="link"),
        cls="flex gap-2 flex-wrap"
    )


def example_disabled():
    return Div(
        Button("Disabled", disabled=True),
        Button("Disabled Primary", variant="primary", disabled=True),
        cls="flex gap-2"
    )


@router.get("/components/button")
@template(title="Button Component Documentation")
def button_docs():
    return Div(
        H1("Button Component"),
        P("Buttons trigger actions and navigation. Available in multiple variants and sizes."),

        Section(
            "Design Philosophy",
            P("This component follows our design principles:"),
            Ul(
                Li("🎨 Basecoat CSS classes for styling (btn-sm-outline, etc.)"),
                Li("📐 Size via class (sm, md, lg, icon)"),
                Li("♿️ Native button element for accessibility"),
                Li("🔗 cls parameter for Tailwind overrides"),
            ),
        ),

        Section(
            "Basic Usage",
            P("Buttons in different variants:"),
            ComponentShowcase(example_basic),
        ),

        Section(
            "All Variants",
            P("Available button variants:"),
            ComponentShowcase(example_variants),
        ),

        Section(
            "Sizes",
            P("Button size options:"),
            ComponentShowcase(example_sizes),
        ),

        Section(
            "Disabled State",
            P("Disabled buttons:"),
            ComponentShowcase(example_disabled),
        ),

        Section(
            "API Reference",
            CodeBlock(
                \"\"\"
def Button(
    *children,
    variant: str = "default",  # default, primary, secondary, ghost, destructive, outline, link
    size: str = "md",          # sm, md, lg, icon
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
    \"\"\"Button component with variants.\"\"\"
\"\"\",
                code_cls="language-python",
            ),
        ),

        Section(
            "Accessibility",
            Ul(
                Li("Uses native <button> element"),
                Li("Disabled state communicated via disabled attribute"),
                Li("Focus visible styling for keyboard navigation"),
            ),
        ),

        BackLink(),
    )
```

### Success Criteria:

#### Automated Verification:
- [ ] All Python files pass pyright: `pyright nitro/nitro/infrastructure/html/components/`
- [ ] No import errors: `python -c "from nitro.infrastructure.html.components import Button, Card, Badge"`
- [ ] Documentation pages render without errors

#### Manual Verification:
- [ ] Each component renders correctly in browser with Basecoat styling
- [ ] Button outputs correct Basecoat classes (btn, btn-secondary, btn-sm-outline, etc.)
- [ ] Dark mode works (Basecoat uses CSS variables)
- [ ] Components are accessible (screen reader announces correctly)
- [ ] Documentation pages accessible at `/components/{name}`
- [ ] ComponentShowcase shows Preview/Code tabs correctly

**Implementation Note**: After completing Phase 0, verify all components render in docs_app before proceeding.

---

## Phase 1: Form Controls (Two-way Binding)

### Overview
Form input components using Datastar's `data_bind` for two-way binding. All form components use Basecoat's context-based styling.

**Basecoat Form Pattern**: Inputs inside `.field` wrapper are automatically styled. For standalone inputs, use the `.input` class prefix.

### Changes Required:

#### 1. Checkbox Component
**File**: `nitro/nitro/infrastructure/html/components/checkbox.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/form/checkbox.css`

Basecoat checkbox is context-based: styled inside `.field` or with `.input[type='checkbox']`.

```python
from rusty_tags import Input, Label as HTMLLabel, Div, HtmlString
from nitro.infrastructure.html.datastar import Signal
from .utils import cn

def Checkbox(
    *children,
    id: str,
    bind: Signal = None,
    checked: bool = False,
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Checkbox input with Datastar binding.

    Note: When used inside Field component, checkbox is auto-styled.
    Standalone checkboxes use .input class.

    Args:
        *children: Label content (optional)
        id: Input ID (required for accessibility)
        bind: Datastar Signal for two-way binding
        checked: Initial checked state (used if no bind signal)
        disabled: Whether checkbox is disabled
        cls: Additional Tailwind classes
        **attrs: HTML attributes

    Example:
        from nitro.infrastructure.html.datastar import Signal, Signals

        # With Signals object
        form = Signals(accepted=False)
        Field(
            Checkbox("Accept terms", id="terms", bind=form.accepted),
        )

        # With standalone Signal
        accepted = Signal("accepted", False)
        Checkbox("I agree", id="agree", bind=accepted)
    """
    checkbox_input = Input(
        type="checkbox",
        id=id,
        bind=bind,  # Uses SDK bind parameter
        checked=checked if bind is None else None,
        disabled=disabled,
        cls=cn("input", cls),  # .input triggers Basecoat styling
        **attrs
    )

    if children:
        return Div(
            checkbox_input,
            HTMLLabel(*children, htmlFor=id),
            cls="flex items-center gap-2",
        )

    return checkbox_input
```

**No CSS file needed** - uses existing `basecoat/components/form/checkbox.css`

#### 2. Radio Group Component
**File**: `nitro/nitro/infrastructure/html/components/radio.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/form/radio.css`

Basecoat radio is context-based: styled inside `.field` or with `.input[type='radio']`.

```python
from rusty_tags import Div, Input, Label as HTMLLabel, HtmlString
from nitro.infrastructure.html.datastar import Signal, Signals
from .utils import cn

def RadioGroup(
    *children,
    bind: Signal,
    orientation: str = "vertical",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Radio group container with Datastar signal.

    Uses compound component pattern - RadioItem receives signal via closure.

    Args:
        *children: RadioItem components
        bind: Datastar Signal for selected value
        orientation: vertical (default) or horizontal
        cls: Additional Tailwind classes
        **attrs: HTML attributes

    Example:
        from nitro.infrastructure.html.datastar import Signals

        form = Signals(size="md")

        RadioGroup(
            RadioItem("Small", value="sm"),
            RadioItem("Medium", value="md"),
            RadioItem("Large", value="lg"),
            bind=form.size,
        )
    """
    processed = [
        child(bind) if callable(child) else child
        for child in children
    ]

    flex_dir = "flex-col" if orientation == "vertical" else "flex-row"

    return Div(
        *processed,
        role="radiogroup",
        cls=cn("flex gap-3", flex_dir, cls),
        **attrs
    )

def RadioItem(
    *children,
    value: str,
    id: str = "",
    disabled: bool = False,
    cls: str = "",
    **attrs
):
    """Individual radio option (closure pattern).

    Receives Signal from parent RadioGroup via closure.
    """
    def create(bind: Signal):
        item_id = id or f"radio_{value}"
        return Div(
            Input(
                type="radio",
                id=item_id,
                value=value,
                bind=bind,  # Uses SDK bind parameter
                disabled=disabled,
                cls="input",  # Triggers Basecoat styling
            ),
            HTMLLabel(*children, htmlFor=item_id),
            cls=cn("flex items-center gap-2", cls),
            **attrs
        )
    return create
```

**No CSS file needed** - uses existing `basecoat/components/form/radio.css`

#### 3. Switch Component
**File**: `nitro/nitro/infrastructure/html/components/switch.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/form/switch.css`

Basecoat switch uses `input[type='checkbox'][role='switch']` pattern - a checkbox with role="switch".

```python
from rusty_tags import Input, Label as HTMLLabel, Div, HtmlString
from nitro.infrastructure.html.datastar import Signal
from .utils import cn

def Switch(
    *children,
    id: str,
    bind: Signal = None,
    checked: bool = False,
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Toggle switch component with Datastar binding.

    Uses native checkbox with role="switch" for Basecoat styling.

    Args:
        *children: Label content (optional)
        id: Input ID (required)
        bind: Datastar Signal for two-way binding
        checked: Initial checked state (used if no bind signal)
        disabled: Whether switch is disabled
        cls: Additional Tailwind classes
        **attrs: HTML attributes

    Example:
        from nitro.infrastructure.html.datastar import Signals

        settings = Signals(notifications=True, dark_mode=False)

        Switch("Enable notifications", id="notifications", bind=settings.notifications)
        Switch("Dark mode", id="dark", bind=settings.dark_mode)
    """
    switch_input = Input(
        type="checkbox",
        role="switch",
        id=id,
        bind=bind,  # Uses SDK bind parameter
        checked=checked if bind is None else None,
        disabled=disabled,
        cls=cn("input", cls),  # .input triggers Basecoat styling
        **attrs
    )

    if children:
        return Div(
            switch_input,
            HTMLLabel(*children, htmlFor=id),
            cls="flex items-center gap-2",
        )

    return switch_input
```

**No CSS file needed** - uses existing `basecoat/components/form/switch.css`

#### 4. Select Component
**File**: `nitro/nitro/infrastructure/html/components/select.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/form/select.css`

Basecoat select is context-based: styled inside `.field` or with `.input` class.

```python
from rusty_tags import Select as HTMLSelect, Option, HtmlString
from nitro.infrastructure.html.datastar import Signal
from .utils import cn

def Select(
    *children,
    id: str,
    bind: Signal = None,
    placeholder: str = "Select...",
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Native select component with Datastar binding.

    Args:
        *children: SelectOption components
        id: Input ID (required)
        bind: Datastar Signal for selected value
        placeholder: Placeholder text
        disabled: Whether select is disabled
        cls: Additional Tailwind classes
        **attrs: HTML attributes

    Example:
        from nitro.infrastructure.html.datastar import Signals

        form = Signals(size="md")

        Field(
            Select(
                SelectOption("Small", value="sm"),
                SelectOption("Medium", value="md"),
                SelectOption("Large", value="lg"),
                id="size",
                bind=form.size,
            ),
            label="Size",
            label_for="size",
        )
    """
    options = [
        Option(placeholder, value="", disabled=True, selected=True) if placeholder else None,
        *children
    ]

    return HTMLSelect(
        *[o for o in options if o],
        id=id,
        bind=bind,  # Uses SDK bind parameter
        disabled=disabled,
        cls=cn("input", cls),  # .input triggers Basecoat styling
        **attrs
    )

def SelectOption(*children, value: str, disabled: bool = False, **attrs) -> HtmlString:
    """Option for Select component."""
    return Option(*children, value=value, disabled=disabled, **attrs)
```

**No CSS file needed** - uses existing `basecoat/components/form/select.css`

#### 5. Textarea Component
**File**: `nitro/nitro/infrastructure/html/components/textarea.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/form/textarea.css`

Basecoat textarea is context-based: styled inside `.field` or with `.input` class.

```python
from rusty_tags import Textarea as HTMLTextarea, HtmlString
from nitro.infrastructure.html.datastar import Signal
from .utils import cn

def Textarea(
    *children,
    id: str,
    bind: Signal = None,
    placeholder: str = "",
    rows: int = 3,
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Textarea component with Datastar binding.

    Args:
        *children: Initial content (optional)
        id: Input ID (required)
        bind: Datastar Signal for two-way binding
        placeholder: Placeholder text
        rows: Number of visible text lines
        disabled: Whether textarea is disabled
        cls: Additional Tailwind classes
        **attrs: HTML attributes

    Example:
        from nitro.infrastructure.html.datastar import Signals

        form = Signals(bio="")

        Field(
            Textarea(id="bio", bind=form.bio, placeholder="Tell us about yourself..."),
            label="Bio",
            label_for="bio",
        )
    """
    return HTMLTextarea(
        *children,
        id=id,
        bind=bind,  # Uses SDK bind parameter
        placeholder=placeholder,
        rows=rows,
        disabled=disabled,
        cls=cn("input", cls),  # .input triggers Basecoat styling
        **attrs
    )
```

**No CSS file needed** - uses existing `basecoat/components/form/textarea.css`

#### 6. Field Component
**File**: `nitro/nitro/infrastructure/html/components/field.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/field.css`

Basecoat Field uses `.field` class which provides context-based styling for all child form inputs. Uses semantic children: `h2/h3` for title, `p` for description, `[role="alert"]` for errors.

```python
from rusty_tags import Div, H3, P, HtmlString
from .utils import cn

def Field(
    *children,
    label: str = "",
    label_for: str = "",
    error: str = "",
    description: str = "",
    orientation: str = "vertical",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Form field wrapper providing Basecoat context styling.

    All inputs inside Field are automatically styled by Basecoat.

    Args:
        *children: Form inputs (Checkbox, Select, Input, etc.)
        label: Field label text
        label_for: ID of the input this label is for
        error: Error message (shown in destructive color)
        description: Help text
        orientation: vertical (default) or horizontal
        cls: Additional Tailwind classes
        **attrs: HTML attributes

    Example:
        from nitro.infrastructure.html.datastar import Signals

        form = Signals(email="")

        Field(
            Input(type="email", id="email", bind=form.email),
            label="Email",
            label_for="email",
            description="We'll never share your email.",
        )
    """
    return Div(
        H3(label, htmlFor=label_for) if label else None,
        P(description) if description else None,
        *children,
        Div(error, role="alert") if error else None,
        cls=cn("field", cls),
        data_orientation=orientation if orientation != "vertical" else None,
        data_invalid="true" if error else None,
        **attrs
    )
```

**No CSS file needed** - uses existing `basecoat/components/field.css`

#### 7. Input Group Component
**File**: `nitro/nitro/infrastructure/html/components/input_group.py`

**Note**: No Basecoat CSS - uses Tailwind classes for layout.

```python
from rusty_tags import Div, Span, HtmlString
from .utils import cn

def InputGroup(*children, cls: str = "", **attrs) -> HtmlString:
    """Container for input with prefix/suffix elements.

    Example:
        InputGroup(
            InputPrefix("$"),
            Input(type="number", id="price"),
            InputSuffix(".00"),
        )
    """
    return Div(
        *children,
        cls=cn("flex items-stretch [&>*:first-child]:rounded-l-md [&>*:last-child]:rounded-r-md [&>input]:rounded-none [&>input]:flex-1", cls),
        **attrs
    )

def InputPrefix(*children, cls: str = "", **attrs) -> HtmlString:
    """Prefix element for InputGroup."""
    return Span(
        *children,
        cls=cn("flex items-center px-3 bg-muted border border-r-0 border-input text-sm text-muted-foreground", cls),
        **attrs
    )

def InputSuffix(*children, cls: str = "", **attrs) -> HtmlString:
    """Suffix element for InputGroup."""
    return Span(
        *children,
        cls=cn("flex items-center px-3 bg-muted border border-l-0 border-input text-sm text-muted-foreground", cls),
        **attrs
    )
```

**No CSS file needed** - uses Tailwind utility classes

#### 8. CSS Note
**No new CSS files needed** - All P1 form components use existing Basecoat CSS in `basecoat/components/form/`.

#### 9. Documentation Pages (Phase 1)

**Files to create:**
- `nitro/docs_app/pages/components/checkbox.py`
- `nitro/docs_app/pages/components/radio.py`
- `nitro/docs_app/pages/components/switch.py`
- `nitro/docs_app/pages/components/select.py`
- `nitro/docs_app/pages/components/textarea.py`
- `nitro/docs_app/pages/components/field.py`
- `nitro/docs_app/pages/components/input-group.py`

Each must include:
- Examples showing Datastar `data_bind` usage
- Signal state visualization
- Form integration examples

### Success Criteria:

#### Automated Verification:
- [ ] Pyright passes for all form components
- [ ] Components import without errors
- [ ] Documentation pages render without errors

#### Manual Verification:
- [ ] Checkbox toggles and signal updates
- [ ] Radio group only allows one selection
- [ ] Switch animates smoothly
- [ ] Select dropdown works with Datastar binding
- [ ] Field shows error state correctly
- [ ] Keyboard navigation works (Tab, Space, Enter)
- [ ] Documentation pages show signal state changes in Preview

---

## Phase 2: Interactive Overlays

### Overview
Dropdown, Popover, and Tooltip using Datastar signals for visibility and positioning.

### Basecoat CSS Approach
**Same principle as P0/P1**: Use existing Basecoat CSS classes. Reference:
- `basecoat/components/dropdown-menu.css` - `.dropdown-menu` with `[role='menuitem']`
- `basecoat/components/popover.css` - `.popover`
- `basecoat/components/tooltip.css` - `[data-tooltip]` with `data-side`, `data-align`
- `basecoat/components/dialog.css` - Alert dialog styling

**Key Pattern Changes for Phase 2 Components:**
- Components output Basecoat class names, NOT custom CSS
- Remove all `**CSS File**:` sections and custom CSS blocks
- Use `.dropdown-menu`, `.popover`, `[data-tooltip]` classes as defined in Basecoat

### Changes Required:

#### 1. Dropdown Menu Component
**File**: `nitro/nitro/infrastructure/html/components/dropdown.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/dropdown-menu.css`

Uses compound component pattern with Signal passed via closure.

```python
from rusty_tags import Div, Button, HtmlString
from nitro.infrastructure.html.datastar import Signal, Signals
from .utils import cn, uniq

def DropdownMenu(
    *children,
    id: str = "",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Dropdown menu container with Datastar signals.

    Uses compound component pattern - children receive Signal via closure.

    Example:
        DropdownMenu(
            DropdownTrigger(Button("Options", variant="outline")),
            DropdownContent(
                DropdownItem("Edit", on_click=handle_edit),
                DropdownItem("Delete", on_click=handle_delete),
            ),
        )
    """
    menu_id = id or f"dropdown_{uniq()}"
    open_signal = Signal(f"{menu_id}_open", False)

    processed = [
        child(open_signal) if callable(child) else child
        for child in children
    ]

    return Div(
        *processed,
        signals={open_signal.name: False},
        cls=cn("dropdown-menu", cls),  # Basecoat class
        data_on_click_outside=open_signal.set(False),
        data_on_keydown_escape=open_signal.set(False),
        **attrs
    )

def DropdownTrigger(*children, cls: str = "", **attrs):
    """Trigger button for dropdown."""
    def create(open_signal: Signal):
        return Button(
            *children,
            on_click=open_signal.toggle(),  # SDK toggle method
            cls=cn(cls),
            aria_haspopup="menu",
            data_attr_aria_expanded=open_signal,  # SDK dynamic attribute
            **attrs
        )
    return create

def DropdownContent(*children, align: str = "start", cls: str = "", **attrs):
    """Dropdown content panel."""
    def create(open_signal: Signal):
        return Div(
            *children,
            data_show=open_signal,  # SDK show binding
            role="menu",
            cls=cn("dropdown-content", cls),
            data_align=align,
            **attrs
        )
    return create

def DropdownItem(
    *children,
    on_click=None,  # Can be Signal action or string
    disabled: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Individual dropdown menu item."""
    return Button(
        *children,
        on_click=on_click,
        role="menuitem",
        disabled=disabled,
        cls=cn(cls),  # Uses Basecoat [role='menuitem'] styling
        **attrs
    )

def DropdownSeparator(cls: str = "", **attrs) -> HtmlString:
    """Separator between dropdown items."""
    return Div(cls=cn("dropdown-separator", cls), role="separator", **attrs)
```

**No CSS file needed** - uses existing `basecoat/components/dropdown-menu.css`

#### 2. Popover Component
**File**: `nitro/nitro/infrastructure/html/components/popover.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/popover.css`

Uses compound component pattern with Signal passed via closure.

```python
from rusty_tags import Div, Button, HtmlString
from nitro.infrastructure.html.datastar import Signal
from .utils import cn, uniq

def Popover(
    *children,
    id: str = "",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Popover container for positioned overlays.

    Uses compound component pattern - children receive Signal via closure.

    Example:
        Popover(
            PopoverTrigger(Button("Open Popover")),
            PopoverContent(
                H4("Settings"),
                P("Configure your preferences here."),
            ),
        )
    """
    popover_id = id or f"popover_{uniq()}"
    open_signal = Signal(f"{popover_id}_open", False)

    processed = [
        child(open_signal) if callable(child) else child
        for child in children
    ]

    return Div(
        *processed,
        signals={open_signal.name: False},
        cls=cn("popover", cls),  # Basecoat class
        data_on_click_outside=open_signal.set(False),
        data_on_keydown_escape=open_signal.set(False),
        **attrs
    )

def PopoverTrigger(*children, cls: str = "", **attrs):
    """Trigger for popover."""
    def create(open_signal: Signal):
        return Button(
            *children,
            on_click=open_signal.toggle(),  # SDK toggle
            cls=cn(cls),
            aria_haspopup="dialog",
            data_attr_aria_expanded=open_signal,  # SDK dynamic attribute
            **attrs
        )
    return create

def PopoverContent(
    *children,
    side: str = "bottom",
    align: str = "center",
    cls: str = "",
    **attrs
):
    """Popover content panel."""
    def create(open_signal: Signal):
        return Div(
            *children,
            data_show=open_signal,  # SDK show binding
            role="dialog",
            cls=cn("popover-content", cls),
            data_side=side,
            data_align=align,
            **attrs
        )
    return create
```

**No CSS file needed** - uses existing `basecoat/components/popover.css`

#### 3. Tooltip Component
**File**: `nitro/nitro/infrastructure/html/components/tooltip.py`

**Basecoat CSS Reference**: `docs_app/static/css/basecoat/components/tooltip.css`

Basecoat tooltip uses `data-tooltip` attribute pattern - pure CSS, no JavaScript needed!

```python
from rusty_tags import Span, HtmlString
from .utils import cn

def Tooltip(
    *children,
    content: str,
    side: str = "top",
    align: str = "center",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Pure CSS tooltip using Basecoat data-tooltip pattern.

    No JavaScript/Datastar needed - tooltip appears on hover via CSS.

    Args:
        *children: Element to attach tooltip to
        content: Tooltip text
        side: top (default), bottom, left, right
        align: center (default), start, end
        cls: Additional Tailwind classes
        **attrs: HTML attributes

    Example:
        Tooltip(
            Button("Hover me"),
            content="This is a tooltip!",
            side="bottom",
        )

        # Can wrap any element
        Tooltip(
            LucideIcon("info"),
            content="More information",
            side="right",
        )
    """
    # Basecoat tooltip wraps content and uses data attributes
    return Span(
        *children,
        data_tooltip=content,  # Basecoat pattern
        data_side=side,
        data_align=align,
        cls=cn(cls),
        **attrs
    )
```

**No CSS file needed** - uses existing `basecoat/components/tooltip.css`
**No JavaScript needed** - Basecoat tooltip is pure CSS

#### 4. Alert Dialog Component
**File**: `nitro/nitro/infrastructure/html/components/alert_dialog.py`

```python
from rusty_tags import Dialog as NativeDialog, Div, H2, P, Button, HtmlString
from .utils import cn

def AlertDialog(
    *children,
    id: str,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Alert dialog for confirmations."""
    return NativeDialog(
        Div(*children, cls="alert-dialog-content"),
        id=id,
        cls=cn("alert-dialog", cls),
        aria_modal="true",
        role="alertdialog",
        **attrs
    )

def AlertDialogTrigger(*children, dialog_id: str, cls: str = "", **attrs) -> HtmlString:
    """Trigger button for alert dialog."""
    return Button(
        *children,
        on_click=f"document.getElementById('{dialog_id}').showModal()",
        cls=cn("alert-dialog-trigger", cls),
        aria_haspopup="dialog",
        **attrs
    )

def AlertDialogHeader(*children, cls: str = "", **attrs) -> HtmlString:
    return Div(*children, cls=cn("alert-dialog-header", cls), **attrs)

def AlertDialogTitle(*children, cls: str = "", **attrs) -> HtmlString:
    return H2(*children, cls=cn("alert-dialog-title", cls), **attrs)

def AlertDialogDescription(*children, cls: str = "", **attrs) -> HtmlString:
    return P(*children, cls=cn("alert-dialog-description", cls), **attrs)

def AlertDialogFooter(*children, cls: str = "", **attrs) -> HtmlString:
    return Div(*children, cls=cn("alert-dialog-footer", cls), **attrs)

def AlertDialogAction(*children, dialog_id: str, on_click: str = "", cls: str = "", **attrs) -> HtmlString:
    """Action button that closes dialog after action."""
    click_handler = f"{on_click}; document.getElementById('{dialog_id}').close()" if on_click else f"document.getElementById('{dialog_id}').close()"
    return Button(
        *children,
        on_click=click_handler,
        cls=cn("alert-dialog-action", cls),
        **attrs
    )

def AlertDialogCancel(*children, dialog_id: str, cls: str = "", **attrs) -> HtmlString:
    """Cancel button that closes dialog."""
    return Button(
        *children,
        on_click=f"document.getElementById('{dialog_id}').close()",
        cls=cn("alert-dialog-cancel", cls),
        **attrs
    )
```

**CSS File**: `nitro/nitro/infrastructure/html/css/components/alert-dialog.css`

```css
.alert-dialog {
  max-width: 32rem;
  padding: 0;
  border: none;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);

  &::backdrop {
    background: rgba(0, 0, 0, 0.5);
  }
}

.alert-dialog-content {
  padding: 1.5rem;
}

.alert-dialog-header {
  text-align: center;
}

.alert-dialog-title {
  font-size: 1.125rem;
  font-weight: 600;
}

.alert-dialog-description {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-muted-foreground);
}

.alert-dialog-footer {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.alert-dialog-action {
  /* Primary button styling */
}

.alert-dialog-cancel {
  /* Ghost/outline button styling */
}
```

#### 5. Documentation Pages (Phase 2)

**Files to create:**
- `nitro/docs_app/pages/components/dropdown.py`
- `nitro/docs_app/pages/components/popover.py`
- `nitro/docs_app/pages/components/tooltip.py`
- `nitro/docs_app/pages/components/alert-dialog.py`

Each must include:
- Examples showing open/close behavior
- Positioning options (side, align)
- Click-outside and Escape key demos

### Success Criteria:

#### Automated Verification:
- [ ] Pyright passes for all interactive components
- [ ] No import errors
- [ ] Documentation pages render without errors

#### Manual Verification:
- [ ] Dropdown opens/closes on trigger click
- [ ] Click outside closes dropdown/popover
- [ ] Escape key closes overlays
- [ ] Tooltip appears on hover with delay
- [ ] Alert dialog blocks background interaction
- [ ] Focus is trapped in alert dialog
- [ ] Documentation pages demonstrate all interaction patterns

---

## Phase 3: Feedback Components

### Overview
Toast notifications, Progress indicators, and loading states.

### Basecoat CSS Approach
**Same principle**: Use existing Basecoat CSS where available. Reference:
- `basecoat/components/toast.css` - Toast notifications
- Progress/Skeleton: No Basecoat CSS - use Tailwind utilities (`animate-pulse`, `bg-muted`)

**Key Pattern Changes:**
- Toast outputs Basecoat `.toast` classes
- Progress uses Tailwind `bg-primary rounded-full` pattern
- Remove custom CSS blocks

### Changes Required:

#### 1. Toast System
**File**: `nitro/nitro/infrastructure/html/components/toast.py`

```python
from rusty_tags import Div, Button, H4, P, HtmlString
from rusty_tags.datastar import Signals
from .utils import cn
from .icons import LucideIcon

def ToastProvider(
    *children,
    position: str = "bottom-right",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Container for toast notifications."""
    return Div(
        *children,
        Div(id="toast-container", cls="toast-container", data_position=position),
        signals=Signals(toasts=[]),
        cls=cn("toast-provider", cls),
        **attrs
    )

def Toast(
    *children,
    id: str,
    title: str = "",
    description: str = "",
    variant: str = "default",
    duration: int = 5000,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Individual toast notification."""
    return Div(
        Div(
            LucideIcon("x", cls="toast-close-icon") if True else None,
            on_click=f"this.parentElement.remove()",
            cls="toast-close",
        ) if True else None,
        H4(title, cls="toast-title") if title else None,
        P(description, cls="toast-description") if description else None,
        *children,
        id=id,
        role="alert",
        cls=cn("toast", cls),
        data_variant=variant,
        data_on_load=f"setTimeout(() => this.remove(), {duration})" if duration > 0 else None,
        **attrs
    )
```

**CSS File**: `nitro/nitro/infrastructure/html/css/components/toast.css`

```css
.toast-container {
  position: fixed;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 24rem;

  &[data-position="top-left"] { top: 1rem; left: 1rem; }
  &[data-position="top-center"] { top: 1rem; left: 50%; transform: translateX(-50%); }
  &[data-position="top-right"] { top: 1rem; right: 1rem; }
  &[data-position="bottom-left"] { bottom: 1rem; left: 1rem; }
  &[data-position="bottom-center"] { bottom: 1rem; left: 50%; transform: translateX(-50%); }
  &[data-position="bottom-right"] { bottom: 1rem; right: 1rem; }
}

.toast {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 1rem;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  animation: toast-enter 200ms ease-out;

  &[data-variant="success"] {
    border-left: 4px solid var(--color-green-500);
  }
  &[data-variant="error"] {
    border-left: 4px solid var(--color-red-500);
  }
  &[data-variant="warning"] {
    border-left: 4px solid var(--color-yellow-500);
  }
  &[data-variant="info"] {
    border-left: 4px solid var(--color-blue-500);
  }
}

.toast-close {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  padding: 0.25rem;
  background: transparent;
  border: none;
  cursor: pointer;
  opacity: 0.5;

  &:hover { opacity: 1; }
}

.toast-title {
  font-weight: 600;
  font-size: 0.875rem;
}

.toast-description {
  font-size: 0.8125rem;
  color: var(--color-muted-foreground);
}

@keyframes toast-enter {
  from {
    opacity: 0;
    transform: translateY(1rem);
  }
}
```

#### 2. Progress Component
**File**: `nitro/nitro/infrastructure/html/components/progress.py`

```python
from rusty_tags import Div, HtmlString
from .utils import cn

def Progress(
    value: int = 0,
    max_value: int = 100,
    indeterminate: bool = False,
    size: str = "md",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Progress bar component."""
    percentage = min(100, max(0, (value / max_value) * 100)) if not indeterminate else 0

    return Div(
        Div(
            cls="progress-indicator",
            style=f"width: {percentage}%" if not indeterminate else None,
        ),
        role="progressbar",
        aria_valuenow=str(value) if not indeterminate else None,
        aria_valuemin="0",
        aria_valuemax=str(max_value),
        cls=cn("progress", cls),
        data_size=size,
        data_indeterminate=indeterminate if indeterminate else None,
        **attrs
    )
```

**CSS File**: `nitro/nitro/infrastructure/html/css/components/progress.css`

```css
.progress {
  position: relative;
  overflow: hidden;
  background: var(--color-zinc-200);
  border-radius: 9999px;

  &[data-size="sm"] { height: 0.5rem; }
  &[data-size="md"] { height: 0.75rem; }
  &[data-size="lg"] { height: 1rem; }
}

.progress-indicator {
  height: 100%;
  background: var(--color-primary);
  border-radius: 9999px;
  transition: width 300ms ease;

  .progress[data-indeterminate] & {
    width: 50%;
    animation: progress-indeterminate 1.5s ease-in-out infinite;
  }
}

@keyframes progress-indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}
```

#### 3. Documentation Pages (Phase 3)

**Files to create:**
- `nitro/docs_app/pages/components/toast.py`
- `nitro/docs_app/pages/components/progress.py`

Each must include:
- Interactive "trigger toast" button
- Progress value manipulation demo
- Variant examples

### Success Criteria:

#### Automated Verification:
- [ ] Pyright passes
- [ ] Components import without errors
- [ ] Documentation pages render without errors

#### Manual Verification:
- [ ] Toast appears and auto-dismisses
- [ ] Toast close button works
- [ ] Progress bar fills correctly
- [ ] Indeterminate progress animates
- [ ] Toasts stack properly
- [ ] Documentation pages allow triggering toasts interactively

---

## Phase 4: Navigation & Display

### Overview
Breadcrumb, Pagination, Avatar, Table components.

### Basecoat CSS Approach
**Same principle**: Use existing Basecoat CSS where available. Reference:
- `basecoat/components/table.css` - Table styling
- Breadcrumb/Pagination/Avatar: No Basecoat CSS - use Tailwind utilities

**Key Pattern Changes:**
- Table outputs Basecoat `.table` class
- Breadcrumb, Pagination, Avatar use Tailwind utility classes
- Remove custom CSS blocks

### Changes Required:

#### 1. Breadcrumb Component
**File**: `nitro/nitro/infrastructure/html/components/breadcrumb.py`

```python
from rusty_tags import Nav, Ol, Li, A, Span, HtmlString
from .utils import cn
from .icons import LucideIcon

def Breadcrumb(*children, cls: str = "", **attrs) -> HtmlString:
    """Breadcrumb navigation container."""
    return Nav(
        Ol(*children, cls="breadcrumb-list"),
        cls=cn("breadcrumb", cls),
        aria_label="Breadcrumb",
        **attrs
    )

def BreadcrumbItem(
    *children,
    href: str = "",
    current: bool = False,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Individual breadcrumb item."""
    content = A(*children, href=href, cls="breadcrumb-link") if href and not current else Span(*children, cls="breadcrumb-page")

    return Li(
        content,
        cls=cn("breadcrumb-item", cls),
        aria_current="page" if current else None,
        **attrs
    )

def BreadcrumbSeparator(cls: str = "", **attrs) -> HtmlString:
    """Separator between breadcrumb items."""
    return Li(
        LucideIcon("chevron-right", size="sm"),
        cls=cn("breadcrumb-separator", cls),
        role="presentation",
        aria_hidden="true",
        **attrs
    )
```

**CSS File**: `nitro/nitro/infrastructure/html/css/components/breadcrumb.css`

```css
.breadcrumb-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.375rem;
  list-style: none;
  padding: 0;
  margin: 0;
}

.breadcrumb-item {
  display: inline-flex;
  align-items: center;
}

.breadcrumb-link {
  font-size: 0.875rem;
  color: var(--color-muted-foreground);
  text-decoration: none;

  &:hover {
    color: var(--color-foreground);
    text-decoration: underline;
  }
}

.breadcrumb-page {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-foreground);
}

.breadcrumb-separator {
  color: var(--color-muted-foreground);
}
```

#### 2. Pagination Component
**File**: `nitro/nitro/infrastructure/html/components/pagination.py`

```python
from rusty_tags import Nav, Ul, Li, Button, Span, HtmlString
from rusty_tags.datastar import Signals
from .utils import cn
from .icons import LucideIcon

def Pagination(
    total_pages: int,
    signal: str = "page",
    current_page: int = 1,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Pagination component."""
    return Nav(
        Ul(
            # Previous
            Li(
                Button(
                    LucideIcon("chevron-left", size="sm"),
                    on_click=f"${signal} > 1 && (${signal} = ${signal} - 1)",
                    cls="pagination-prev",
                    aria_label="Previous page",
                ),
                cls="pagination-item",
            ),
            # Page numbers would be generated dynamically
            Span(f"Page ${{{signal}}} of {total_pages}", cls="pagination-info"),
            # Next
            Li(
                Button(
                    LucideIcon("chevron-right", size="sm"),
                    on_click=f"${signal} < {total_pages} && (${signal} = ${signal} + 1)",
                    cls="pagination-next",
                    aria_label="Next page",
                ),
                cls="pagination-item",
            ),
            cls="pagination-list",
        ),
        signals=Signals(**{signal: current_page}),
        cls=cn("pagination", cls),
        aria_label="Pagination",
        **attrs
    )
```

**CSS File**: `nitro/nitro/infrastructure/html/css/components/pagination.css`

```css
.pagination {
  display: flex;
  justify-content: center;
}

.pagination-list {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  list-style: none;
  padding: 0;
  margin: 0;
}

.pagination-item button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  padding: 0 0.5rem;
  font-size: 0.875rem;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;

  &:hover:not(:disabled) {
    background: var(--color-zinc-100);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.active {
    background: var(--color-primary);
    color: var(--color-primary-foreground);
    border-color: var(--color-primary);
  }
}

.pagination-info {
  padding: 0 0.75rem;
  font-size: 0.875rem;
  color: var(--color-muted-foreground);
}
```

#### 3. Avatar Component
**File**: `nitro/nitro/infrastructure/html/components/avatar.py`

```python
from rusty_tags import Div, Img, Span, HtmlString
from .utils import cn

def Avatar(
    src: str = "",
    alt: str = "",
    fallback: str = "",
    size: str = "md",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Avatar component with image and fallback."""
    initials = fallback or (alt[:2].upper() if alt else "?")

    return Div(
        Img(src=src, alt=alt, cls="avatar-image") if src else None,
        Span(initials, cls="avatar-fallback") if not src else None,
        cls=cn("avatar", cls),
        data_size=size,
        **attrs
    )
```

**CSS File**: `nitro/nitro/infrastructure/html/css/components/avatar.css`

```css
.avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: var(--color-zinc-200);
  border-radius: 9999px;

  &[data-size="xs"] { width: 1.5rem; height: 1.5rem; font-size: 0.625rem; }
  &[data-size="sm"] { width: 2rem; height: 2rem; font-size: 0.75rem; }
  &[data-size="md"] { width: 2.5rem; height: 2.5rem; font-size: 0.875rem; }
  &[data-size="lg"] { width: 3rem; height: 3rem; font-size: 1rem; }
  &[data-size="xl"] { width: 4rem; height: 4rem; font-size: 1.25rem; }
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-fallback {
  font-weight: 500;
  color: var(--color-zinc-600);
}
```

#### 4. Table Component
**File**: `nitro/nitro/infrastructure/html/components/table.py`

```python
from rusty_tags import Table as HTMLTable, Thead, Tbody, Tr, Th, Td, HtmlString
from .utils import cn

def Table(*children, cls: str = "", **attrs) -> HtmlString:
    """Table container."""
    return HTMLTable(*children, cls=cn("table", cls), **attrs)

def TableHeader(*children, cls: str = "", **attrs) -> HtmlString:
    """Table header section."""
    return Thead(*children, cls=cn("table-header", cls), **attrs)

def TableBody(*children, cls: str = "", **attrs) -> HtmlString:
    """Table body section."""
    return Tbody(*children, cls=cn("table-body", cls), **attrs)

def TableRow(*children, cls: str = "", **attrs) -> HtmlString:
    """Table row."""
    return Tr(*children, cls=cn("table-row", cls), **attrs)

def TableHead(
    *children,
    sortable: bool = False,
    sort_direction: str = "",
    on_sort: str = "",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Table header cell."""
    return Th(
        *children,
        cls=cn("table-head", cls),
        data_sortable=sortable if sortable else None,
        data_sort=sort_direction if sort_direction else None,
        on_click=on_sort if sortable else None,
        **attrs
    )

def TableCell(*children, cls: str = "", **attrs) -> HtmlString:
    """Table data cell."""
    return Td(*children, cls=cn("table-cell", cls), **attrs)
```

**CSS File**: `nitro/nitro/infrastructure/html/css/components/table.css`

```css
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.table-header {
  border-bottom: 1px solid var(--color-border);
}

.table-head {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 500;
  color: var(--color-muted-foreground);

  &[data-sortable] {
    cursor: pointer;
    user-select: none;

    &:hover {
      color: var(--color-foreground);
    }
  }
}

.table-body .table-row {
  border-bottom: 1px solid var(--color-border);

  &:hover {
    background: var(--color-zinc-50);
  }
}

.table-cell {
  padding: 0.75rem 1rem;
}
```

#### 5. Documentation Pages (Phase 4)

**Files to create:**
- `nitro/docs_app/pages/components/breadcrumb.py`
- `nitro/docs_app/pages/components/pagination.py`
- `nitro/docs_app/pages/components/avatar.py`
- `nitro/docs_app/pages/components/table.py`

Each must include:
- Navigation examples (breadcrumb, pagination)
- Avatar with image and fallback demos
- Table with sortable columns demo

### Success Criteria:

#### Automated Verification:
- [ ] Pyright passes
- [ ] All components import
- [ ] Documentation pages render without errors

#### Manual Verification:
- [ ] Breadcrumb navigation works
- [ ] Pagination changes page signal
- [ ] Avatar shows image or fallback
- [ ] Table renders correctly
- [ ] Sortable headers respond to clicks
- [ ] Documentation shows data-driven examples

---

## Phase 5: Advanced Components

### Overview
Combobox, Command palette - complex filtering and keyboard navigation.

### Basecoat CSS Approach
**Same principle**: Use existing Basecoat CSS where available. Reference:
- `basecoat/components/command.css` - Command palette styling
- Combobox/ThemeSwitcher: No Basecoat CSS - use Tailwind utilities or combine existing patterns

**Key Pattern Changes:**
- Command outputs Basecoat `.command` classes
- Combobox uses popover/dropdown patterns with input field
- Theme switcher uses button styling
- Remove custom CSS blocks

### Changes Required:

#### 1. Combobox Component
**File**: `nitro/nitro/infrastructure/html/components/combobox.py`

```python
from rusty_tags import Div, Input, Button, Ul, Li, HtmlString
from rusty_tags.datastar import Signals
from .utils import cn, uniq

def Combobox(
    *children,
    id: str = "",
    placeholder: str = "Search...",
    signal: str = "",
    items_signal: str = "",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Combobox with search filtering."""
    combobox_id = id or f"combobox_{uniq()}"
    query_sig = signal or f"{combobox_id}_query"
    selected_sig = f"{combobox_id}_selected"
    open_sig = f"{combobox_id}_open"

    return Div(
        Input(
            type="text",
            id=combobox_id,
            data_bind=query_sig,
            placeholder=placeholder,
            on_focus=f"${open_sig} = true",
            role="combobox",
            aria_expanded=f"${{{open_sig}}}",
            aria_autocomplete="list",
            autocomplete="off",
            cls="combobox-input",
        ),
        Div(
            *children,
            show=f"${open_sig}",
            role="listbox",
            cls="combobox-content",
        ),
        signals=Signals(**{
            query_sig: "",
            selected_sig: "",
            open_sig: False,
        }),
        cls=cn("combobox", cls),
        data_on_click_outside=f"${open_sig} = false",
        data_on_keydown_escape=f"${open_sig} = false",
        **attrs
    )

def ComboboxItem(
    *children,
    value: str,
    combobox_id: str,
    cls: str = "",
    **attrs
) -> HtmlString:
    """Individual combobox option."""
    selected_sig = f"{combobox_id}_selected"
    open_sig = f"{combobox_id}_open"
    query_sig = f"{combobox_id}_query"

    return Li(
        *children,
        on_click=f"${selected_sig} = '{value}'; ${query_sig} = '{value}'; ${open_sig} = false",
        role="option",
        cls=cn("combobox-item", cls),
        data_class=f"{{'selected': ${selected_sig} === '{value}'}}",
        **attrs
    )
```

**CSS File**: `nitro/nitro/infrastructure/html/css/components/combobox.css`

```css
.combobox {
  position: relative;
}

.combobox-input {
  width: 100%;
  height: 2.5rem;
  padding: 0 0.75rem;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);

  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: -1px;
  }
}

.combobox-content {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 50;
  max-height: 15rem;
  overflow-y: auto;
  margin-top: 0.25rem;
  padding: 0.25rem;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  list-style: none;
}

.combobox-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  border-radius: var(--radius-sm);
  cursor: pointer;

  &:hover {
    background: var(--color-zinc-100);
  }

  &.selected {
    background: var(--color-primary);
    color: var(--color-primary-foreground);
  }
}
```

#### 2. Command Palette
**File**: `nitro/nitro/infrastructure/html/components/command.py`

```python
from rusty_tags import Div, Input, Ul, Li, Span, HtmlString
from rusty_tags.datastar import Signals
from .utils import cn

def Command(
    *children,
    id: str = "command",
    placeholder: str = "Type a command or search...",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Command palette component."""
    return Div(
        Input(
            type="text",
            data_bind=f"{id}_query",
            placeholder=placeholder,
            cls="command-input",
            autocomplete="off",
        ),
        Div(*children, cls="command-list"),
        signals=Signals(**{f"{id}_query": ""}),
        cls=cn("command", cls),
        role="dialog",
        aria_label="Command palette",
        **attrs
    )

def CommandGroup(
    *children,
    heading: str = "",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Group of related commands."""
    return Div(
        Span(heading, cls="command-group-heading") if heading else None,
        Ul(*children, cls="command-group-list", role="group"),
        cls=cn("command-group", cls),
        **attrs
    )

def CommandItem(
    *children,
    on_select: str = "",
    shortcut: str = "",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Individual command item."""
    return Li(
        Span(*children, cls="command-item-content"),
        Span(shortcut, cls="command-item-shortcut") if shortcut else None,
        on_click=on_select,
        role="option",
        cls=cn("command-item", cls),
        tabindex="0",
        **attrs
    )

def CommandSeparator(cls: str = "", **attrs) -> HtmlString:
    """Separator between command groups."""
    return Div(cls=cn("command-separator", cls), role="separator", **attrs)
```

**CSS File**: `nitro/nitro/infrastructure/html/css/components/command.css`

```css
.command {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 32rem;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}

.command-input {
  width: 100%;
  height: 3rem;
  padding: 0 1rem;
  font-size: 0.875rem;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--color-border);

  &:focus {
    outline: none;
  }

  &::placeholder {
    color: var(--color-muted-foreground);
  }
}

.command-list {
  max-height: 20rem;
  overflow-y: auto;
  padding: 0.5rem;
}

.command-group-heading {
  display: block;
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-muted-foreground);
}

.command-group-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.command-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  border-radius: var(--radius-sm);
  cursor: pointer;

  &:hover,
  &:focus {
    background: var(--color-zinc-100);
    outline: none;
  }
}

.command-item-shortcut {
  font-size: 0.75rem;
  color: var(--color-muted-foreground);
}

.command-separator {
  height: 1px;
  margin: 0.25rem 0;
  background: var(--color-border);
}
```

#### 3. Theme Switcher
**File**: `nitro/nitro/infrastructure/html/components/theme_switcher.py`

```python
from rusty_tags import Button, HtmlString
from rusty_tags.datastar import Signals
from .utils import cn
from .icons import LucideIcon

def ThemeSwitcher(
    signal: str = "theme",
    default_theme: str = "system",
    cls: str = "",
    **attrs
) -> HtmlString:
    """Theme toggle component (light/dark/system)."""
    return Button(
        LucideIcon("sun", cls="theme-icon-light"),
        LucideIcon("moon", cls="theme-icon-dark"),
        LucideIcon("monitor", cls="theme-icon-system"),
        signals=Signals(**{signal: default_theme}),
        on_click=f"""
            const themes = ['light', 'dark', 'system'];
            const current = themes.indexOf(${signal});
            ${signal} = themes[(current + 1) % themes.length];
            document.documentElement.dataset.theme = ${signal} === 'system'
                ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
                : ${signal};
        """,
        cls=cn("theme-switcher", cls),
        aria_label="Toggle theme",
        data_class=f"{{'light': ${signal} === 'light', 'dark': ${signal} === 'dark', 'system': ${signal} === 'system'}}",
        **attrs
    )
```

**CSS File**: `nitro/nitro/infrastructure/html/css/components/theme-switcher.css`

```css
.theme-switcher {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  padding: 0;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;

  &:hover {
    background: var(--color-zinc-100);
  }
}

.theme-icon-light,
.theme-icon-dark,
.theme-icon-system {
  display: none;
}

.theme-switcher.light .theme-icon-light,
.theme-switcher.dark .theme-icon-dark,
.theme-switcher.system .theme-icon-system {
  display: block;
}
```

#### 4. Documentation Pages (Phase 5)

**Files to create:**
- `nitro/docs_app/pages/components/combobox.py`
- `nitro/docs_app/pages/components/command.py`
- `nitro/docs_app/pages/components/theme-switcher.py`

Each must include:
- Search/filter functionality demo
- Keyboard navigation examples
- Theme persistence demonstration

### Success Criteria:

#### Automated Verification:
- [ ] Pyright passes
- [ ] All components import
- [ ] Documentation pages render without errors

#### Manual Verification:
- [ ] Combobox filters options as you type
- [ ] Combobox selection updates signal
- [ ] Command palette keyboard navigation (arrow keys)
- [ ] Theme switcher cycles through themes
- [ ] Theme persists after refresh (with data-persist)
- [ ] Documentation pages show complex interactions clearly

---

## Testing Strategy

### Documentation Pages as Test Grounds

Each component's documentation page serves as the primary testing ground:
- **Location**: `nitro/docs_app/pages/components/{name}.py`
- **Route**: `/components/{name}`
- **Purpose**: Visual verification, interaction testing, API documentation

### Unit Tests:
- Each component renders without error
- Components output correct Basecoat classes (e.g., `btn-sm-outline`, `badge-secondary`)
- Closure components pass signals correctly
- ARIA attributes are present

### Integration Tests:
- Form components bind to Datastar signals
- Interactive components respond to events
- Compound components coordinate state

### Manual Testing Steps (via Documentation Pages):
1. Navigate to `/components/{name}` in browser
2. Verify visual appearance matches Basecoat reference
3. Test all examples in ComponentShowcase
4. Test keyboard navigation (Tab, Enter, Escape, Arrow keys)
5. Test with screen reader (VoiceOver/NVDA)
6. Test dark mode toggle
7. Verify Preview/Code tabs work correctly

## Performance Considerations

- No JavaScript bundles - Datastar is CDN-loaded
- CSS is modular - only import what you use
- Components are pure functions - no class instantiation overhead
- Signals are reactive but minimal - no virtual DOM

## Migration Notes

- Existing Dialog, Tabs, Sheet, Accordion remain unchanged
- Alert in docs_app can migrate to core component
- Button used in Sheet needs variant system from new Button component

## References

- Research: `docs/research/2025-12-12-basecoat-component-implementation.md`
- Skill: `.claude/skills/nitro-components/SKILL.md`
- Existing components: `nitro/nitro/infrastructure/html/components/`
- **Basecoat CSS (local)**: `nitro/docs_app/static/css/basecoat/components/`
- **Basecoat CSS (form)**: `nitro/docs_app/static/css/basecoat/components/form/`
- Basecoat website: https://basecoatui.com/
