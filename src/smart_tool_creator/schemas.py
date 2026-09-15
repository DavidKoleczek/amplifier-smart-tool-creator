from pathlib import Path
from typing import Literal, NamedTuple

from pydantic import BaseModel, Field

DEFAULT_INTELLIGENCE_MODEL = "gpt-6-astra"
ReasoningEffort = Literal["low", "medium", "high", "xhigh", "max"]

SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"
SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"


class SmartToolCreatorError(Exception):
    """Raised for any failure the library can name and explain how to fix."""


# region: Manifest


class ManifestRequirement(BaseModel):
    """One environment prerequisite; `install` references documentation, never a command."""

    name: str
    purpose: str
    install: str
    optional: bool = False


class Manifest(BaseModel):
    """The structured form of SMART_TOOL.md: the frontmatter as fields, the Markdown below it as text."""

    smart_tool_format: int
    name: str = Field(pattern=SLUG_PATTERN)
    version: str = Field(pattern=SEMVER_PATTERN)
    description: str
    use_cases: list[str]
    platforms: list[str]
    requires: list[ManifestRequirement] = Field(default_factory=list)
    body: str = Field(description="The Markdown below the frontmatter: the skill `--help` renders")


# endregion

# region: Skill


class Capability(NamedTuple):
    """One capability of the tool, as the skill's capability list presents it."""

    name: str
    summary: str
    model_backed: bool


# endregion

# region: Init

Language = Literal["uv-python"]
IntelligenceLayer = Literal["copilot-sdk"]


class Scaffold(BaseModel):
    """What init produced."""

    root: Path = Field(description="The new tool's distribution root")
    files: list[Path] = Field(description="Every file written, relative to the root")
    references: list[str] = Field(description="The repositories cloned into reference/")


# endregion

# region: Add smart capability


class Check(BaseModel):
    """One of the extended tool's own checks, as it stood after the agent finished."""

    name: str
    command: list[str]
    status: Literal["passed", "failed", "skipped"]
    output: str = Field(
        description="The tail of the combined output when it failed, the reason when it was skipped, empty when it passed"
    )


class AddedCapability(BaseModel):
    """What add_smart_capability produced."""

    root: Path = Field(description="The extended tool's distribution root")
    report: str = Field(description="The agent's final message: what it added, how to try it, caveats")
    checks: list[Check] = Field(description="The tool's own checks, run after the work finished")
    fix_rounds: int = Field(description="Extra agent runs spent on failing checks")


# endregion
