---
title: Installation
category: Getting Started
order: 1
---

# Installation

Get started with Nitro Framework in under a minute.

## Requirements

- **Python 3.10 or higher**
- **pip** package manager

## Quick Install

Install Nitro from PyPI:

```bash
pip install nitro-boost
```

## Development Installation

For development with additional dependencies (FastAPI, examples, etc.):

```bash
pip install nitro-boost[dev]
```

This includes:
- FastAPI for running examples
- Additional development tools
- Testing dependencies

## Verify Installation

Check that Nitro is installed correctly:

```bash
nitro --version
```

You should see output like:

```
Nitro CLI version X.X.X
```

## Initialize Tailwind CSS (Optional)

If you plan to use Tailwind CSS for styling, initialize it:

```bash
nitro tw init
```

This will:
- Download the Tailwind CSS standalone binary to `~/.nitro/cache/`
- Create a basic `tailwind.config.js` if one doesn't exist
- Set up input/output CSS file paths

**Note:** Tailwind CSS initialization is optional. You can skip this if you're using a different CSS framework or building APIs without UI.

## Configuration

Nitro uses environment variables for configuration. Create a `.env` file in your project root:

```bash
# Database configuration (default: sqlite:///nitro.db)
NITRO_DB_URL=sqlite:///nitro.db

# Tailwind CSS configuration
NITRO_TAILWIND_CSS_INPUT=static/css/input.css
NITRO_TAILWIND_CSS_OUTPUT=static/css/output.css
NITRO_TAILWIND_CONTENT_PATHS=["**/*.py", "**/*.html"]
```

**Default values** are provided, so you only need to create a `.env` file if you want to customize these settings.

## Database Setup

If you're using SQL entities, initialize the database:

```python
from nitro.domain.entities.base_entity import Entity

# Initialize database tables
Entity._repository.init_db()
```

Or use the CLI command (if available):

```bash
nitro db init
```

## Troubleshooting

### Import errors

If you encounter import errors, ensure you're using Python 3.10+:

```bash
python --version
```

### Tailwind binary download issues

If Tailwind CSS binary download fails, try manually downloading from the [Tailwind CLI releases](https://github.com/tailwindlabs/tailwindcss/releases) and placing it in `~/.nitro/cache/latest/`.

### Database connection errors

Make sure your `NITRO_DB_URL` is correctly formatted:

- SQLite: `sqlite:///path/to/database.db`
- PostgreSQL: `postgresql://user:password@host:port/database`
- MySQL: `mysql://user:password@host:port/database`

## Next Steps

Now that Nitro is installed, you're ready to build your first application:

- [Quickstart Tutorial](quickstart.md) - Build a todo app in 5 minutes
- [Entity Overview](../entity/overview.md) - Learn about entity-centric design
- [Framework Integration](../frameworks/overview.md) - Integrate with FastAPI, Flask, or FastHTML

## IDE Setup (Optional)

For the best development experience, we recommend:

### VS Code

Install these extensions:
- Python (Microsoft)
- Pylance for type hints and autocomplete

### PyCharm

PyCharm works out of the box with Nitro's type hints.

### Type Hints

Nitro has full type hint support for IDE autocomplete:

```python
from nitro.domain.entities.base_entity import Entity

todo: Todo = Todo.get("1")  # IDE knows all methods
todos: list[Todo] = Todo.all()
```

## What's Installed?

When you install Nitro, you get:

- **Entity System** - Rich domain models with Active Record pattern
- **Repository Layer** - SQL, memory, and custom persistence backends
- **Event System** - Blinker-based event handling
- **HTML Generation** - RustyTags for high-performance HTML
- **Datastar SDK** - Reactive UI components
- **CLI Tools** - Tailwind CSS integration, database migrations
- **Configuration** - Pydantic-based settings management

Ready to build? Continue to the [Quickstart Tutorial](quickstart.md).
