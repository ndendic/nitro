---
title: Tailwind CSS CLI
category: Frontend
order: 12
---

# Nitro Tailwind CSS CLI

Nitro includes a built-in CLI for working with Tailwind CSS without requiring Node.js. It downloads and manages the standalone Tailwind binary and provides convenient commands for development and production builds.

## Why Use Nitro's Tailwind CLI?

**Zero Node.js Required** - No npm, no node_modules, no package.json

**Automatic Binary Management** - Downloads and caches the correct Tailwind binary for your platform

**Smart Project Detection** - Auto-detects your project structure and configures paths

**Works with Any Framework** - FastAPI, Flask, Django, FastHTML, Starlette - all supported

## Installation

The Tailwind CLI is included with Nitro:

```bash
pip install nitro-boost
```

Verify installation:

```bash
nitro --version
nitro tw --help
```

## Commands

### `nitro tw init` - Initialize Tailwind CSS

Sets up Tailwind CSS in your project.

```bash
nitro tw init
```

**What it does:**

1. Downloads the Tailwind CSS standalone binary to `~/.nitro/cache/`
2. Creates CSS input file with `@tailwind` directives
3. Detects project structure and configures paths
4. Updates `.gitignore` to exclude generated files

**Options:**

```bash
nitro tw init --force      # Reinitialize even if files exist
nitro tw init --verbose    # Show detailed progress
```

**Output:**

```
✨ Initializing Tailwind CSS...
Created: static/css/input.css
Tailwind binary ready: ~/.nitro/cache/latest/tailwindcss-linux-x64
Updated: .gitignore

🎉 Tailwind CSS initialized!

Next steps:
  1. Run nitro tw dev to start development
  2. Run nitro tw build for production CSS
  3. Edit static/css/input.css to customize your styles
```

### `nitro tw dev` - Development Watch Mode

Watches for changes and rebuilds CSS automatically.

```bash
nitro tw dev
```

**What it does:**

- Watches all files matching content paths (default: `**/*.py`, `**/*.html`)
- Rebuilds CSS when files change
- Runs continuously until stopped with `Ctrl+C`

**Options:**

```bash
nitro tw dev --verbose     # Show detailed output
```

**Typical Workflow:**

```bash
# Terminal 1: Web server
uvicorn app:app --reload

# Terminal 2: CSS watcher
nitro tw dev
```

**Output:**

```
Checking Tailwind binary...
Starting Tailwind CSS watcher...
Press Ctrl+C to stop

Watching for changes in: /path/to/project
Rebuilding...
Done in 45ms
```

### `nitro tw build` - Production Build

Creates a minified, optimized CSS file for production.

```bash
nitro tw build
```

**What it does:**

- Scans all content files for used classes
- Removes unused CSS (tree-shaking)
- Minifies output for smallest file size
- Creates production-ready CSS

**Options:**

```bash
nitro tw build --output custom.css   # Custom output path
nitro tw build --no-minify           # Skip minification
nitro tw build --verbose             # Show details
```

**Output:**

```
Checking Tailwind binary...
Building CSS...
Build completed!

Output    static/css/output.css
Size      24.3 KB
Minified  Yes
```

## Configuration

Nitro auto-detects your project structure but allows environment variable overrides.

### Auto-Detection

Nitro looks for common directory patterns:

```python
# If static/ exists:
css_input:  static/css/input.css
css_output: static/css/output.css

# If assets/ exists:
css_input:  assets/input.css
css_output: assets/output.css

# Otherwise:
css_input:  input.css
css_output: output.css
```

### Environment Variables

Override defaults with environment variables:

```bash
# Input CSS file
export NITRO_TAILWIND_CSS_INPUT="src/styles/tailwind.css"

# Output CSS file
export NITRO_TAILWIND_CSS_OUTPUT="public/css/app.css"

# Content paths (JSON array)
export NITRO_TAILWIND_CONTENT_PATHS='["src/**/*.py", "templates/**/*.html"]'
```

Or create a `.env` file:

```env
NITRO_TAILWIND_CSS_INPUT=src/styles/tailwind.css
NITRO_TAILWIND_CSS_OUTPUT=public/css/app.css
NITRO_TAILWIND_CONTENT_PATHS=["src/**/*.py", "templates/**/*.html"]
```

### Configuration Priority

1. Environment variables (highest priority)
2. `.env` files
3. Auto-detected defaults (lowest priority)

## Binary Management

### Download Location

Binaries are cached in `~/.nitro/cache/`:

```
~/.nitro/cache/
└── latest/
    ├── tailwindcss-linux-x64          # Linux
    ├── tailwindcss-darwin-arm64       # macOS ARM
    ├── tailwindcss-darwin-x64         # macOS Intel
    └── tailwindcss-win32-x64.exe      # Windows
```

### Platform Detection

Nitro automatically downloads the correct binary for your platform:

| Platform | Architecture | Binary |
|----------|-------------|--------|
| Linux | x64 | `tailwindcss-linux-x64` |
| Linux | ARM64 | `tailwindcss-linux-arm64` |
| macOS | Intel | `tailwindcss-darwin-x64` |
| macOS | Apple Silicon | `tailwindcss-darwin-arm64` |
| Windows | x64 | `tailwindcss-win32-x64.exe` |

### Manual Binary Management

The binary manager is accessible via Python:

```python
from nitro.application.tailwind_builder.binary import TailwindBinaryManager

manager = TailwindBinaryManager()

# Get binary path (downloads if missing)
binary_path = manager.get_binary()
print(f"Binary: {binary_path}")

# Force re-download
manager.download_binary()
```

