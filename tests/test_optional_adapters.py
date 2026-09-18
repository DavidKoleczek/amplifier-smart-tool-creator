"""Optional surfaces stay thin, installable, and independent of model credentials."""

import json
import os
from pathlib import Path
import subprocess
import tomllib
from typing import get_args
from zipfile import ZipFile

import pytest
from typer.testing import CliRunner

from smart_tool_creator.capabilities.init import scaffold
from smart_tool_creator.cli import app
from smart_tool_creator.lib import check_conformance, init, skill
from smart_tool_creator.schemas import IntelligenceLayer, OptionalAdapter, SmartToolCreatorError


def run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"VIRTUAL_ENV", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GH_TOKEN", "GITHUB_TOKEN"}
    }
    return subprocess.run(command, cwd=root, env=environment, capture_output=True, text=True)


def passes(command: list[str], root: Path) -> None:
    result = run(command, root)
    assert result.returncode == 0, f"{' '.join(command)}\n{result.stdout}\n{result.stderr}"


@pytest.mark.parametrize("adapter", ["mcp", "mcp-app"])
@pytest.mark.parametrize("intelligence", get_args(IntelligenceLayer))
def test_optional_adapter_has_real_transport_and_provider_free_cli(
    tmp_path: Path, adapter: OptionalAdapter, intelligence: IntelligenceLayer
) -> None:
    root = tmp_path / "portable-notes"
    result = init("portable-notes", "Summarizes changelogs", directory=root, intelligence=intelligence, adapter=adapter)
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    assert metadata["project"]["optional-dependencies"]["mcp"] == ["mcp>=2.2,<3.0"]
    assert not any(value.startswith("mcp") for value in metadata["project"]["dependencies"])
    assert metadata["project"]["dependencies"] == sorted(
        scaffold.BASE_DEPENDENCIES + scaffold.INTELLIGENCE_DEPENDENCIES[intelligence]
    )
    assert metadata["project"]["scripts"]["portable-notes-mcp"].endswith("adapters.mcp_server:main")
    assert "optional " + adapter + " adapter ready" in result.output_message
    assert "docs/03-portable-adapter.md" in result.output_message
    assert run(["git", "status", "--porcelain"], root).stdout == ""

    passes(["uv", "run", "--extra", "mcp", "pytest"], root)
    passes(["prek", "run", "--all-files"], root)
    passes(["uv", "run", "portable-notes", "manifest"], root)
    passes(["uv", "run", "portable-notes", "--help"], root)
    report = check_conformance(root)
    assert report.verdict == "PASS", report.output_message
    passes(["uv", "build"], root)
    wheel = next((root / "dist").glob("*.whl"))
    with ZipFile(wheel) as archive:
        assert "portable_notes/adapters/mcp_server.py" in archive.namelist()
        if adapter == "mcp-app":
            assert "portable_notes/adapters/mcp_app.html" in archive.namelist()
            license_text = archive.read("portable_notes/adapters/mcp_app.LICENSE.txt").decode()
            assert "@modelcontextprotocol/ext-apps@" in license_text
            assert "zod@" in license_text
            assert "MIT License" in license_text
    passes(
        [
            "uv",
            "run",
            "--isolated",
            "--no-project",
            "--with",
            f"{wheel}[mcp]",
            "python",
            "-c",
            (
                "import sys; from portable_notes import lib; "
                "from portable_notes.adapters.mcp_server import create_server; "
                "assert lib.load_manifest().name == 'portable-notes'; create_server(); "
                "assert not any(n.startswith(('amplifier_agent_', 'copilot')) for n in sys.modules)"
            ),
        ],
        root,
    )
    descriptor = json.loads((root / "smart-tool.json").read_text())
    assert set(descriptor) == {"manifest", "cli_argv", "deterministic_smoke"}
    assert Path("src/portable_notes/adapters/mcp_server.py") in result.files
    if adapter == "mcp-app":
        assert Path("ui/package-lock.json") in result.files
        assert Path("src/portable_notes/adapters/mcp_app.html") in result.files
        assert Path("src/portable_notes/adapters/mcp_app.LICENSE.txt") in result.files
        assert "modelcontextprotocol/ext-apps" in (root / "ui/package-lock.json").read_text()
        passes(["npm", "run", "build"], root / "ui")
    else:
        assert not (root / "ui").exists()


def test_missing_npm_fails_before_writing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = scaffold.shutil.which
    monkeypatch.setattr(scaffold.shutil, "which", lambda name: None if name == "npm" else original(name))
    root = tmp_path / "portable-notes"
    with pytest.raises(SmartToolCreatorError, match="needs npm"):
        init("portable-notes", "Summarizes changelogs", directory=root, adapter="mcp-app")
    assert not root.exists()


def test_optional_adapter_help_is_reachable_from_both_surfaces() -> None:
    detail = skill("init")
    assert "--adapter none|mcp|mcp-app" in detail
    assert "<file>capabilities/init/portable-surfaces.md</file>" in detail
    result = CliRunner().invoke(app, ["init", "-h"])
    assert result.exit_code == 0
    assert "--adapter" in result.stdout
    invalid = CliRunner().invoke(app, ["init", "notes", "--description", "Notes", "--adapter", "unrecognized"])
    assert invalid.exit_code == 2
