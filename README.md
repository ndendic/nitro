# Nitro

⚠️ **Early Beta** - This library is in active development and APIs may change.

A booster add-on for your favourite web-framework. Built on rusty-tags core. Nitro provides a web development toolkit with intelligent templating, reactive component support, event system, framework integrations, and a powerful Tailwind CSS CLI.

## What Nitro Does

Nitro provides a comprehensive web development framework with:

- **🏷️ Complete HTML5/SVG Tags**: All standard HTML5 and SVG elements powered by rusty-tags core
- **⚡ High Performance**: 3-10x faster than pure Python through Rust-optimized HTML generation
- **🎨 Modern Templating**: Page templates, decorators, and component system for full-stack development
- **🔄 Reactive Components**: Built-in Datastar integration for modern web applications
- **🏗️ FastHTML-Style API**: Familiar syntax with callable chaining support
- **🧠 Intelligent Processing**: Automatic attribute handling and smart type conversion
- **🎯 Tailwind CSS CLI**: Framework-agnostic CLI for Tailwind CSS integration and build management
- **📦 Framework Ready**: Works with FastAPI, Flask, Django, and other Python web frameworks

## Architecture

Nitro is built on top of the `rusty-tags` core package:

- **`rusty-tags`** (core): High-performance HTML generation library with Rust backend
- **`nitro`** (framework): Full-stack web development toolkit with advanced features

## Quick Start

### Installation

```bash
# Install Nitro framework (includes rusty-tags as dependency)
pip install nitro-boost

# For development - clone and install
git clone <repository>
cd nitro
pip install -e .
```

The installation includes the `nitro` CLI for Tailwind CSS management:

```bash
# Verify CLI installation
nitro --version

# See available commands
nitro --help

# Initialize Tailwind CSS in your project
nitro tw init
```

### Basic HTML Generation

```python
from nitro import Div, P, H1, A, Button, Input

# Simple HTML elements
content = Div(
    H1("Welcome to Nitro"),
    P("High-performance HTML generation with Python + Rust"),
    A("Learn More", href="https://github.com/ndendic/Nitro"),
    cls="container"
)
print(content)
# <div class="container">
#   <h1>Welcome to Nitro</h1>
#   <p>High-performance HTML generation with Python + Rust</p>
#   <a href="https://github.com/ndendic/Nitro">Learn More</a>
# </div>
```

### Complete Page Templates

```python
from nitro.utils import Page, create_template
from nitro import Main, Section, H2, P

# Create a page template
template = create_template(
    title="My App",
    hdrs=(
        Link(rel="stylesheet", href="/static/app.css"),
        Meta(charset="utf-8"),
    ),
    datastar=True  # Include Datastar for reactive components
)

# Use as decorator
@template
def home_page():
    return Main(
        Section(
            H2("Dashboard"),
            P("Welcome to your dashboard"),
            cls="hero"
        ),
        cls="container"
    )

# Or create complete pages directly
page = Page(
    H1("My Website"),
    P("Built with Nitro"),
    title="Home Page",
    htmlkw={"lang": "en"},
    bodykw={"class": "bg-gray-100"}
)
```

### Reactive Web Applications

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from nitro import *
from nitro.datastar import DS

app = FastAPI()
page = create_template("Counter App", datastar=True)

@app.get("/")
@page(wrap_in=HTMLResponse)
def counter_app():
    return Main(
        H1("Interactive Counter"),
        Div(
            P(text="Count: $count", cls="display"),
            Button("+1", on_click="$count++", cls="btn"),
            Button("-1", on_click="$count--", cls="btn"),
            Button("Reset", on_click=DS.set("count", 0), cls="btn"),
            signals={"count": 0}  # Reactive state
        ),
        cls="app"
    )
```

## Core Features

### 🏷️ Complete HTML5/SVG Tag System

Nitro provides all standard HTML5 and SVG elements as Python functions:

```python
# HTML elements
Html, Head, Body, Title, Meta, Link, Script
H1, H2, H3, H4, H5, H6, P, Div, Span, A
Form, Input, Button, Select, Textarea, Label
Table, Tr, Td, Th, Tbody, Thead, Tfoot
Nav, Main, Section, Article, Header, Footer
Img, Video, Audio, Canvas, Iframe
# ... and many more

