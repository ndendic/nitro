---
title: CLI Reference
category: Reference
order: 2
---

# CLI Reference

The Nitro CLI provides commands for managing Tailwind CSS integration and database migrations. All commands use the `nitro` executable.

## Installation

The CLI is automatically available after installing Nitro:

```bash
pip install -e .
```

## General Commands

### `--version`

Display the current version of Nitro.

```bash
nitro --version
```

**Output:**
```
nitro 0.1.0
```

### `--help`

Show help information for available commands.

```bash
nitro --help
```

## Tailwind CSS Commands

The `tw` subcommand provides Tailwind CSS integration without requiring Node.js.

### `nitro tw init`

Initialize Tailwind CSS in your Nitro project.

**Syntax:**
```bash
nitro tw init [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--force` | - | Force initialization (overwrite existing files) | `False` |
| `--verbose` | `-v` | Show detailed output during initialization | `False` |

**What it does:**

1. Downloads the Tailwind CSS standalone binary to `~/.nitro/cache/`
2. Creates CSS directories (`static/css/` or `assets/` based on project structure)
3. Generates a CSS input file with Tailwind directives
4. Updates `.gitignore` with Nitro-specific entries

**Examples:**

```bash
# Basic initialization
nitro tw init

# Force reinitialize existing setup
nitro tw init --force

# Show detailed progress
nitro tw init --verbose
```

**Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `NITRO_TAILWIND_CSS_INPUT` | Path to Tailwind input CSS file | `static/css/input.css` |
| `NITRO_TAILWIND_CSS_OUTPUT` | Path to Tailwind output CSS file | `static/css/output.css` |
| `NITRO_TAILWIND_CONTENT_PATHS` | JSON array of glob patterns to scan | `["**/*.py", "**/*.html", "**/*.jinja2"]` |

**Auto-detection:**
- If `static/` exists: Uses `static/css/input.css` → `static/css/output.css`
- If `assets/` exists: Uses `assets/input.css` → `assets/output.css`
- Otherwise: Uses `input.css` → `output.css`

### `nitro tw dev`

Start Tailwind CSS in watch mode for development.

**Syntax:**
```bash
nitro tw dev [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--verbose` | `-v` | Show detailed output including binary path and config | `False` |

**What it does:**

1. Checks for Tailwind binary (downloads if missing)
2. Creates CSS input file if it doesn't exist
3. Starts Tailwind in watch mode
4. Automatically rebuilds CSS when files change
5. Continues running until stopped with `Ctrl+C`

**Examples:**

```bash
# Start development watcher
nitro tw dev

# Show detailed status information
nitro tw dev --verbose
```

**Output:**
```
Checking Tailwind binary...
Starting Tailwind CSS watcher...
Press Ctrl+C to stop

Watching for changes in: /path/to/project
```

### `nitro tw build`

Build production CSS with optional minification.

**Syntax:**
```bash
nitro tw build [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Custom CSS output path | Uses config default |
| `--minify/--no-minify` | - | Enable/disable CSS minification | `True` |
| `--verbose` | `-v` | Show detailed build information | `False` |

**What it does:**

1. Checks for Tailwind binary (downloads if missing)
2. Creates CSS input file if it doesn't exist
3. Builds optimized production CSS
4. Shows file size and build statistics

**Examples:**

```bash
# Build production CSS (minified)
nitro tw build

# Build without minification
nitro tw build --no-minify

# Build to custom location
nitro tw build --output dist/styles.css

# Show detailed build info
nitro tw build --verbose
```

**Output:**
```
Checking Tailwind binary...
Building CSS...
Build completed!

