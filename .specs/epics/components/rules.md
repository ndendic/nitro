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

**Key Patterns Established:**
- `cn()` for class merging (`utils.py:6-24`)
- `cva()` for variant classes (`utils.py:27-66`)
- Closure pattern for compound components (`tabs.py:63-84`)
- Datastar Signals for reactive state (`sheet.py:20-37`)
- Native HTML elements where possible (`dialog.py:95-99`)

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