# SVG elements
Svg, Circle, Rect, Line, Path, Polygon
G, Defs, Use, Symbol, LinearGradient
Text, Image, ForeignObject
# ... complete SVG support
```

### 🎨 Modern Templating System

**Page Templates:**
```python
from nitro.utils import Page, create_template

# Complete HTML documents
page = Page(
    H1("My Site"),
    P("Content here"),
    title="Page Title",
    hdrs=(Meta(charset="utf-8"), Link(rel="stylesheet", href="/app.css")),
    datastar=True  # Auto-include reactive framework
)

# Reusable templates with decorators
@create_template("My App", datastar=True)
def my_view():
    return Div("Page content")
```

**Component System:**
```python
# Reusable components
def Card(title, *content, **attrs):
    return Div(
        H3(title, cls="card-title"),
        Div(*content, cls="card-body"),
        cls="card",
        **attrs
    )

# Usage
cards = Div(
    Card("Card 1", P("First card content")),
    Card("Card 2", P("Second card content"), cls="featured"),
    cls="card-grid"
)
```

### ⚡ Performance Optimizations

- **Memory Pooling**: Thread-local string pools and arena allocators
- **Intelligent Caching**: Lock-free attribute processing with smart cache invalidation
- **String Interning**: Common HTML strings pre-allocated for efficiency
- **Type Optimization**: Fast paths for common Python types and HTML patterns
- **Expression Detection**: Intelligent JavaScript expression analysis for reactive components

### 🔄 Reactive Component Integration

Built-in Datastar support for modern reactive web development:

```python
# Reactive state management
interactive_form = Form(
    Input(bind="$email", placeholder="Enter email"),
    Input(bind="$name", placeholder="Enter name"),
    Button("Submit", on_click=DS.post("/api/submit", data={"email": "$email", "name": "$name"})),
    Div(
        text="Email: $email, Name: $name",
        show="$email && $name"  # Conditional display
    ),
    signals={"email": "", "name": ""}  # Initial state
)

# Server-sent events and real-time updates
@app.get("/updates")
async def live_updates():
    async def event_stream():
        while True:
            yield SSE.patch_elements(
                Div(f"Update: {datetime.now()}", cls="update"),
                selector="#updates"
            )
            await asyncio.sleep(1)
    return event_stream()
```

### 🏗️ FastHTML-Style API

Familiar syntax with enhanced capabilities:

```python
# Traditional syntax
content = Div("Hello", cls="greeting")

# Callable chaining (FastHTML-style)
content = Div(cls="container")(
    H1("Title"),
    P("Content")
)

# Attribute flexibility
element = Div(
    "Content",
    {"id": "main", "data-value": 123},  # Dict automatically expands to attributes
    cls="primary",
    hidden=False  # Boolean attributes handled correctly
)
```

### 🔧 Smart Type System

Intelligent handling of Python types:

```python
# Automatic type conversion
Div(
    42,           # Numbers → strings
    True,         # Booleans → "true"/"false" or boolean attributes
    None,         # None → empty string
    [1, 2, 3],    # Lists → joined strings
    custom_obj,   # Objects with __html__(), render(), or _repr_html_()
)

# Framework integration
class MyComponent:
    def __html__(self):
        return "<div>Custom HTML</div>"

# Automatically recognized and rendered
Div(MyComponent())
```

## ⚡ Tailwind CSS CLI

Nitro includes a powerful, framework-agnostic CLI for Tailwind CSS integration that works with any Python web framework.

### Quick Start

```bash
# Initialize Tailwind CSS in your project
nitro tw init

# Start development with file watching
nitro tw dev

# Build production CSS
nitro tw build
```

### Features

- **🚀 Framework Agnostic**: Works with FastAPI, Django, Flask, FastHTML, Sanic, and any Python framework
- **📦 Standalone Binary**: Downloads and manages Tailwind CSS standalone CLI automatically
- **⚙️ Smart Configuration**: Auto-detects project structure with environment variable overrides
- **👀 File Watching**: Development mode with automatic CSS rebuilding
- **🎯 Content Scanning**: Scans your entire project for Tailwind classes
- **🔧 Zero Config**: Works out of the box with sensible defaults

### Commands

#### `nitro tw init`

Initialize Tailwind CSS in your project:

```bash
# Basic initialization
nitro tw init

