# Nitro

⚠️ **Early Beta** - This library is in active development and APIs may change.

**Nitro is a collection of abstraction layers for Python web development.** It is not a framework - it's a toolkit that works with your favorite web frameworks (FastAPI, Flask, FastHTML, Django, etc.).

Built on rusty-tags core, Nitro provides intelligent templating, reactive component support, event system, and a powerful Tailwind CSS CLI.

## Three Core Abstraction Layers

1. **Active Record** - Entity-centric persistence with rich domain models
2. **Front-end UI Design** - High-performance HTML generation, reactive components, templating
3. **Event Routing** - Domain events with Blinker, decoupled side effects

## What Nitro Provides

- **🏷️ Complete HTML5/SVG Tags**: All standard HTML5 and SVG elements powered by rusty-tags core
- **⚡ High Performance**: 3-10x faster than pure Python through Rust-optimized HTML generation
- **🎨 Modern Templating**: Page templates, decorators, and component system for full-stack development
- **🔄 Reactive Components**: Built-in Datastar integration for modern web applications
- **🏗️ FastHTML-Style API**: Familiar syntax with callable chaining support
- **🧠 Intelligent Processing**: Automatic attribute handling and smart type conversion
- **🎯 Tailwind CSS CLI**: CLI for Tailwind CSS integration and build management
- **📦 Works Everywhere**: Integrates with FastAPI, Flask, Django, FastHTML, and any Python web framework

## Architecture

Nitro is built on top of the `rusty-tags` core package:

- **`rusty-tags`** (core): High-performance HTML generation library with Rust backend
- **`nitro`** (abstraction layers): Collection of tools for web development - Active Record, UI Design, Event Routing

## Quick Start

### Installation

```bash
# Install Nitro (includes rusty-tags as dependency)
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
from nitro.utils import Page, page_template

# Complete HTML documents
page = Page(
    H1("My Site"),
    P("Content here"),
    title="Page Title",
    hdrs=(Meta(charset="utf-8"), Link(rel="stylesheet", href="/app.css")),
    datastar=True  # Auto-include Datastar reactive library
)

# Reusable templates with decorators
@page_template("My App", datastar=True)
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

## 🚀 Auto-Routing System (Phase 2)

Nitro's auto-routing system dramatically reduces boilerplate by automatically generating RESTful routes from entity methods. Works with FastAPI, Flask, FastHTML, and other Python web frameworks.

### Quick Example

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.routing import action
from fastapi import FastAPI
from nitro.adapters.fastapi import configure_nitro

# Define entity with actions
class Counter(Entity, table=True):
    count: int = 0

    @action()  # Automatically routed!
    def increment(self, amount: int = 1) -> dict:
        self.count += amount
        self.save()
        return {"count": self.count}

    @action()
    def reset(self) -> dict:
        self.count = 0
        self.save()
        return {"count": 0}

# Configure app (one line!)
app = FastAPI()
configure_nitro(app, entities=[Counter])

# Routes automatically generated:
# POST /counter/{id}/increment?amount=5
# POST /counter/{id}/reset
```

**Before Auto-Routing:** 190 lines of boilerplate route handlers
**After Auto-Routing:** < 50 lines of pure business logic

### Custom Route Naming

Control your API design with custom entity names and action paths:

#### Custom Entity Names

Use `__route_name__` for plural forms or custom naming:

```python
class User(Entity):
    __route_name__ = "users"  # Plural form

    username: str = ""

    @action()
    def activate(self):
        self.is_active = True
        self.save()
        return {"status": "activated"}

# Generated URL: POST /users/{id}/activate (not /user/{id}/activate)
```

#### Custom Action Paths

Use `@action(path="...")` for cleaner URLs:

```python
class BlogPost(Entity):
    __route_name__ = "posts"

    title: str = ""
    is_published: bool = False

    @action(path="/publish")  # Custom path
    def make_public(self):
        self.is_published = True
        self.save()
        return {"status": "published"}

# Generated URL: POST /posts/{id}/publish (not /posts/{id}/make_public)
```

