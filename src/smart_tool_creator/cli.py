"""Command line entry point for the Smart Tool Creator."""

from pathlib import Path
from typing import Annotated

import typer

from smart_tool_creator import lib
from smart_tool_creator.schemas import IntelligenceLayer, Language, SmartToolCreatorError

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
) -> None:
    """Scaffold a new smart tool: a git repository holding a spec-conforming tool that passes the conformance kit. Deterministic."""
    scaffold = lib.init(
        name,
        description,
        directory=directory,
        language=language,
        intelligence=intelligence,
        skill=skill,
    )
    lines = [
        f"Scaffolded {name} at {scaffold.root}",
        f"  {len(scaffold.files)} files written as a {language} tool with {intelligence} intelligence, "
        "committed to a new git repository with no remote",
        f"  environment synced: `uv run {name} manifest` works from that directory",
    ]
    if skill:
        lines.append(f"  Agent Skill at skills/{name}/SKILL.md")
    lines.append("  reference/ holds shallow clones of:")
    lines.extend(f"    {repository}" for repository in scaffold.references)
    lines.extend(
        [
            "Next:",
            f"  cd {scaffold.root}",
            "  read AGENTS.md, then fill in the Goals and Non-Goals in docs/00-vision.md",
            f"  add the first capability to src/{name.replace('-', '_')}/lib.py and expose it in cli.py",
            "  document it in docs/01-library.md and docs/02-cli.md, and add its worked invocation to SMART_TOOL.md",
            "  run `prek run --all-files`, `uv run pytest`, and the conformance kit as CONTRIBUTING.md describes",
            "  add a remote and push when ready",
        ]
    )
    typer.echo("\n".join(lines))


def main() -> int:
    try:
        app()
    except SmartToolCreatorError as error:
        typer.echo(error, err=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
