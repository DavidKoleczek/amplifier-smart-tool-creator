"""Command line entry point for the Smart Tool Creator."""

import typer

from smart_tool_creator import lib
from smart_tool_creator.schemas import SmartToolCreatorError

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback()
def cli() -> None:
    """Create, validate, and evaluate smart tools."""


@app.command()
def manifest() -> None:
    """Print the tool's manifest as JSON."""
    typer.echo(lib.load_manifest().model_dump_json(indent=2))


def main() -> int:
    try:
        app()
    except SmartToolCreatorError as error:
        typer.echo(error, err=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
