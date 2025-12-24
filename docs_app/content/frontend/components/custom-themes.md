# Custom Themes

Nitro's theming system is built on CSS variables, making it easy to create custom color schemes, support dark mode, and switch between themes at runtime.

## Theming Philosophy

**CSS Variables as the Foundation** - All component styling references CSS variables, not hardcoded colors. This means:

- Change one variable, update every component
- Support multiple themes without duplicate CSS
- Switch themes at runtime with JavaScript
- Users can override with their own stylesheets

## Dark Mode

Dark mode is built into Basecoat and activated via the `.dark` class or `[data-theme="dark"]` attribute.

### Applying Dark Mode

**Method 1: Class on HTML Element**

```python
from rusty_tags import Html, Body

Html(
    Body(
        # Content here
        cls="dark"  # Activates dark mode
    )
)
```

**Method 2: Data Attribute**

```python
from rusty_tags import Html

Html(
    # Content
    data_theme="dark"  # Activates dark mode
)
```

### Dark Mode CSS Variables

Location: `nitro/docs_app/static/css/basecoat/base/base.css`

```css
/* Light mode (default) */
:root {
  --background: oklch(1 0 0);           /* White */
  --foreground: oklch(0.1450 0 0);      /* Near black */
  --primary: oklch(0.2050 0 0);         /* Dark gray */
  --primary-foreground: oklch(0.9850 0 0); /* Near white */
  --border: oklch(0.9220 0 0);          /* Light gray */
}

/* Dark mode */
.dark {
  --background: oklch(0.1450 0 0);      /* Near black */
  --foreground: oklch(0.9850 0 0);      /* Near white */
  --primary: oklch(0.9220 0 0);         /* Light gray */
  --primary-foreground: oklch(0.2050 0 0); /* Dark gray */
  --border: oklch(0.2750 0 0);          /* Dark gray */
}
```

### System Preference Detection

Detect user's OS preference:

```html
<script>
  // Apply dark mode based on system preference
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark');
  }

  // Listen for changes
  window.matchMedia('(prefers-color-scheme: dark)')
    .addEventListener('change', (e) => {
      if (e.matches) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    });
</script>
```

## ThemeSwitcher Component

Nitro provides a built-in component for toggling themes.

Location: `nitro/nitro/infrastructure/html/components/theme_switcher.py`

### Basic Usage

```python
from nitro.infrastructure.html.components import ThemeSwitcher

# Simple light/dark toggle
ThemeSwitcher()
```

This creates a button that cycles through: `light` → `dark` → `system` → `light`

### With System Preference

```python
# Include system preference option
ThemeSwitcher(
    default_theme="system",  # Start with system preference
    persist=True             # Remember user choice
)
```

### Customization

```python
# Custom positioning
ThemeSwitcher(
    cls="fixed top-4 right-4",
    size="lg",
    variant="outline"
)

# Custom signal name (for multiple theme controls)
ThemeSwitcher(
    signal="app_theme",
    default_theme="dark"
)
```

### Dropdown Variant

For explicit theme selection instead of cycling:

```python
from nitro.infrastructure.html.components import ThemeSwitcherDropdown

ThemeSwitcherDropdown(
    default_theme="system",
    persist=True
)
```

### How ThemeSwitcher Works

The component uses Datastar signals and effects:

```python
# Simplified implementation
ThemeSwitcher(
    signal="theme_mode",        # Datastar signal: "light" | "dark" | "system"
    default_theme="system",
    persist=True                # Uses data-persist for localStorage
)

# JavaScript effect (built into component)
"""
const mode = $theme_mode;
const isDark = mode === 'dark' ||
  (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

if (isDark) {
  document.documentElement.classList.add('dark');
} else {
  document.documentElement.classList.remove('dark');
}
"""
```

## Creating Custom Themes

Beyond light/dark, you can create named themes with custom color palettes.

### Define Theme Variables

Create a new CSS file with theme variables:

```css
/* themes/ocean.css */
[data-theme="ocean"] {
  /* Brand colors */
  --primary: oklch(0.5 0.15 240);           /* Ocean blue */
  --primary-foreground: oklch(1 0 0);       /* White */
  --secondary: oklch(0.85 0.05 200);        /* Light cyan */
  --secondary-foreground: oklch(0.2 0 0);   /* Dark text */

  /* UI colors */
  --background: oklch(0.98 0.01 220);       /* Light blue tint */
  --foreground: oklch(0.15 0.02 240);       /* Deep blue */
  --card: oklch(1 0 0);                     /* White cards */
  --card-foreground: oklch(0.15 0.02 240);
  --border: oklch(0.85 0.03 220);           /* Soft blue border */
  --muted: oklch(0.9 0.02 220);
  --muted-foreground: oklch(0.5 0.05 240);

  /* Accent colors */
  --accent: oklch(0.6 0.18 180);            /* Teal accent */
  --accent-foreground: oklch(1 0 0);

  /* Status colors */
  --destructive: oklch(0.6 0.25 25);        /* Coral red */
  --destructive-foreground: oklch(1 0 0);

  /* Component customization */
  --radius: 0.75rem;                         /* Rounder corners */
  --shadow-sm: 0 2px 8px oklch(0.5 0.15 240 / 0.15);  /* Blue shadows */
}
```

### Apply Custom Theme

**Option 1: Via Page Component**

```python
from nitro.infrastructure.html import Page

page = Page(
    content,
    data_theme="ocean",  # Apply ocean theme
    title="My App"
)
```

**Option 2: On Specific Sections**

```python
from rusty_tags import Div
from nitro.infrastructure.html.components import Card

Div(
    Card("This card uses the ocean theme"),
    data_theme="ocean"  # Only this section is themed
)
```

**Option 3: Root Level**

```python
from rusty_tags import Html, Body

Html(
    Body(
        # Content
    ),
    data_theme="ocean"
)
```

### Theme Switcher for Named Themes

Use `ThemeSelect` for named theme selection:

```python
from nitro.infrastructure.html.components import ThemeSelect

ThemeSelect(
    options=[
        {"value": "default", "label": "Default"},
        {"value": "ocean", "label": "Ocean Blue"},
        {"value": "forest", "label": "Forest Green"},
        {"value": "sunset", "label": "Sunset Orange"},
    ],
    default_theme="default",
    persist=True  # Remember user choice
)
```

## Complete Theme Example

Here's a complete custom theme implementation:

### 1. Create Theme CSS

```css
/* static/css/themes/candy.css */
[data-theme="candy"] {
  /* Vibrant candy colors */
  --primary: oklch(0.6 0.25 320);           /* Hot pink */
  --primary-foreground: oklch(1 0 0);
  --secondary: oklch(0.75 0.2 280);         /* Purple */
  --secondary-foreground: oklch(1 0 0);
  --background: oklch(0.98 0.02 350);       /* Pink tint */
  --foreground: oklch(0.2 0.05 320);        /* Dark magenta */
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.2 0.05 320);
  --border: oklch(0.85 0.08 320);           /* Pink border */
  --accent: oklch(0.65 0.22 60);            /* Yellow accent */
  --accent-foreground: oklch(0.2 0 0);
  --destructive: oklch(0.65 0.28 10);       /* Red */
  --destructive-foreground: oklch(1 0 0);

  /* Fun customization */
  --radius: 1rem;                            /* Very round */
  --font-sans: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
  --shadow-md: 0 4px 12px oklch(0.6 0.25 320 / 0.3);  /* Pink glow */
}
```

### 2. Load Theme CSS

```python
from nitro.infrastructure.html import Page
from rusty_tags import Link

page = Page(
    content,
    hdrs=(
        Link(rel="stylesheet", href="/static/css/basecoat/basecoat.css"),
        Link(rel="stylesheet", href="/static/css/themes/candy.css"),
    ),
    data_theme="candy",
    title="Candy Theme"
)
```

### 3. Add Theme Selector