## CSS Input File

The input file is created by `nitro tw init`:

```css
/* static/css/input.css */
@import "tailwindcss";

/* Your custom CSS here */
@layer base {
  :root {
    /* Custom variables */
  }
}

@layer components {
  /* Custom components */
  .btn-special {
    @apply px-4 py-2 bg-blue-500 text-white rounded;
  }
}

@layer utilities {
  /* Custom utilities */
  .text-balance {
    text-wrap: balance;
  }
}
```

## Using with Page Component

### Include Generated CSS

```python
from nitro.infrastructure.html import Page
from rusty_tags import Link

page = Page(
    content,
    hdrs=(
        Link(rel="stylesheet", href="/static/css/output.css"),
    ),
    title="My App"
)
```

### Use Tailwind CDN (Development)

For quick prototyping, use the Tailwind CDN:

```python
from nitro.infrastructure.html import Page

page = Page(
    content,
    tailwind4=True,  # Includes Tailwind v4 CDN
    title="My App"
)
```

**Note:** CDN is great for development but use `nitro tw build` for production.

## Framework-Specific Examples

### FastAPI

```python
# app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from nitro.infrastructure.html import Page
from rusty_tags import Div, H1, Link

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    return Page(
        Div(
            H1("Hello Tailwind", cls="text-4xl font-bold text-blue-600"),
            cls="container mx-auto p-8"
        ),
        hdrs=(Link(rel="stylesheet", href="/static/css/output.css"),),
        title="FastAPI + Tailwind"
    )
```

**Run:**

```bash
# Terminal 1
uvicorn app:app --reload

# Terminal 2
nitro tw dev
```

### Flask

```python
# app.py
from flask import Flask
from nitro.infrastructure.html import Page
from rusty_tags import Div, H1, Link

app = Flask(__name__)

@app.route("/")
def index():
    return Page(
        Div(
            H1("Hello Tailwind", cls="text-4xl font-bold text-green-600"),
            cls="container mx-auto p-8"
        ),
        hdrs=(Link(rel="stylesheet", href="/static/css/output.css"),),
        title="Flask + Tailwind"
    )

if __name__ == "__main__":
    app.run(debug=True)
```

**Run:**

```bash
# Terminal 1
python app.py

# Terminal 2
nitro tw dev
```

### FastHTML

```python
# app.py
from fasthtml.common import *
from rusty_tags import Link

app, rt = fast_app()

@rt("/")
def index():
    return Html(
        Head(
            Title("FastHTML + Tailwind"),
            Link(rel="stylesheet", href="/static/css/output.css")
        ),
        Body(
            Div(
                H1("Hello Tailwind", cls="text-4xl font-bold text-purple-600"),
                cls="container mx-auto p-8"
            )
        )
    )

serve()
```

## Content Path Configuration

Tailwind scans content paths to find used classes. Configure for your project structure:

### Python-Only Project

```bash
NITRO_TAILWIND_CONTENT_PATHS='["**/*.py"]'
```

### With Templates

```bash
NITRO_TAILWIND_CONTENT_PATHS='["**/*.py", "templates/**/*.html", "templates/**/*.jinja2"]'
```

### Monorepo or Complex Structure

```bash
NITRO_TAILWIND_CONTENT_PATHS='["app/**/*.py", "components/**/*.py", "frontend/**/*.html"]'
```

## Troubleshooting

### Binary Download Fails

```bash
# Check network connection
ping github.com

# Try manual download
python -c "from nitro.application.tailwind_builder.binary import TailwindBinaryManager; TailwindBinaryManager().download_binary()"
```

### CSS Not Updating

1. Check that `nitro tw dev` is running
2. Verify content paths include your files
3. Ensure you're using classes that Tailwind recognizes (not dynamic strings)

```python
# ✅ Good - static class names
cls="text-blue-500 font-bold"

# ❌ Bad - dynamic strings (Tailwind can't detect)
color = "blue"
cls=f"text-{color}-500"  # Won't work
```

### Permission Errors

```bash
# Make binary executable (Linux/macOS)
chmod +x ~/.nitro/cache/latest/tailwindcss-*
```

### Output File Not Found

1. Check output path configuration
2. Verify parent directory exists
3. Look for errors in `nitro tw dev` output

## Advanced Usage

### Custom Tailwind Config

Create `tailwind.config.js` in your project root:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['**/*.py', 'templates/**/*.html'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff',
          500: '#0ea5e9',
          900: '#0c4a6e',
        }
      }
    }
  },
  plugins: [],
}
```

### Multiple CSS Outputs

Build different CSS files for different parts of your app:

```bash
# Main app CSS
nitro tw build --output public/css/app.css

# Admin panel CSS
export NITRO_TAILWIND_CSS_INPUT=admin/styles.css
nitro tw build --output public/css/admin.css
```

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
- name: Build CSS
  run: |
    pip install nitro-boost
    nitro tw build --no-minify  # or --minify for production
```

## Related Documentation

- [Component Library Overview](./overview.md) - Using Nitro components
- [Basecoat Styling](./basecoat-styling.md) - CSS variable system
- [Custom Themes](./custom-themes.md) - Creating custom themes

## Source Code Reference

- CLI Commands: `nitro/nitro/application/cli/tailwind_commands/`
- Init Command: `nitro/nitro/application/cli/tailwind_commands/init.py`
- Dev Command: `nitro/nitro/application/cli/tailwind_commands/dev.py`
- Build Command: `nitro/nitro/application/cli/tailwind_commands/build.py`
- Binary Manager: `nitro/nitro/application/tailwind_builder/binary.py`
