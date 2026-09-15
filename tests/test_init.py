"""Scaffolds a tool for real, then holds it to what a published smart tool is held to."""

import json
import os
from pathlib import Path
import subprocess

from smart_tool_creator.lib import init

NAME = "release-notes"
DESCRIPTION = "Summarizes changelogs into release notes"

SPEC_REQUIRED = [
    "smart-tool.json",
    "pyproject.toml",
    "src/release_notes/SMART_TOOL.md",
    "src/release_notes/lib.py",
    "src/release_notes/cli.py",
]
SHIPPED_ALONGSIDE = [
    "AGENTS.md",
    "CONTRIBUTING.md",
    "README.md",
    "docs/00-vision.md",
    "docs/01-library.md",
    "docs/02-cli.md",
    "setup-for-dev.py",
    "src/release_notes/capabilities/__init__.py",
    "src/release_notes/core/skill.py",
    "src/release_notes/intelligence/interface.py",
    "src/release_notes/intelligence/copilot.py",
    "skills/release-notes/SKILL.md",
    "tests/test_manifest.py",
    "tests/test_skill.py",
]
CREATOR_TRACES = ["smart-tool-creator", "smart_tool_creator", "SmartToolCreator"]


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment.pop("VIRTUAL_ENV", None)
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=environment)


def passes(command: list[str], cwd: Path) -> None:
    completed = run(command, cwd)
    assert completed.returncode == 0, f"{' '.join(command)}\n{completed.stdout}\n{completed.stderr}"


def test_init_produces_a_conforming_committed_tool(tmp_path: Path) -> None:
    root = tmp_path / NAME
    result = init(NAME, DESCRIPTION, directory=root, skill=True)

    assert result.root == root.resolve()
    for relative in SPEC_REQUIRED + SHIPPED_ALONGSIDE:
        assert Path(relative) in result.files, relative
        assert (root / relative).is_file(), relative

    committed = run(["git", "ls-files"], root).stdout.split()
    assert sorted(committed) == sorted([*(str(file) for file in result.files), "uv.lock"])
    assert len(run(["git", "log", "--oneline"], root).stdout.strip().splitlines()) == 1
    assert run(["git", "remote"], root).stdout.strip() == ""
    assert run(["git", "status", "--porcelain"], root).stdout.strip() == ""

    for relative in committed:
        content = (root / relative).read_text(encoding="utf-8")
        assert not any(trace in content for trace in CREATOR_TRACES), relative

    assert sorted(path.name for path in (root / "reference").iterdir()) == sorted(
        url.rsplit("/", 1)[-1] for url in result.references
    )
    assert "amplifier-smart-tools" in {url.rsplit("/", 1)[-1] for url in result.references}

    invoked = run(["uv", "run", NAME, "manifest"], root)
    assert invoked.returncode == 0, invoked.stderr
    manifest = json.loads(invoked.stdout)
    assert (manifest["name"], manifest["version"], manifest["description"]) == (NAME, "0.1.0", DESCRIPTION)

    passes(["prek", "run", "--all-files"], root)
    passes(["uv", "run", "pytest"], root)

    kit = Path("reference") / "amplifier-smart-tools" / "conformance" / "run.py"
    conformance = run(["uv", "run", "--", "uv", "run", "--no-project", str(kit), ".", "--json-only"], root)
    verdict = json.loads(conformance.stdout)
    assert conformance.returncode == 0, conformance.stderr
    assert verdict["verdict"] == "PASS", verdict["failed_rules"]
    assert verdict["counts"]["skip"] == 0, verdict
