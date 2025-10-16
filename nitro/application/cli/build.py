"""Build production Tailwind CSS."""

import subprocess
from pathlib import Path

import typer
from rich.table import Table

from nitro.config import get_nitro_config
from nitro.application.tailwind_builder.binary import TailwindBinaryManager
from nitro.application.templates.css_input import generate_css_input
from nitro.application.cli.utils import console, error, success


def format_size(bytes: int) -> str:
    """Format file size in human-readable format."""
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f} KB"
    return f"{bytes / (1024 * 1024):.1f} MB"


def ensure_css_input(config) -> Path:
    """Ensure CSS input file exists."""
    input_path = config.css_input_absolute

    if not input_path.exists():
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(generate_css_input(config))
        console.print(f"[green]Created:[/green] {input_path.relative_to(config.project_root)}")

    return input_path


def run_tailwind_build(binary_path: Path, input_css: Path, output_css: Path, project_root: Path, minify: bool = True) -> bool:
    """Run Tailwind build command."""
    cmd = [
        str(binary_path),
        "--input", str(input_css),
        "--output", str(output_css),
    ]

    if minify:
        cmd.append("--minify")

    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            error(f"Tailwind build failed: {result.stderr or result.stdout}")
            return False

        return True
    except Exception as e:
        error(f"Failed to run Tailwind: {e}")
        return False


def build_command(
    output: str | None = typer.Option(None, "--output", "-o", help="CSS output path"),
    minify: bool = typer.Option(True, "--minify/--no-minify", help="Minify CSS"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show details"),
) -> None:
    """Build production CSS."""

    try:
        config = get_nitro_config()

        # Override output path if specified
        if output:
            from nitro.config import NitroConfig, TailwindConfig
            output_path = Path(output)
            if not output_path.suffix:
                output_path = output_path.with_suffix(".css")

            # Create new config with custom output
            custom_tailwind = TailwindConfig(
                css_input=config.tailwind.css_input,
                css_output=output_path, 
                content_paths=config.tailwind.content_paths
            )
            config = NitroConfig(
                project_root=config.project_root,
                tailwind=custom_tailwind
            )

        # Get or download Tailwind binary
        console.print("[cyan]Checking Tailwind binary...[/cyan]")
        manager = TailwindBinaryManager()
        binary_path = Path(manager.get_binary())

        if verbose:
            console.print(f"[dim]Using binary: {binary_path}[/dim]")

        # Ensure CSS files exist
        input_css = ensure_css_input(config)
        output_css = config.css_output_absolute

        # Create output directory
        output_css.parent.mkdir(parents=True, exist_ok=True)

        if verbose:
            console.print(f"[dim]Input: {input_css.relative_to(config.project_root)}[/dim]")
            console.print(f"[dim]Output: {output_css.relative_to(config.project_root)}[/dim]")

        # Build CSS
        console.print("[cyan]Building CSS...[/cyan]")

        success_build = run_tailwind_build(binary_path, input_css, output_css, config.project_root, minify)

        if not success_build:
            raise typer.Exit(1)

        if not output_css.exists():
            error("Build completed but output file not found")
            raise typer.Exit(1)

        # Show results
        success("Build completed!")

        # Show stats
        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Output", str(output_css.relative_to(config.project_root)))

        try:
            file_size = output_css.stat().st_size
            table.add_row("Size", format_size(file_size))
        except Exception:
            pass

        table.add_row("Minified", "Yes" if minify else "No")

        console.print(table)

    except Exception as e:
        error(f"Build error: {e}")
        raise typer.Exit(1) from e