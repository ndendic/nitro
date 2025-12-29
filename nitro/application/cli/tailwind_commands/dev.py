"""Tailwind CSS development watcher."""

import subprocess
import time
from pathlib import Path

import typer
from rich.panel import Panel

from nitro.config import get_nitro_config
from nitro.application.tailwind_builder.binary import TailwindBinaryManager
from nitro.application.templates.css_input import generate_css_input
from nitro.application.cli.utils import console, error, success


def ensure_css_input(config) -> Path:
    """Ensure CSS input file exists."""
    input_path = config.css_input_absolute

    if not input_path.exists():
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(generate_css_input(config))
        console.print(f"[green]Created:[/green] {input_path.relative_to(config.project_root)}")

    return input_path


def run_tailwind_watch(binary_path: Path, input_css: Path, output_css: Path, project_root: Path):
    """Run Tailwind in watch mode."""
    cmd = [
        str(binary_path),
        "--input", str(input_css),
        "--output", str(output_css),
        "--watch",
    ]

    console.print(f"[cyan]Running:[/cyan] {' '.join(cmd[1:])}")  # Hide full binary path for cleaner output
    console.print(f"[dim]Watching for changes in: {project_root}[/dim]")

    try:
        # Run Tailwind in watch mode - it will keep running until interrupted
        process = subprocess.run(cmd, cwd=project_root, check=False)
        return process.returncode
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping Tailwind watcher...[/yellow]")
        return 0


def show_dev_status(config, input_css: Path, output_css: Path):
    """Show development status information."""
    from rich.table import Table

    table = Table(title="Nitro Tailwind CSS Watcher", show_header=False)
    table.add_column(style="cyan")
    table.add_column(style="green")

    table.add_row("Input CSS", str(input_css.relative_to(config.project_root)))
    table.add_row("Output CSS", str(output_css.relative_to(config.project_root)))
    table.add_row("Project Root", str(config.project_root))
    table.add_row("Content Paths", ", ".join(config.tailwind.content_paths))

    console.print(Panel(table, border_style="green"))


def dev_command(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """Start Tailwind CSS in watch mode."""

    try:
        config = get_nitro_config()

        # Get or download Tailwind binary
        console.print("[cyan]Checking Tailwind binary...[/cyan]")
        manager = TailwindBinaryManager()
        binary_path = Path(manager.get_binary())

        if verbose:
            console.print(f"[dim]Using binary: {binary_path}[/dim]")

        # Ensure CSS files exist
        input_css = ensure_css_input(config)
        output_css = config.css_output_absolute

        # Show status
        if verbose:
            show_dev_status(config, input_css, output_css)

        console.print("\n[green]Starting Tailwind CSS watcher...[/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        # Run Tailwind watcher
        exit_code = run_tailwind_watch(binary_path, input_css, output_css, config.project_root)

        if exit_code == 0:
            success("Tailwind watcher stopped")
        else:
            error(f"Tailwind watcher exited with code {exit_code}")
            raise typer.Exit(exit_code)

    except Exception as e:
        error(f"Dev watcher error: {e}")
        raise typer.Exit(1) from e