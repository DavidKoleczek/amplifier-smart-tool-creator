"""Init: a new smart tool rendered from templates into a git repository of its own."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from liquid import Environment, StrictUndefined

from smart_tool_creator.schemas import SLUG_PATTERN, IntelligenceLayer, Language, Scaffold, SmartToolCreatorError

TEMPLATES_ROOT = Path(__file__).parent / "templates"
TEMPLATE_SUFFIX = ".liquid"
PACKAGE_SEGMENT = "__package__"
NAME_SEGMENT = "__name__"

INITIAL_VERSION = "0.1.0"
PYTHON_VERSION = "3.13"

BASE_DEPENDENCIES = ["pydantic>=2.13,<3.0", "pyyaml>=6.0.3,<7.0.0", "typer>=0.27.2,<0.28.0"]
INTELLIGENCE_DEPENDENCIES: dict[str, list[str]] = {
    "copilot-sdk": ["github-copilot-sdk>=1.0.13,<2.0.0", "jsonschema>=4.26.0,<5.0.0"]
}

SPEC_REPOSITORY = "https://github.com/microsoft/amplifier-smart-tools"
INTELLIGENCE_REPOSITORIES: dict[str, str] = {"copilot-sdk": "https://github.com/github/copilot-sdk"}
SKILL_REPOSITORY = "https://github.com/agentskills/agentskills"

ENVIRONMENT = Environment(undefined=StrictUndefined)


def init(
    name: str,
    description: str,
    directory: Path | None = None,
    language: Language = "uv-python",
    intelligence: IntelligenceLayer = "copilot-sdk",
    skill: bool = False,
) -> Scaffold:
    """Scaffold a new smart tool and leave it committed, synced, and runnable."""
    root = (Path.cwd() / name if directory is None else directory).resolve()
    # One line with no closing period, so it drops into the manifest as is and into prose as a sentence.
    description = " ".join(description.split()).rstrip(".")
    _preflight(name, description, root)

    references = reference_repositories(intelligence, skill)
    sources = [TEMPLATES_ROOT / language / "base", TEMPLATES_ROOT / language / "intelligence" / intelligence]
    if skill:
        sources.append(TEMPLATES_ROOT / language / "skill")
    variables = _variables(name, description, intelligence, references, skill)

    files = sorted(file for source in sources for file in _render(source, root, variables))
    _git(["init", "--initial-branch=main"], root, "Could not create the git repository")
    _run(["uv", "sync"], root, "Could not sync the new tool's environment")
    for repository in references:
        destination = Path("reference") / repository.rsplit("/", 1)[-1]
        _git(
            ["clone", "--depth", "1", "--single-branch", repository, str(destination)],
            root,
            f"Could not clone the reference {repository}",
        )
    _git(["add", "-A"], root, "Could not stage the new tool")
    _git(["commit", "-m", f"Scaffold {name} with smart-tool-creator"], root, "Could not commit the new tool")
    return Scaffold(root=root, files=files, references=references)


def reference_repositories(intelligence: IntelligenceLayer, skill: bool) -> list[str]:
    """The repositories an agent developing the new tool should read rather than recall."""
    references = [SPEC_REPOSITORY, INTELLIGENCE_REPOSITORIES[intelligence]]
    if skill:
        references.append(SKILL_REPOSITORY)
    return references


def _preflight(name: str, description: str, root: Path) -> None:
    """Everything that can be known before a file is written, so a failure leaves no half-built tool."""
    if re.match(SLUG_PATTERN, name) is None:
        raise SmartToolCreatorError(
            f"'{name}' is not a usable tool name. Use lowercase letters, digits, and single hyphens, as in 'incident-postmortem'."
        )
    if not description:
        raise SmartToolCreatorError(
            "The new tool needs a description. Say what it is for and when to reach for it; it becomes the manifest description."
        )
    if root.exists():
        if not root.is_dir():
            raise SmartToolCreatorError(f"{root} is a file. Choose a directory that does not exist or is empty.")
        if any(root.iterdir()):
            raise SmartToolCreatorError(f"{root} is not empty. Choose a directory that does not exist or is empty.")
    for executable, install in (("git", "https://git-scm.com/"), ("uv", "https://docs.astral.sh/uv/")):
        if shutil.which(executable) is None:
            raise SmartToolCreatorError(f"'{executable}' is not on PATH. Install it from {install} and try again.")
    for setting in ("user.name", "user.email"):
        configured = subprocess.run(["git", "config", setting], capture_output=True, text=True)
        if configured.returncode != 0 or not configured.stdout.strip():
            raise SmartToolCreatorError(
                f"git has no {setting}, so the new tool's first commit cannot be made. "
                f"Set it with `git config --global {setting} <value>`."
            )


def _variables(
    name: str, description: str, intelligence: IntelligenceLayer, references: list[str], skill: bool
) -> dict[str, object]:
    package = name.replace("-", "_")
    title = " ".join(word.capitalize() for word in name.split("-"))
    return {
        "name": name,
        "package": package,
        "title": title,
        "error_class": f"{title.replace(' ', '')}Error",
        "description": description,
        # A description carrying quotes or backslashes still has to render valid TOML and valid
        # Python, so those two positions take an escaped form; everywhere else takes the plain text.
        "description_literal": json.dumps(description),
        "description_docstring": _docstring(description),
        "version": INITIAL_VERSION,
        "python_version": PYTHON_VERSION,
        "dependencies": sorted(BASE_DEPENDENCIES + INTELLIGENCE_DEPENDENCIES[intelligence]),
        "references": references,
        "skill": skill,
    }


def _docstring(text: str) -> str:
    """The text as a triple-quoted Python docstring, in the shape a formatter would leave it."""
    escaped = text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    if escaped.endswith('"'):
        escaped = f'{escaped[:-1]}\\"'
    return f'"""{escaped}"""'


def _render(source: Path, root: Path, variables: dict[str, object]) -> list[Path]:
    """Render one template tree into the new tool, returning the files written relative to its root."""
    written: list[Path] = []
    for template in sorted(path for path in source.rglob("*") if path.is_file()):
        relative = _destination(template.relative_to(source), variables)
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(ENVIRONMENT.render(template.read_text(encoding="utf-8"), **variables))
        written.append(relative)
    return written


def _destination(relative: Path, variables: dict[str, object]) -> Path:
    substitutions = {PACKAGE_SEGMENT: str(variables["package"]), NAME_SEGMENT: str(variables["name"])}
    segments = [substitutions.get(segment, segment) for segment in relative.parts]
    segments[-1] = segments[-1].removesuffix(TEMPLATE_SUFFIX)
    return Path(*segments)


def _git(arguments: list[str], root: Path, failure: str) -> None:
    _run(["git", *arguments], root, failure)


def _run(command: list[str], root: Path, failure: str) -> None:
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, env=_clean_environment())
    if completed.returncode != 0:
        raise SmartToolCreatorError(f"{failure}: {completed.stderr.strip() or completed.stdout.strip()}")


def _clean_environment() -> dict[str, str]:
    """This process's environment without its own virtual environment, which uv would otherwise sync."""
    return {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}
