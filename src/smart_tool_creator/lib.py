"""Top level entry point for the Smart Tool Creator library."""

from pathlib import Path

from smart_tool_creator.core import manifest, scaffold
from smart_tool_creator.schemas import IntelligenceLayer, Language, Manifest, Scaffold


def load_manifest() -> Manifest:
    """The tool's manifest as structured data, read from the SMART_TOOL.md shipped inside the package."""
    return manifest.load_manifest()


def init(
    name: str,
    description: str,
    directory: Path | None = None,
    language: Language = "uv-python",
    intelligence: IntelligenceLayer = "copilot-sdk",
    skill: bool = False,
) -> Scaffold:
    """Scaffold a new smart tool: a git repository with no remote, synced, committed, and conforming to the spec."""
    return scaffold.init(
        name,
        description,
        directory=directory,
        language=language,
        intelligence=intelligence,
        skill=skill,
    )
