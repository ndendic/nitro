# RustyTags Overview

RustyTags is the high-performance HTML generation engine that powers Nitro's frontend capabilities. Built with a Rust core and Python interface via PyO3, RustyTags delivers 3-10x faster HTML generation compared to pure Python implementations while maintaining a clean, Pythonic API.

## What is RustyTags?

RustyTags is a minimal, focused library that does one thing exceptionally well: generating HTML and SVG content at blazing speed. It serves as the foundation for Nitro's templating system, providing:

- **Complete HTML5/SVG tag system** - All standard HTML5 and SVG elements
- **Rust-powered performance** - 3-10x faster than pure Python with intelligent caching
- **Lightweight design** - Minimal dependencies, works with any Python web framework
- **Datastar integration** - Built-in reactive component support
- **Smart type handling** - Automatic attribute conversion and type processing

## Performance Benefits

RustyTags achieves exceptional performance through several Rust-powered optimizations:

### Memory Efficiency
- **Memory pooling** - Thread-local string pools and arena allocators minimize allocations
- **String interning** - Common HTML strings pre-allocated for maximum efficiency
- **Lock-free caching** - Intelligent attribute processing with smart cache invalidation

### Speed Improvements
- **3-10x faster** HTML generation compared to pure Python implementations
- **Sub-microsecond** rendering for simple elements
- **Type optimization** - Fast paths for common Python types and HTML patterns
- **Scalable** - Lock-free concurrent data structures for multi-threaded environments

## Architecture

RustyTags follows a clean separation between the Rust core and Python interface:

**Rust Core** (`RustyTags/src/lib.rs`):
- High-performance HTML/SVG generation with PyO3 bindings
- Advanced memory management with pooling and interning
- Complete tag system with macro-generated optimizations
- Approximately 2000+ lines of optimized Rust code

**Python Interface** (`rusty_tags/`):
- All HTML/SVG tags exported as Python classes
- Datastar SDK for reactive components
- Utility functions (Page, show, template helpers)
- Zero runtime dependencies

## Basic Usage

### Importing Tags

```python
# Import individual tags
from rusty_tags import Div, H1, P, Button, Input

# Import multiple HTML tags
from rusty_tags import (
    Html, Head, Body, Main, Section,  # Structure
    H1, H2, H3, P, A, Strong, Em,     # Text
    Form, Input, Button, Select,       # Forms
    Ul, Ol, Li,                        # Lists
    Table, Tr, Td, Th,                 # Tables
)

# Import SVG tags
from rusty_tags import Svg, Circle, Rect, Path, Line
```

### Creating HTML Elements

```python
from rusty_tags import Div, H1, P, Button

# Simple element
header = H1("Welcome to RustyTags")

# Nested elements
content = Div(
    H1("Welcome", cls="text-4xl font-bold"),
    P("High-performance HTML generation with Rust + Python"),
    Button("Click me", type="submit"),
    cls="container mx-auto p-8"
)

# Convert to HTML string
html_string = str(content)
# Output: <div class="container mx-auto p-8">...</div>
```

### Available Tags

RustyTags provides all standard HTML5 tags:

**Structure**: `Html`, `Head`, `Body`, `Main`, `Section`, `Article`, `Header`, `Footer`, `Nav`, `Aside`, `Div`, `Span`

**Text**: `H1`-`H6`, `P`, `A`, `Strong`, `Em`, `B`, `I`, `U`, `Small`, `Mark`, `Del`, `Ins`, `Sub`, `Sup`, `Abbr`, `Code`, `Pre`, `Kbd`, `Samp`, `Var`, `Blockquote`, `Q`, `Cite`

**Forms**: `Form`, `Input`, `Button`, `Select`, `OptionEl` (aliased as `Option`), `Textarea`, `Label`, `Fieldset`, `Legend`, `Datalist`, `Optgroup`, `Meter`, `Progress`

**Lists**: `Ul`, `Ol`, `Li`, `Dl`, `Dt`, `Dd`, `Menu`

**Tables**: `Table`, `Thead`, `Tbody`, `Tfoot`, `Tr`, `Th`, `Td`, `Caption`, `Col`, `Colgroup`

**Media**: `Img`, `Video`, `Audio`, `Source`, `Track`, `Picture`, `Canvas`, `Iframe`, `Embed`, `Object`