```python
from nitro.infrastructure.html.components import ThemeSelect

# In your app header
ThemeSelect(
    options=[
        {"value": "default", "label": "Default"},
        {"value": "candy", "label": "Candy"},
    ],
    default_theme="default",
    persist=True,
    cls="absolute top-4 right-4"
)
```

## Advanced Theming Techniques

### Theme-Specific Component Variants

Create theme-specific styles:

```css
/* Default theme button */
[data-theme="default"] .btn-special {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
}

/* Ocean theme button */
[data-theme="ocean"] .btn-special {
  background: linear-gradient(135deg,
    oklch(0.5 0.2 240),
    oklch(0.6 0.18 180)
  );
  box-shadow: 0 4px 12px oklch(0.5 0.2 240 / 0.3);
}
```

### Scoped Theming

Apply different themes to different sections:

```python
from rusty_tags import Div, Section
from nitro.infrastructure.html.components import Card

Div(
    Section(
        Card("Default theme section"),
        data_theme="default"
    ),
    Section(
        Card("Ocean theme section"),
        data_theme="ocean"
    ),
    Section(
        Card("Dark mode section"),
        data_theme="dark"
    )
)
```

### Dynamic Theme Loading

Load themes based on user preference or URL parameter:

```python
from fastapi import FastAPI, Request
from nitro.infrastructure.html import Page

app = FastAPI()

@app.get("/")
def index(request: Request):
    # Get theme from query param or default
    theme = request.query_params.get("theme", "default")

    return Page(
        content,
        data_theme=theme,
        title="Themed App"
    )
```

### Theme Inheritance

Extend existing themes:

```css
/* Extend dark theme with custom colors */
.dark[data-theme="dark-ocean"] {
  --primary: oklch(0.6 0.15 240);      /* Ocean blue on dark */
  --accent: oklch(0.65 0.18 180);      /* Teal accent */
  /* Other dark mode variables remain unchanged */
}
```

## Persistence with Datastar

Themes can be persisted to `localStorage` using Datastar:

```python
from nitro.infrastructure.html.components import ThemeSwitcher

# Automatically persists to localStorage
ThemeSwitcher(
    signal="theme_mode",
    persist=True  # Uses data-persist attribute
)
```

The component generates:

```html
<div>
  <button><!-- Theme toggle --></button>
  <div class="hidden" data-persist="theme_mode" data-effect="...">
    <!-- Persistence handler -->
  </div>
</div>
```

On page load, the theme is restored from `localStorage`.

## Best Practices

**Use Semantic Color Names**

```css
/* ✅ Good - semantic meaning */
--primary
--destructive
--muted-foreground

/* ❌ Avoid - implementation detail */
--blue-500
--red-600
```

**Maintain Contrast Ratios**

Ensure text is readable in all themes:

```css
/* Use foreground variants with sufficient contrast */
--primary: oklch(0.5 0.15 240);
--primary-foreground: oklch(1 0 0);  /* White on blue = good contrast */
```

**Test in Both Light and Dark**

If you create a custom theme, create both light and dark variants:

```css
[data-theme="ocean"] { /* ... light ocean ... */ }
.dark[data-theme="ocean"] { /* ... dark ocean ... */ }
```

**Use OKLCH Color Space**

OKLCH provides perceptually uniform colors:

```css
/* ✅ OKLCH - perceptually uniform */
--primary: oklch(0.5 0.15 240);

/* ⚠️ HSL - not perceptually uniform */
--primary: hsl(240, 50%, 50%);
```

## Related Documentation

- [Component Library Overview](./overview.md) - All available components
- [Basecoat Styling](./basecoat-styling.md) - CSS variable system
- [Nitro TW CLI](./nitro-tw-cli.md) - Building custom CSS

## Source Code Reference

- Base CSS Variables: `nitro/docs_app/static/css/basecoat/base/base.css:3-100`
- ThemeSwitcher Component: `nitro/nitro/infrastructure/html/components/theme_switcher.py:17-121`
- ThemeSelect Component: `nitro/nitro/infrastructure/html/components/theme_switcher.py:234-301`
