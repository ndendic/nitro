"""Boost command for initializing new Nitro projects."""

from pathlib import Path
import typer

from nitro.cli.utils import console, success, error, info
from nitro.cli.templates import generate_boost_base, generate_env_example


def validate_boost_project(root: Path, force: bool = False) -> None:
    """Check for existing files that would be overwritten."""
    conflicts = []

    files_to_check = [
        (root / "base.py", "base.py template"),
        (root / ".env.example", ".env.example config"),
    ]

    for file_path, description in files_to_check:
        if file_path.exists():
            conflicts.append(f"{file_path.name} ({description})")

    if conflicts and not force:
        error(
            "Project appears to already be boosted. Found:\n"
            + "\n".join(f"  - {item}" for item in conflicts)
        )
        info("Use --force to overwrite existing files")
        raise typer.Exit(1)


def write_boost_files(root: Path, verbose: bool = False) -> None:
    """Generate and write boost files to project root."""
    files = [
        ("base.py", generate_boost_base()),
        (".env.example", generate_env_example()),
    ]

    for filename, content in files:
        file_path = root / filename
        file_path.write_text(content)
        if verbose:
            console.print(f"[green]Created:[/green] {filename}")


def boost_command(
    force: bool = typer.Option(False, "--force", help="Force overwrite existing files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
) -> None:
    """Initialize a new Nitro project with base template files.

    Creates base.py and .env.example in the current directory.
    Configure your environment, then run 'nitro tw init' to set up Tailwind CSS.
    """
    try:
        root = Path.cwd()

        if verbose:
            console.print(f"[blue]Initializing Nitro project in:[/blue] {root}")

        # Check for conflicts
        validate_boost_project(root, force)

        console.print("\n[green]Nitro Boost![/green]")

        # Generate files
        write_boost_files(root, verbose)

        console.print("\n[green]Project initialized![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Edit [blue].env.example[/blue] and save as [blue].env[/blue]")
        console.print("  2. Run [blue]nitro tw init[/blue] to initialize Tailwind CSS")
        console.print("  3. Edit [blue]base.py[/blue] to configure [blue]wrap_in[/blue] for your framework")
        console.print("\n[dim]Tip: Check the comments in base.py for framework-specific examples[/dim]")

    except typer.Exit:
        raise
    except Exception as e:
        error(f"Boost failed: {e}")
        raise typer.Exit(1) from e