# With detailed output
nitro tw init --verbose

# Force overwrite existing files
nitro tw init --force
```

**What it does:**
- Downloads the Tailwind CSS standalone binary for your platform
- Creates CSS input file with Tailwind v4 directives
- Sets up appropriate directory structure
- Updates `.gitignore` with generated file patterns

#### `nitro tw dev`

Start Tailwind CSS in watch mode for development:

```bash
# Start file watcher
nitro tw dev

# With detailed output
nitro tw dev --verbose
```

**Features:**
- Watches all project files for Tailwind class changes
- Automatically rebuilds CSS when changes detected
- Shows build progress and file sizes
- Graceful keyboard interrupt handling

#### `nitro tw build`

Build optimized production CSS:

```bash
# Build production CSS
nitro tw build

# Build with custom output path
nitro tw build --output dist/styles.css

# Build without minification
nitro tw build --no-minify

# Verbose build information
nitro tw build --verbose
```

### Configuration

#### Auto-Detection

Nitro automatically detects the best CSS file locations based on your project structure:

```bash
# If static/ folder exists:
static/css/input.css  → static/css/output.css

# If assets/ folder exists:
assets/input.css      → assets/output.css

# Otherwise:
input.css             → output.css
```

#### Environment Variables

Override default paths using environment variables:

```bash
# Custom input CSS location
NITRO_TAILWIND_CSS_INPUT="src/styles/main.css"

# Custom output CSS location
NITRO_TAILWIND_CSS_OUTPUT="dist/app.css"

# Custom content scanning paths
NITRO_TAILWIND_CONTENT_PATHS='["src/**/*.py", "templates/**/*.html"]'
```

#### Environment Files

Create `.env` files in your project root for persistent configuration:

```bash
# .env
NITRO_TAILWIND_CSS_INPUT="assets/styles/input.css"
NITRO_TAILWIND_CSS_OUTPUT="public/css/styles.css"

# .env.local (for local development overrides)
NITRO_TAILWIND_CSS_OUTPUT="dev/styles.css"

# .env.prod (for production settings)
NITRO_TAILWIND_CSS_OUTPUT="dist/production.css"
```

### Framework Examples

#### FastAPI

```bash
# Project structure
myapp/
├── static/css/
├── templates/
├── .env
└── main.py

# .env
NITRO_TAILWIND_CSS_INPUT="static/css/input.css"
NITRO_TAILWIND_CSS_OUTPUT="static/css/styles.css"
```

#### Django

```bash
# Project structure
myproject/
├── myapp/static/css/
├── templates/
├── .env
└── settings.py

# .env
NITRO_TAILWIND_CSS_INPUT="myapp/static/src/input.css"
NITRO_TAILWIND_CSS_OUTPUT="myapp/static/css/tailwind.css"
NITRO_TAILWIND_CONTENT_PATHS='["myapp/**/*.py", "templates/**/*.html"]'
```

#### Flask

```bash
# Project structure
flask-app/
├── static/css/
├── templates/
├── .env
└── app.py

# .env
NITRO_TAILWIND_CSS_INPUT="static/scss/main.css"
NITRO_TAILWIND_CSS_OUTPUT="static/css/app.css"
```

### Binary Management

The CLI automatically manages the Tailwind CSS standalone binary:

- **Download Location**: `~/.nitro/cache/latest/tailwindcss-{platform}-{arch}`
- **Version Support**: Latest Tailwind CSS v4.x
- **Platform Support**: Windows, macOS (Intel/ARM), Linux (x64/ARM)
- **Validation**: Ensures downloaded binary is genuine Tailwind CLI
- **Cache**: Reuses downloaded binary across projects

### Content Scanning

By default, Nitro scans these file patterns for Tailwind classes:

```python
[
    "**/*.py",      # Python files
    "**/*.html",    # HTML templates
    "**/*.jinja2",  # Jinja templates
    "!**/__pycache__/**",  # Exclude Python cache
    "!**/test_*.py"       # Exclude test files
]
```

Customize scanning patterns with environment variables:

```bash
NITRO_TAILWIND_CONTENT_PATHS='[
    "src/**/*.py",
    "templates/**/*.html",
    "components/**/*.vue",
    "!**/node_modules/**"
]'
```

### Integration with Development Servers

The Tailwind CLI runs independently of your web framework, making it perfect for development workflows:

```bash
# Terminal 1: Start your web server
python -m uvicorn main:app --reload

