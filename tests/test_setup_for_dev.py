"""Tests development setup prerequisite validation."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[1]


def load_setup_module() -> ModuleType:
    """Load the standalone setup script as a testable module."""
    spec = importlib.util.spec_from_file_location("setup_for_dev", ROOT / "setup-for-dev.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_require_supported_uv_accepts_minimum_version() -> None:
    setup = load_setup_module()

    setup.require_supported_uv("uv 0.9.17")


def test_require_supported_uv_rejects_older_version() -> None:
    setup = load_setup_module()

    with pytest.raises(SystemExit, match=r"uv 0\.9\.17 or newer.*Found uv 0\.8\.17.*Upgrade uv"):
        setup.require_supported_uv("uv 0.8.17")
