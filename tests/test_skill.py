from pathlib import Path
import tomllib

from typer.testing import CliRunner

from smart_tool_creator.cli import app
from smart_tool_creator.core.skill import CAPABILITIES
from smart_tool_creator.lib import load_manifest, repository_url, skill, skill_directory

DISTRIBUTION_ROOT = Path(__file__).parents[1]

runner = CliRunner()


def test_manifest_body_is_the_markdown_below_the_frontmatter() -> None:
    body = load_manifest().body

    assert body
    assert not body.startswith("#")


def test_skill_is_a_wrapped_document_naming_every_capability() -> None:
    document = skill()

    assert document.startswith('<skill_content name="smart-tool-creator">')
    assert document.endswith("</skill_content>")
    assert "# smart-tool-creator" in document
    assert load_manifest().body in document
    for capability in CAPABILITIES:
        assert f"`{capability.name}` [deterministic]" in document
        assert f"`smart-tool-creator {capability.name} --help`" in document


def test_repository_line_names_the_url_the_package_declares() -> None:
    pyproject = tomllib.loads((DISTRIBUTION_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = pyproject["project"]["urls"]["Repository"]
    header = skill().splitlines()

    assert repository_url() == declared
    assert header[1].startswith("Skill directory: ")
    assert header[2] == f"Repository: {declared}"
    assert header[3] == "Relative paths in this skill are relative to the skill directory."


def test_skill_resources_resolve_under_the_skill_directory() -> None:
    root = skill_directory()
    resources = [line.removeprefix("<file>").removesuffix("</file>") for line in _resource_lines(skill())]

    assert resources
    assert (root / "SMART_TOOL.md").is_file()
    for resource in resources:
        assert (root / resource).is_file()


def _resource_lines(document: str) -> list[str]:
    lines = [line.strip() for line in document.splitlines()]
    start = lines.index("<skill_resources>")
    end = lines.index("</skill_resources>")
    return lines[start + 1 : end]


def test_help_prints_the_skill() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert result.stdout.strip() == skill()


def test_short_help_and_no_arguments_print_the_terse_summary() -> None:
    short = runner.invoke(app, ["-h"])
    bare = runner.invoke(app, [])

    assert short.exit_code == 0
    assert "<skill_content" not in short.stdout
    assert "manifest" in short.stdout
    assert "<skill_content" not in bare.stdout


def test_every_command_answers_its_own_help() -> None:
    for capability in CAPABILITIES:
        result = runner.invoke(app, [capability.name, "--help"])

        assert result.exit_code == 0
        assert result.stdout.strip()
