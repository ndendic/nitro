"""Boost command for initializing new Nitro projects."""

from enum import Enum
from pathlib import Path
import typer
from rich.prompt import Prompt

from nitro.cli.utils import console, error, info
from nitro.cli.templates import (
    generate_boost_base,
    generate_boost_components,
    generate_boost_main,
    generate_env_example,
)


class Framework(str, Enum):
    sanic = "sanic"
    fastapi = "fastapi"


TEMPLATE_CHOICES = {
    "1": ("blank", "Blank"),
    "2": ("app", "App (sidebar + navbar)"),
}


def prompt_template() -> str:
    """Interactive template selection using Rich prompt."""
    console.print("\n[bold]Select a template:[/bold]")
    for key, (_, label) in TEMPLATE_CHOICES.items():
        console.print(f"  [cyan]{key}[/cyan]) {label}")

    choice = Prompt.ask(
        "\nTemplate",
        choices=list(TEMPLATE_CHOICES.keys()),
        default="1",
    )
    return TEMPLATE_CHOICES[choice][0]


def validate_boost_project(root: Path, force: bool = False) -> None:
    """Check for existing files that would be overwritten."""
    conflicts = []

    files_to_check = [
        (root / "main.py", "main.py app entry"),
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


def write_boost_files(
    root: Path, framework: str, template: str, verbose: bool = False
) -> None:
    """Generate and write boost files to project root."""
    # Ensure static dir exists for static file serving
    static_dir = root / "static"
    static_dir.mkdir(exist_ok=True)

    files = [
        ("main.py", generate_boost_main(framework)),
        ("base.py", generate_boost_base(framework, template)),
        (".env.example", generate_env_example()),
    ]

    # Add components.py if the template needs it
    components = generate_boost_components(template)
    if components:
        files.append(("components.py", components))

    for filename, content in files:
        file_path = root / filename
        file_path.write_text(content)
        if verbose:
            console.print(f"[green]Created:[/green] {filename}")

    if verbose:
        console.print("[green]Created:[/green] static/")


def run_tailwind_setup(verbose: bool = False) -> None:
    """Run tailwind init and build after project scaffolding."""
    from nitro.config import get_nitro_config
    from nitro.cli.tailwind_commands.init import (
        setup_css_directories,
        download_tailwind_binary,
        copy_css_folder,
        create_gitignore_entries,
    )
    from nitro.cli.tailwind_commands.build import (
        ensure_css_input,
        run_tailwind_build,
    )

    root = Path.cwd()
    config = get_nitro_config(root)

    console.print("\n[cyan]Setting up Tailwind CSS...[/cyan]")

    # Init steps
    setup_css_directories(config, verbose)
    binary_path = download_tailwind_binary(verbose)
    copy_css_folder(config, verbose)
    create_gitignore_entries(config, verbose)

    # Build initial CSS (unminified for dev)
    input_css = ensure_css_input(config)
    output_css = config.css_output_absolute
    output_css.parent.mkdir(parents=True, exist_ok=True)

    if run_tailwind_build(
        binary_path, input_css, output_css, config.project_root, minify=False
    ):
        console.print("[green]Tailwind CSS built.[/green]")
    else:
        console.print(
            "[yellow]Tailwind build had issues — run 'nitro tw build' manually.[/yellow]"
        )


def boost_command(
    framework: Framework = typer.Option(
        None,
        "--framework",
        "-f",
        help="Web framework to use",
        prompt="Select a framework",
        show_choices=True,
    ),
    template: str = typer.Option(
        None,
        "--template",
        "-t",
        help="Template to use (blank, app)",
    ),
    force: bool = typer.Option(False, "--force", help="Force overwrite existing files"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output"
    ),
) -> None:
    """Initialize a new Nitro project with base template files.

    Creates main.py, base.py, and .env.example in the current directory,
    then initializes and builds Tailwind CSS.
    """
    try:
        root = Path.cwd()

        if verbose:
            console.print(f"[blue]Initializing Nitro project in:[/blue] {root}")

        # Check for conflicts
        validate_boost_project(root, force)

        # Interactive template selection if not provided via flag
        if template is None:
            template = prompt_template()

        valid_templates = [key for key, _ in TEMPLATE_CHOICES.values()]
        if template not in valid_templates:
            error(f"Unknown template: {template}. Choose from: {', '.join(valid_templates)}")
            raise typer.Exit(1)

        label = next(l for k, l in TEMPLATE_CHOICES.values() if k == template)
        console.print(
            f"\n[green]Nitro Boost![/green] "
            f"(framework: [bold]{framework.value}[/bold], "
            f"template: [bold]{label}[/bold])"
        )

        # Generate files
        write_boost_files(root, framework.value, template, verbose)

        # Init + build Tailwind CSS
        run_tailwind_setup(verbose)

        console.print("\n[green]Project ready![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print(
            "  1. Run [blue]python main.py[/blue] to start the dev server"
        )
        console.print(
            "  2. Run [blue]nitro tw dev[/blue] in a separate terminal to watch for CSS changes"
        )
        console.print("  3. Edit [blue]base.py[/blue] to customize your page")

    except typer.Exit:
        raise
    except Exception as e:
        error(f"Boost failed: {e}")
        raise typer.Exit(1) from e
