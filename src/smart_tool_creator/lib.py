"""Top level entry point for the Smart Tool Creator library."""

from pathlib import Path

from smart_tool_creator.core import manifest, scaffold
from smart_tool_creator.core import skill as skill_module
from smart_tool_creator.schemas import IntelligenceLayer, Language, Manifest, Scaffold


def load_manifest() -> Manifest:
    """The tool's manifest as structured data, read from the SMART_TOOL.md shipped inside the package."""
    return manifest.load_manifest()


def skill() -> str:
    """The tool's skill: the manifest body and the capability list, wrapped so a reader knows where its files are."""
    return skill_module.skill()


def skill_directory() -> Path:
    """The installed package root, where the files the skill names can be read."""
    return skill_module.skill_directory()


def skill_resources() -> list[str]:
    """The files the skill lists, as paths relative to the skill directory. Every one ships inside the package."""
    return skill_module.skill_resources()


def repository_url() -> str | None:
    """The tool's canonical source, from the package metadata, or None when the package declares none."""
    return skill_module.repository_url()


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
