"""Top level entry point for the Smart Tool Creator library."""

from smart_tool_creator.core import manifest
from smart_tool_creator.schemas import Manifest


def load_manifest() -> Manifest:
    """The tool's manifest as structured data, read from the SMART_TOOL.md shipped inside the package."""
    return manifest.load_manifest()
