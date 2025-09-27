from pathlib import Path

import typer
from rich.progress import track

from ..config import NitroConfig, get_nitro_config
from ..css.binary import TailwindBinaryManager
from ..templates.css_input import generate_css_input
from .utils import confirm, console, error, info, success


def validate_tailwind_project(root: Path, force: bool = False) -> None:
    conflicts = []

    # Check for existing Tailwind files
    tailwind_files = ["input.css", "tailwind.config.js", "static/css/input.css", "static/css/nitro.css"]

    for file_path in tailwind_files:
        path = root / file_path
        if path.exists():
            conflicts.append(f"{file_path}")

    if conflicts and not force:
        error(
            "Tailwind appears to already be initialized. Found:\n"
            + "\n".join(f"  • {item}" for item in conflicts)
        )
        info("Use --force to reinitialize anyway")
        raise typer.Exit(1)


def setup_css_directories(config: NitroConfig, verbose: bool = False) -> None:
    """Create necessary directories for Tailwind CSS."""
    dirs = [
        config.css_dir_absolute,
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        if verbose:
            console.print(
                f"[green]Created:[/green] {d.relative_to(config.project_root)}"
            )


def create_css_input(config: NitroConfig, verbose: bool = False) -> None:
    """Create Tailwind CSS input file."""
    input_path = config.css_input_absolute
    input_path.write_text(generate_css_input(config))
    if verbose:
        console.print(f"[green]Created:[/green] {input_path.relative_to(config.project_root)}")


def download_tailwind_binary(verbose: bool = False) -> Path:
    """Download Tailwind CSS binary."""
    try:
        manager = TailwindBinaryManager()
        binary_path = manager.get_binary()
        if verbose:
            success(f"Tailwind binary ready: {binary_path}")
        return binary_path
    except Exception as e:
        error(f"Failed to download Tailwind binary: {e}")
        raise typer.Exit(1) from e


def create_gitignore_entries(config: NitroConfig, verbose: bool = False) -> None:
    """Add Nitro-specific entries to .gitignore."""
    gitignore = config.project_root / ".gitignore"
    nitro_ignores = [
        "\n# Nitro generated files",
        str(config.tailwind.css_output),
        "*.css.map",
        "",
        "# Nitro cache",
        ".nitro/",
        "",
    ]

    content = gitignore.read_text() if gitignore.exists() else ""

    if "# Nitro generated files" not in content:
        if content and not content.endswith("\n"):
            content += "\n"
        gitignore.write_text(content + "\n".join(nitro_ignores))
        if verbose:
            console.print(
                f"[green]{'Updated' if content else 'Created'}:[/green] .gitignore"
            )
    elif verbose:
        console.print("[yellow]Skipped:[/yellow] .gitignore (Nitro patterns exist)")


def init_command(
    force: bool = typer.Option(False, "--force", help="Force initialization"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show details"),
) -> None:
    """Initialize Tailwind CSS in a Nitro project."""
    try:
        root = Path.cwd()

        if verbose:
            console.print(f"[blue]Initializing Tailwind CSS in:[/blue] {root}")

        config = get_nitro_config(root)

        if verbose:
            console.print(f"[dim]CSS input:[/dim] {config.tailwind.css_input}")
            console.print(f"[dim]CSS output:[/dim] {config.tailwind.css_output}")

        validate_tailwind_project(root, force)

        if not force and config.css_output_absolute.exists():
            console.print(
                f"\n[yellow]Will overwrite:[/yellow]\n  • {config.tailwind.css_output}"
            )
            if not confirm("\nProceed?", default=True):
                info("Cancelled")
                raise typer.Exit()

        console.print("\n[green]✨ Initializing Tailwind CSS...[/green]")

        steps = [
            ("Creating CSS directories", lambda: setup_css_directories(config, verbose)),
            ("Downloading Tailwind binary", lambda: download_tailwind_binary(verbose)),
            ("Creating CSS input file", lambda: create_css_input(config, verbose)),
            ("Updating .gitignore", lambda: create_gitignore_entries(config, verbose)),
        ]

        if verbose:
            for name, func in steps:
                console.print(f"[blue]{name}...[/blue]")
                func()
        else:
            for _, func in track(steps, description="Initializing..."):
                func()

        console.print("\n[green]🎉 Tailwind CSS initialized![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Run [blue]nitro tw dev[/blue] to start development")
        console.print("  2. Run [blue]nitro tw build[/blue] for production CSS")
        console.print(f"  3. Edit [blue]{config.tailwind.css_input}[/blue] to customize your styles")

    except Exception as e:
        error(f"Initialization failed: {e}")
        raise typer.Exit(1) from e
