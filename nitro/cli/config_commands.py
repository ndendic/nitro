"""Nitro CLI commands for configuration management."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rich_print

from nitro.config import get_nitro_config, NitroConfig, TailwindConfig

config_app = typer.Typer(name="config", help="Configuration management")
console = Console()

# Map of env var names to their descriptions
ENV_VAR_DESCRIPTIONS = {
    "NITRO_DB_URL": "Database connection URL",
    "NITRO_PROJECT_ROOT": "Project root directory",
    "NITRO_TAILWIND_CSS_INPUT": "Path to Tailwind input CSS file",
    "NITRO_TAILWIND_CSS_OUTPUT": "Path to Tailwind output CSS file",
    "NITRO_TAILWIND_CONTENT_PATHS": "JSON array of glob patterns for Tailwind to scan",
}


def _get_config_source(field_name: str, config: NitroConfig) -> str:
    """Determine the source of a config value (default, env, or file)."""
    import os

    env_map = {
        "db_url": "NITRO_DB_URL",
        "project_root": "NITRO_PROJECT_ROOT",
    }
    env_var = env_map.get(field_name)
    if env_var and os.environ.get(env_var):
        return "env"

    # Check if any .env files exist and might be providing values
    env_files = [".env", ".env.local", ".env.prod"]
    root = config.project_root
    for env_file in env_files:
        env_path = root / env_file
        if env_path.exists():
            try:
                content = env_path.read_text()
                if env_var and f"{env_var}=" in content:
                    return f"file ({env_file})"
            except Exception:
                pass

    return "default"


def _get_tailwind_config_source(field_name: str, config: NitroConfig) -> str:
    """Determine the source of a tailwind config value."""
    import os

    env_map = {
        "css_input": "NITRO_TAILWIND_CSS_INPUT",
        "css_output": "NITRO_TAILWIND_CSS_OUTPUT",
        "content_paths": "NITRO_TAILWIND_CONTENT_PATHS",
    }
    env_var = env_map.get(field_name)
    if env_var and os.environ.get(env_var):
        return "env"

    env_files = [".env", ".env.local", ".env.prod"]
    root = config.project_root
    for env_file in env_files:
        env_path = root / env_file
        if env_path.exists():
            try:
                content = env_path.read_text()
                if env_var and f"{env_var}=" in content:
                    return f"file ({env_file})"
            except Exception:
                pass

    return "default"


@config_app.command("show")
def show(
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Display all current configuration values."""
    config = get_nitro_config()

    if output_json:
        data = {
            "project_root": str(config.project_root),
            "db_url": config.db_url,
            "tailwind": {
                "css_input": str(config.tailwind.css_input),
                "css_output": str(config.tailwind.css_output),
                "content_paths": config.tailwind.content_paths,
                "css_input_absolute": str(config.css_input_absolute),
                "css_output_absolute": str(config.css_output_absolute),
            },
        }
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(title="Nitro Configuration", show_header=True, header_style="bold blue")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Source", style="dim")

    table.add_row(
        "project_root",
        str(config.project_root),
        _get_config_source("project_root", config),
    )
    table.add_row(
        "db_url",
        config.db_url,
        _get_config_source("db_url", config),
    )
    table.add_row(
        "tailwind.css_input",
        str(config.tailwind.css_input),
        _get_tailwind_config_source("css_input", config),
    )
    table.add_row(
        "tailwind.css_output",
        str(config.tailwind.css_output),
        _get_tailwind_config_source("css_output", config),
    )
    table.add_row(
        "tailwind.content_paths",
        json.dumps(config.tailwind.content_paths),
        _get_tailwind_config_source("content_paths", config),
    )
    table.add_row(
        "css_input_absolute",
        str(config.css_input_absolute),
        "computed",
    )
    table.add_row(
        "css_output_absolute",
        str(config.css_output_absolute),
        "computed",
    )

    console.print(table)


@config_app.command("check")
def check() -> None:
    """Validate the current configuration."""
    config = get_nitro_config()
    issues = []

    rich_print("[bold]Checking Nitro configuration...[/bold]\n")

    # Check db_url
    db_url = config.db_url
    if db_url.startswith("sqlite:///"):
        db_path_str = db_url.replace("sqlite:///", "")
        if db_path_str == ":memory:":
            rich_print("[green]  db_url: in-memory SQLite (OK)[/green]")
        else:
            db_path = Path(db_path_str)
            if not db_path.is_absolute():
                db_path = config.project_root / db_path
            if db_path.exists():
                rich_print(f"[green]  db_url: SQLite file exists at {db_path}[/green]")
            else:
                rich_print(f"[yellow]  db_url: SQLite file not found at {db_path} (will be created on first use)[/yellow]")
    else:
        rich_print(f"[blue]  db_url: {db_url} (non-SQLite, cannot verify connectivity)[/blue]")

    # Check tailwind css_input path
    css_input = config.css_input_absolute
    if css_input.exists():
        rich_print(f"[green]  tailwind.css_input: found at {css_input}[/green]")
    else:
        rich_print(f"[yellow]  tailwind.css_input: not found at {css_input} (run 'nitro tw init' to create)[/yellow]")
        issues.append(f"Tailwind CSS input file missing: {css_input}")

    # Check tailwind css_output path
    css_output = config.css_output_absolute
    if css_output.exists():
        rich_print(f"[green]  tailwind.css_output: found at {css_output}[/green]")
    else:
        rich_print(f"[yellow]  tailwind.css_output: not found at {css_output} (will be generated by 'nitro tw build')[/yellow]")

    # Check .env files
    env_files = [".env", ".env.local", ".env.prod"]
    found_env = []
    for env_file in env_files:
        env_path = config.project_root / env_file
        if env_path.exists():
            found_env.append(env_file)

    if found_env:
        rich_print(f"[green]  .env files: found {', '.join(found_env)}[/green]")
    else:
        rich_print("[dim]  .env files: none found (using defaults and environment variables)[/dim]")

    # Summary
    rich_print("")
    if issues:
        rich_print(f"[yellow]Found {len(issues)} warning(s):[/yellow]")
        for issue in issues:
            rich_print(f"  [yellow]- {issue}[/yellow]")
        raise typer.Exit(code=1)
    else:
        rich_print("[green]Configuration looks good.[/green]")


@config_app.command("env")
def env() -> None:
    """Show environment variable reference for Nitro configuration."""
    import os

    config = get_nitro_config()

    # Show which .env files were loaded
    env_files = [".env", ".env.local", ".env.prod"]
    loaded = []
    for env_file in env_files:
        env_path = config.project_root / env_file
        if env_path.exists():
            loaded.append(str(env_path))

    if loaded:
        rich_print(f"[dim]Loaded .env files: {', '.join(loaded)}[/dim]\n")
    else:
        rich_print("[dim]No .env files found in project root.[/dim]\n")

    table = Table(
        title="Supported Environment Variables",
        show_header=True,
        header_style="bold blue",
    )
    table.add_column("Variable", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Current Value", style="yellow")

    for var, description in ENV_VAR_DESCRIPTIONS.items():
        current = os.environ.get(var, "[dim](not set)[/dim]")
        table.add_row(var, description, current)

    console.print(table)
