import re
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

console = Console()


def success(message: str, **kwargs: Any) -> None:
    console.print(f"[green]✓[/green] {message}", **kwargs)


def error(message: str, exception: Exception | None = None, **kwargs: Any) -> None:
    console.print(f"[red]❌ Error:[/red] {message}", **kwargs)
    if exception:
        console.print(f"[dim]Details: {str(exception)}[/dim]")


def warning(message: str, **kwargs: Any) -> None:
    console.print(f"[yellow]⚠ Warning:[/yellow] {message}", **kwargs)


def info(message: str, **kwargs: Any) -> None:
    console.print(f"[blue]ℹ Info:[/blue] {message}", **kwargs)


def confirm(message: str, default: bool = False) -> bool:
    return typer.confirm(message, default=default)


def create_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )


def get_project_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


def status_context(message: str):
    return console.status(message)