┌──────────┬────────────────────┐
│ Output   │ static/css/output.css │
│ Size     │ 12.4 KB            │
│ Minified │ Yes                │
└──────────┴────────────────────┘
```

## Database Commands

The `db` subcommand provides database migration management using Alembic.

### `nitro db init`

Initialize Alembic migrations in your project.

**Syntax:**
```bash
nitro db init [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--directory` | `-d` | Directory where to initialize Alembic | `.` (current directory) |

**What it does:**

1. Creates `migrations/` directory with Alembic configuration
2. Creates `migrations/versions/` directory for migration files
3. Generates `alembic.ini` configuration file
4. Copies template files (`env.py`, `README`, `script.py.mako`)

**Examples:**

```bash
# Initialize in current directory
nitro db init

# Initialize in specific directory
nitro db init --directory /path/to/project
```

**Output:**
```
Successfully initialized Alembic in migrations directory!
Please make sure to add your models to migrations/env.py file before running migrations!
```

**Created structure:**
```
.
├── alembic.ini
└── migrations/
    ├── env.py
    ├── README
    ├── script.py.mako
    └── versions/
```

### `nitro db migrations`

Generate a new Alembic migration file.

**Syntax:**
```bash
nitro db migrations [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--message` | `-m` | Migration message/description | `"Pushing changes"` |
| `--autogenerate/--no-autogenerate` | - | Auto-detect model changes | `True` |

**What it does:**

1. Analyzes your SQLModel entities
2. Compares with current database schema
3. Generates migration file with detected changes
4. Saves migration to `migrations/versions/`

**Examples:**

```bash
# Auto-generate migration with custom message
nitro db migrations -m "Add user table"

# Generate empty migration template
nitro db migrations --no-autogenerate -m "Custom migration"

# Use default message
nitro db migrations
```

**Output:**
```
Generating Alembic migration with message: Add user table
Migration created successfully!
```

### `nitro db migrate`

Apply pending database migrations.

**Syntax:**
```bash
nitro db migrate [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--revision` | `-r` | Revision to upgrade/downgrade to | `"head"` |

**What it does:**

1. Reads pending migration files
2. Applies migrations to the database
3. Updates Alembic version tracking

**Examples:**

```bash
# Upgrade to latest version
nitro db migrate

# Upgrade one revision
nitro db migrate -r +1

# Downgrade one revision
nitro db migrate -r -1

# Downgrade all migrations
nitro db migrate -r base
```

**Output:**
```
Applying database migrations...
Migrations applied successfully!
```

## Configuration Files

### `.env` File

Nitro loads configuration from `.env`, `.env.local`, or `.env.prod` files (in order):

```bash
# Database configuration
NITRO_DB_URL=sqlite:///nitro.db

# Tailwind CSS configuration
NITRO_TAILWIND_CSS_INPUT=static/css/input.css
NITRO_TAILWIND_CSS_OUTPUT=static/css/output.css
NITRO_TAILWIND_CONTENT_PATHS=["**/*.py", "**/*.html", "**/*.jinja2"]
```

### Environment Variables

All configuration can be overridden via environment variables with the `NITRO_` prefix:

**General:**
- `NITRO_DB_URL` - Database connection string (default: `sqlite:///nitro.db`)

**Tailwind:**
- `NITRO_TAILWIND_CSS_INPUT` - Input CSS file path
- `NITRO_TAILWIND_CSS_OUTPUT` - Output CSS file path
- `NITRO_TAILWIND_CONTENT_PATHS` - JSON array of glob patterns

**Example:**
```bash
export NITRO_DB_URL=postgresql://user:pass@localhost/mydb
export NITRO_TAILWIND_CSS_OUTPUT=dist/styles.css
nitro tw build
```

## Common Workflows

### Initial Project Setup

```bash
# 1. Initialize Tailwind CSS
nitro tw init

# 2. Initialize database migrations
nitro db init

# 3. Start development
nitro tw dev
```

### Development Workflow

```bash
# Terminal 1: Run your web application
python app.py

# Terminal 2: Watch CSS changes
nitro tw dev
```

### Production Build

```bash
# Build optimized CSS
nitro tw build

# Apply database migrations
nitro db migrate
```

### Database Migration Workflow

```bash
# 1. Modify your Entity models
# 2. Generate migration
nitro db migrations -m "Add new fields to User"

# 3. Review migration file in migrations/versions/
# 4. Apply migration
nitro db migrate
```

## Troubleshooting

### Tailwind binary not found

If the Tailwind binary download fails, manually download from:
```
https://github.com/tailwindlabs/tailwindcss/releases/latest
```

Place it at: `~/.nitro/cache/latest/tailwindcss-{platform}-{arch}`

### CSS not updating

1. Check that `nitro tw dev` is running
2. Verify file paths in output match your project structure
3. Check content paths include your files
4. Restart the watcher

### Migration errors

1. Ensure `nitro db init` was run first
2. Check that models are imported in `migrations/env.py`
3. Verify database connection string in `NITRO_DB_URL`
4. Check Alembic logs for detailed errors

## Exit Codes

All commands use standard exit codes:
- `0` - Success
- `1` - Error (with detailed error message)

## Related Documentation

- [Getting Started Guide](/getting-started/installation.md)
- [Entity Reference](/entity/base.md)
- [Configuration Guide](/reference/configuration.md)
