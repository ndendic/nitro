import typer
from rich import print as rich_print

from nitro import __version__

from .tailwind_commands.build import build_command
from .tailwind_commands.dev import dev_command
from .tailwind_commands.init import init_command
from .database_commands.cli import app as db_app
app = typer.Typer(
    name="nitro",
    help="Python-first set of abstraction layers for Python web development",
    rich_markup_mode="rich",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    if value:
        rich_print(f"[bold blue]nitro {__version__}[/bold blue]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Python-first set of abstraction layers for Python web development."""


# Tailwind commands group
tw_app = typer.Typer(name="tw", help="Tailwind CSS commands")
tw_app.command("init")(init_command)
tw_app.command("dev")(dev_command)
tw_app.command("build")(build_command)
app.add_typer(tw_app)

app.add_typer(db_app)

if __name__ == "__main__":
    app()
