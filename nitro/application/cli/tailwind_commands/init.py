import shutil
from pathlib import Path

import typer
from rich.progress import track

from nitro.config import NitroConfig, get_nitro_config
from nitro.application.tailwind_builder.binary import TailwindBinaryManager
from nitro.application.cli.utils import confirm, console, error, info, success

# Path to the CSS templates folder
CSS_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "css"


def validate_tailwind_project(config: NitroConfig, force: bool = False) -> None:
    """Validate project for Tailwind initialization using actual config values."""
    conflicts = []

    # Check for existing files based on actual config (including env overrides)
    files_to_check = [
        (config.css_input_absolute, "CSS input file"),
        (config.css_output_absolute, "CSS output file"),
        (config.css_input_absolute.parent / "basecoat", "BaseCoat components folder"),
    ]

    # Also check for common Tailwind config files
    common_config_files = [
        (config.project_root / "tailwind.config.js", "Tailwind config (JS)"),
        (config.project_root / "tailwind.config.ts", "Tailwind config (TS)"),
    ]

    # Check configured paths
    for file_path, description in files_to_check:
        if file_path.exists():
            rel_path = file_path.relative_to(config.project_root)
            conflicts.append(f"{rel_path} ({description})")

    # Check common config files (optional)
    for file_path, description in common_config_files:
        if file_path.exists():
            rel_path = file_path.relative_to(config.project_root)
            conflicts.append(f"{rel_path} ({description})")

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
        config.css_input_absolute.parent,  # Input CSS directory
        config.css_dir_absolute,           # Output CSS directory
    ]

    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            if verbose:
                console.print(
                    f"[green]Created:[/green] {d.relative_to(config.project_root)}"
                )


def copy_css_folder(config: NitroConfig, verbose: bool = False) -> None:
    """Copy the CSS templates folder to the project."""
    # Destination is the parent directory of the css_input file
    dest_dir = config.css_input_absolute.parent

    # Ensure destination exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy each item from the CSS templates directory
    for item in CSS_TEMPLATES_DIR.iterdir():
        dest_path = dest_dir / item.name
        if item.is_dir():
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(item, dest_path)
            if verbose:
                console.print(f"[green]Copied:[/green] {dest_path.relative_to(config.project_root)}/")
        else:
            shutil.copy2(item, dest_path)
            if verbose:
                console.print(f"[green]Copied:[/green] {dest_path.relative_to(config.project_root)}")


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

        validate_tailwind_project(config, force)

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
            (f"Copying CSS templates to {config.css_input_absolute.parent.relative_to(config.project_root)}", lambda: copy_css_folder(config, verbose)),
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
        console.print(f"  4. BaseCoat components available in [blue]{config.css_input_absolute.parent.relative_to(config.project_root)}/basecoat/[/blue]")

    except Exception as e:
        error(f"Initialization failed: {e}")
        raise typer.Exit(1) from e
