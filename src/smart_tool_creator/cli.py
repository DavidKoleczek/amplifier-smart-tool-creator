"""Command line entry point for the Smart Tool Creator."""

from pathlib import Path
from typing import Annotated

import typer

from smart_tool_creator import lib
from smart_tool_creator.schemas import (
    DEFAULT_INTELLIGENCE_MODEL,
    IntelligenceLayer,
    Language,
    ReasoningEffort,
    SmartToolCreatorError,
)

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    # Every command answers both flags. The root callback claims `--help` for the skill below, and Click drops a
    # help option name already taken by a parameter, which leaves the root's generated summary on `-h`.
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _print_skill(value: bool) -> None:
    """Answer the root `--help` with the skill the library composes, leaving `-h` to Typer."""
    if value:
        typer.echo(lib.skill())
        raise typer.Exit()


@app.callback()
def cli(
    help: Annotated[
        bool,
        typer.Option(
            "--help", is_eager=True, callback=_print_skill, help="This tool's skill, for an agent driving it."
        ),
    ] = False,
) -> None:
    """Create, validate, and evaluate smart tools."""


@app.command()
def manifest() -> None:
    """Print the tool's manifest as JSON. Deterministic."""
    typer.echo(lib.load_manifest().model_dump_json(indent=2))


@app.command()
def init(
    name: Annotated[str, typer.Argument(help="The tool's slug: lowercase alphanumeric and hyphens.")],
    description: Annotated[str, typer.Option("--description", help="What the tool is for and when to reach for it.")],
    directory: Annotated[
        Path | None,
        typer.Option("--directory", help="Where to create it; the name under the current directory when omitted."),
    ] = None,
    language: Annotated[Language, typer.Option("--language", help="The language the tool is written in.")] = (
        "uv-python"
    ),
    intelligence: Annotated[
        IntelligenceLayer, typer.Option("--intelligence", help="The SDK its model-backed capabilities run through.")
    ] = "copilot-sdk",
    skill: Annotated[
        bool, typer.Option("--skill", help="Also ship an Agent Skill that teaches an agent to drive the tool.")
    ] = False,
    repository: Annotated[
        str | None,
        typer.Option(
            "--repository",
            help="The https:// URL the tool will be cloned from. Declared in pyproject.toml, used by every install "
            "instruction, and added as the origin remote; nothing is pushed.",
        ),
    ] = None,
) -> None:
    """Scaffold a new smart tool: a git repository holding a spec-conforming tool that passes the conformance kit. Deterministic."""
    scaffold = lib.init(
        name,
        description,
        directory=directory,
        language=language,
        intelligence=intelligence,
        skill=skill,
        repository=repository,
    )
    typer.echo(scaffold.output_message)


@app.command()
def add_smart_capability(
    request: Annotated[
        str, typer.Argument(help="What the capability does, for whom, and what it takes in and gives back.")
    ],
    directory: Annotated[
        Path | None, typer.Option("--directory", help="The smart tool to work in; the current directory when omitted.")
    ] = None,
    context: Annotated[
        list[str] | None,
        typer.Option("--context", help="Repeatable; text, or paths the agent should read before it designs anything."),
    ] = None,
    model: Annotated[str, typer.Option("--model", help="The model the agent runs on.")] = DEFAULT_INTELLIGENCE_MODEL,
    reasoning_effort: Annotated[
        ReasoningEffort, typer.Option("--reasoning-effort", help="How hard the model thinks before it acts.")
    ] = "low",
) -> None:
    """Add one model-backed capability to an existing smart tool: library, CLI, tests, and docs, verified against the tool's own checks. Model-backed: runs through GitHub Copilot, signed in as the GitHub CLI's user."""
    added = lib.add_smart_capability(
        request,
        directory=directory,
        context=context,
        model=model,
        reasoning_effort=reasoning_effort,
    )
    typer.echo(added.output_message)
    if any(check.status == "failed" for check in added.checks):
        raise typer.Exit(1)


def main() -> int:
    try:
        app()
    except SmartToolCreatorError as error:
        typer.echo(error, err=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
