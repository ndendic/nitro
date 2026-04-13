"""CLI command for `nitro create` — interactive project scaffolding."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.prompt import Prompt

from nitro.cli.utils import console, error, info, success
from nitro.scaffold.config import ScaffoldConfig, TEMPLATE_DESCRIPTIONS
from nitro.scaffold.generator import generate_project


TEMPLATE_MENU = {
    "1": "minimal",
    "2": "auth",
    "3": "fullstack",
}


def _prompt_template() -> str:
    """Interactively ask the user which template to use."""
    console.print("\n[bold]Select a template:[/bold]")
    for key, template_name in TEMPLATE_MENU.items():
        desc = TEMPLATE_DESCRIPTIONS[template_name]
        console.print(f"  [cyan]{key}[/cyan]) [bold]{template_name}[/bold] — {desc}")

    choice = Prompt.ask(
        "\nTemplate",
        choices=list(TEMPLATE_MENU.keys()),
        default="1",
    )
    return TEMPLATE_MENU[choice]


def _write_files(files: dict[str, str], root: Path, verbose: bool) -> list[str]:
    """Write generated files to the target directory.

    Args:
        files: Mapping of filename → content returned by the generator.
        root: Target directory (created if it doesn't exist).
        verbose: When True, print each file as it is written.

    Returns:
        List of relative filenames that were written.
    """
    root.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    for filename, content in files.items():
        dest = root / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        written.append(filename)
        if verbose:
            console.print(f"[green]Created:[/green] {filename}")

    return written


def create_command(
    name: str = typer.Argument(None, help="Project directory name"),
    template: str = typer.Option(
        None,
        "--template",
        "-t",
        help="Template to use (minimal, auth, fullstack)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing files without prompting",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show each file as it is created",
    ),
) -> None:
    """Create a new Nitro project with production-ready scaffolding.

    When called without arguments, runs an interactive prompt to gather
    the project name and template choice.
    """
    try:
        # --- Resolve project name ---
        if name is None:
            name = Prompt.ask("[bold]Project name[/bold]")
        if not name:
            error("Project name cannot be empty.")
            raise typer.Exit(1)

        # --- Resolve template ---
        if template is None:
            template = _prompt_template()

        valid_templates = list(TEMPLATE_DESCRIPTIONS.keys())
        if template not in valid_templates:
            error(
                f"Unknown template: '{template}'. "
                f"Choose from: {', '.join(valid_templates)}"
            )
            raise typer.Exit(1)

        # --- Resolve output directory ---
        root = Path.cwd() / name

        if root.exists() and any(root.iterdir()) and not force:
            error(
                f"Directory '{name}' already exists and is not empty. "
                "Use --force to overwrite."
            )
            raise typer.Exit(1)

        # --- Build config and generate ---
        config = ScaffoldConfig(name=name, template=template, output_dir=str(root))
        console.print(
            f"\n[bold green]Nitro Create[/bold green] "
            f"— [bold]{name}[/bold] "
            f"(template: [bold]{template}[/bold])"
        )
        console.print(f"  [dim]{config.description}[/dim]\n")

        files = generate_project(config)
        written = _write_files(files, root, verbose)

        console.print("\n[bold green]Project created![/bold green]")
        console.print(f"\n[bold]Location:[/bold] {root}")
        console.print("\n[bold]Generated files:[/bold]")
        for filename in written:
            console.print(f"  [green]+[/green] {filename}")

        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  [bold]1.[/bold] Enter your project:  [blue]cd {name}[/blue]")
        console.print(
            "  [bold]2.[/bold] Install dependencies: [blue]uv sync[/blue] "
            "[dim]or[/dim] [blue]pip install sanic nitro[/blue]"
        )
        console.print(
            "  [bold]3.[/bold] Run the app:          [blue]python main.py[/blue]"
        )
        console.print(
            "\n  [dim]Docs: https://nitro.artyficial.space[/dim]"
        )

    except typer.Exit:
        raise
    except Exception as exc:
        error(f"Create failed: {exc}")
        raise typer.Exit(1) from exc