# Terminal 2: Start Tailwind watcher
nitro tw dev
```

Or use process managers like `honcho` or `foreman`:

```yaml
# Procfile
web: python -m uvicorn main:app --reload --port 8000
css: nitro tw dev
```

### Troubleshooting

**Binary Download Issues:**
```bash
# Check binary location
ls -la ~/.nitro/cache/latest/

# Clear cache and re-download
rm -rf ~/.nitro/cache/ && nitro tw init
```

**Configuration Issues:**
```bash
# Test configuration loading
python -c "from nitro.config import get_nitro_config; print(get_nitro_config().tailwind.css_output)"

# Verify environment variables
env | grep NITRO_TAILWIND
```

## Framework Integration

### FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from nitro.utils import create_template

app = FastAPI()
page = create_template("My API", datastar=True)

@app.get("/")
@page(wrap_in=HTMLResponse)
def index():
    return Main(H1("API Dashboard"))
```

### Flask

```python
from flask import Flask
from nitro import Page, H1, P

app = Flask(__name__)

@app.route("/")
def index():
    return str(Page(
        H1("Flask + Nitro"),
        P("High performance templating"),
        title="Flask Demo"
    ))
```

### Jupyter/IPython

```python
from nitro.utils import show
from nitro import Div, H1

# Display in notebooks
content = Div(H1("Notebook Content"), style="color: blue;")
show(content)  # Renders directly in Jupyter cells
```

## Architecture

**🦀 Rust Core (`src/lib.rs`):**
- High-performance HTML/SVG generation with PyO3 bindings
- Advanced memory management with pooling and interning
- Intelligent Datastar attribute processing
- Complete tag system with macro-generated optimizations

**🐍 Python Layer (`nitro/`):**
- **Core Module**: All HTML/SVG tags and utilities
- **Templates**: Page generation and decorator system
- **Datastar**: Reactive component utilities and action generators
- **Events**: Blinker-based event system for scalable applications
- **Client**: WebSocket/SSE client management
- **Extras**: UI components (accordion, dialog, tabs, etc.)

**💻 Examples (`lab/`):**
- Complete FastAPI applications
- Real-world usage patterns
- Interactive examples with SSE

## Performance

Nitro delivers significant performance improvements:

- **3-10x faster** than pure Python HTML generation
- **Sub-microsecond** rendering for simple elements
- **Memory efficient** with intelligent pooling and caching
- **Scalable** with lock-free concurrent data structures

```bash
# Run performance tests (when available)
python lab/benchmarks.py
```

## Development Status

**Early Beta** - Core functionality is stable and extensively used in development, but APIs may evolve.

### ✅ Stable Features
- Complete HTML5/SVG tag system
- High-performance Rust core
- Modern templating with decorators
- Reactive component integration
- Framework compatibility
- Memory optimization
- Tailwind CSS CLI with environment configuration

### 🔄 In Development
- Comprehensive test suite
- Performance benchmarking
- Package distribution
- Enhanced documentation

## System Requirements

- **Python 3.10+** (broad compatibility)
- **Dependencies**: `blinker ≥1.9.0`, `pydantic ≥2.11.9`, `pydantic-settings ≥2.11.0`, `rusty-tags ≥0.6.1`, `typer ≥0.19.2`
- **Build Requirements** (development): Rust 1.70+, Maturin ≥1.9
- **CLI Requirements**: Internet connection for Tailwind CSS binary download (cached after first use)

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please check the repository for contributing guidelines and open issues.

## Links

- **Repository**: https://github.com/ndendic/Nitro
- **Issues**: https://github.com/ndendic/Nitro/issues
- **Examples**: See `lab/` directory for complete applications