#### Combined Customization

```python
class BlogPost(Entity):
    __route_name__ = "posts"     # Custom entity name

    @action(path="/publish")     # Custom action path
    def make_public(self):
        ...

# Generated URL: POST /posts/{id}/publish
```

### API Versioning with Prefixes

Support multiple API versions simultaneously:

```python
# V1 API - Simple counter
configure_nitro(app, entities=[CounterV1], prefix="/api/v1")

# V2 API - Enhanced counter with new features
configure_nitro(app, entities=[CounterV2], prefix="/api/v2")

# Both versions coexist:
# POST /api/v1/counter/{id}/increment
# POST /api/v2/counter/{id}/increment
```

### Features

- **🎯 Zero Boilerplate**: Define business logic once, routes generated automatically
- **🔄 Type Safety**: Parameter extraction from type hints with Pydantic validation
- **🎨 Custom Naming**: Full control over entity names and action paths
- **📦 Works With Any Framework**: Integrates with FastAPI, Flask, FastHTML, and more
- **🔌 Plug & Play**: One-line configuration per web framework
- **📚 OpenAPI**: Automatic Swagger/ReDoc documentation (FastAPI)
- **🎭 Versioning**: API prefixes for versioning support

### Try It

Run the interactive demo:

```bash
# Custom routing demo
uvicorn examples.custom_routes_demo:app --port 8095

# API versioning demo
uvicorn examples.versioned_api_demo:app --port 8090
```

Then visit `http://localhost:8095/` for interactive documentation and examples.

### Learn More

- **📖 [Custom Route Naming Guide](docs/custom_route_naming.md)**: Complete guide with examples
- **📖 [Route Prefixes Guide](docs/route_prefixes_guide.md)**: API versioning strategies
- **🎯 [Phase 2 Design](PHASE_2_AUTO_ROUTING_DESIGN.md)**: Technical architecture
- **💡 [Examples](examples/)**: Working demo applications

## ⚡ Tailwind CSS CLI

Nitro includes a powerful CLI for Tailwind CSS integration that works with any Python web framework.

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

- **🚀 Works Everywhere**: Integrates with FastAPI, Django, Flask, FastHTML, Sanic, and any Python web framework
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

### Integration Examples

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

The Tailwind CLI runs independently of your web application, making it perfect for development workflows:

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

## Web Framework Integration Examples

### FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from nitro.utils import page_template

app = FastAPI()
page = page_template("My API", datastar=True)

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

## Documentation

Comprehensive documentation is available:

- **📖 [Tutorial](docs/TUTORIAL.md)**: Build a Todo app in 5 minutes
- **📚 [API Reference](docs/API_REFERENCE.md)**: Complete API documentation
- **🔄 [Migration Guide](examples/migration_from_starmodel.md)**: Migrate from StarModel
- **📝 [Changelog](CHANGELOG.md)**: Version history and breaking changes
- **💡 [Examples](examples/)**: Complete working applications

### Quick Start

```bash
# Install
pip install nitro-boost

# Follow 5-minute tutorial
# See docs/TUTORIAL.md
```

### Development Requirements

For development and building from source:
- **Python 3.10+**: Core runtime
- **Rust toolchain**: Required for building RustyTags (HTML generation core)
  - Install Rust: https://rustup.rs/
  - Verify: `rustc --version`
- **Maturin**: Python-Rust build tool
  - Install: `pip install maturin`

```bash
# Clone and build
git clone <repository>
cd nitro
pip install -e .
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please check the repository for contributing guidelines and open issues.

## Links

- **Repository**: https://github.com/ndendic/Nitro
- **Issues**: https://github.com/ndendic/Nitro/issues
- **Examples**: See `examples/` directory for complete applications