**Interactive**: `Details`, `Summary`, `Dialog`

**Metadata**: `Title`, `Meta`, `Link`, `Style`, `Script`, `Base`, `Noscript`, `Template`

**Other**: `Hr`, `Br`, `Wbr`, `Address`, `Time`, `Data`, `Figure`, `Figcaption`, `Map`, `Area`

### SVG Support

RustyTags includes complete SVG tag support:

```python
from rusty_tags import Svg, Circle, Rect, Line, Path

# Create SVG graphics
chart = Svg(
    Circle(cx="50", cy="50", r="40", fill="blue"),
    Rect(x="10", y="10", width="30", height="30", fill="red"),
    Line(x1="0", y1="0", x2="100", y2="100", stroke="black"),
    width="200", height="200", viewBox="0 0 200 200"
)
```

**SVG Tags**: `Svg`, `Circle`, `Rect`, `Line`, `Path`, `Polygon`, `Polyline`, `Ellipse`, `Text`, `G`, `Defs`, `Use`, `Symbol`, `Marker`, `LinearGradient`, `RadialGradient`, `Stop`, `Pattern`, `ClipPath`, `Mask`, `Image`, `ForeignObject`

## Smart Type System

RustyTags automatically handles various Python types:

```python
from rusty_tags import Div, P

content = Div(
    42,              # Numbers → strings
    True,            # Booleans → "true"/"false"
    None,            # None → empty string (filtered out)
    [1, 2, 3],       # Lists → joined strings
    P("Nested"),     # Other tags → rendered HTML
)
```

### Custom Object Support

RustyTags recognizes objects with HTML rendering methods:

```python
class MyComponent:
    def __html__(self):
        return "<div>Custom HTML</div>"

# Automatically calls __html__()
Div(MyComponent())
```

Supported methods (checked in order):
1. `__html__()` - Explicit HTML rendering
2. `render()` - Common rendering method
3. `_repr_html_()` - Jupyter notebook compatibility

## Framework Integration

RustyTags is completely framework-agnostic and works with any Python web framework:

```python
from rusty_tags import Div, H1, P, Page

# FastAPI
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def home():
    return HTMLResponse(str(Page(
        H1("FastAPI + RustyTags"),
        P("High-performance HTML generation"),
        title="Home"
    )))

# Flask
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return str(Page(
        H1("Flask + RustyTags"),
        title="Home"
    ))

# Django
from django.http import HttpResponse

def home(request):
    return HttpResponse(str(Page(
        H1("Django + RustyTags"),
        title="Home"
    )))
```

## Jupyter Integration

RustyTags includes a `show()` utility for displaying HTML directly in Jupyter notebooks:

```python
from rusty_tags import Div, H1, show

# Create content
content = Div(
    H1("Notebook Content"),
    style="color: blue; padding: 20px;"
)

# Display in Jupyter
show(content)  # Renders directly in the notebook cell
```

## Relationship to Nitro

While RustyTags can be used standalone, Nitro builds on top of it to provide:

- **Advanced templating** - Enhanced `Page` component with CDN integrations
- **UI component library** - 43+ pre-built components with Basecoat styling
- **Event system** - Backend events and real-time communication
- **Framework adapters** - Deep integration with FastAPI, FastHTML, Flask
- **Entity system** - Rich domain models with hybrid persistence
- **Tailwind CSS CLI** - Integrated build system

**Use RustyTags standalone when:**
- You need minimal dependencies
- You're building your own templating system
- You want maximum performance with simple needs

**Use Nitro when:**
- You want a complete web framework
- You need advanced templating and components
- You're building complex applications with entities and events

## Installation

RustyTags is installed automatically with Nitro:

```bash
pip install nitro
```

Or install standalone:

```bash
pip install rusty-tags
```

**Requirements:**
- Python 3.8+
- No runtime dependencies

## Source References

- **RustyTags Core**: `/RustyTags/src/lib.rs` - Rust implementation
- **Python Interface**: `/RustyTags/rusty_tags/__init__.py` - Python bindings
- **RustyTags Documentation**: `/RustyTags/README.md` - Complete library docs

## Next Steps

- Learn practical usage patterns in [RustyTags Usage](./usage.md)
- Explore reactive components in [Datastar Overview](../datastar/philosophy.md)
- Build complete pages with the [Nitro Page component](./usage.md#page-component)
