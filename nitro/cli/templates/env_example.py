"""Environment example template for new Nitro projects."""

ENV_EXAMPLE_TEMPLATE = '''\
# =============================================================================
# Nitro Configuration
# =============================================================================
# Copy this file to .env and customize for your project.
# All variables are optional - defaults are shown below.
#
# For more information, see: https://nitro.systems/docs/configuration
# =============================================================================

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------

# Database connection URL
# Supports: SQLite, PostgreSQL, MySQL, and other SQLAlchemy-compatible databases
# Examples:
#   sqlite:///nitro.db              (SQLite - default)
#   sqlite:///./data/app.db         (SQLite in subdirectory)
#   postgresql://user:pass@localhost/dbname
#   mysql://user:pass@localhost/dbname
NITRO_DB_URL=sqlite:///nitro.db

# -----------------------------------------------------------------------------
# Tailwind CSS Configuration
# -----------------------------------------------------------------------------

# Path to Tailwind CSS input file (relative to project root)
# This file is processed by Tailwind CLI to generate output CSS
NITRO_TAILWIND_CSS_INPUT=static/css/input.css

# Path to Tailwind CSS output file (relative to project root)
# This is the compiled CSS file you should link in your HTML
NITRO_TAILWIND_CSS_OUTPUT=static/css/output.css

# Content paths for Tailwind to scan for class names (JSON array)
# Tailwind scans these paths to determine which CSS classes to include
# Use glob patterns to match files
NITRO_TAILWIND_CONTENT_PATHS=["**/*.py", "**/*.html", "**/*.jinja2", "!**/__pycache__/**", "!**/test_*.py"]
'''


def generate_env_example() -> str:
    """Generate the .env.example template content."""
    return ENV_EXAMPLE_TEMPLATE
