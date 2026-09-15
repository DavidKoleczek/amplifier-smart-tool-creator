"""
Cross-platform script to set up a development environment for the project.
It assumes that you have installed all the prerequisites listed in CONTRIBUTING.md.
"""

import shlex
import subprocess

MINIMUM_UV_VERSION = (0, 9, 17)


def run(command: str) -> None:
    """Run a command, forwarding its output to this process's stdout and stderr."""
    subprocess.run(shlex.split(command), check=True)


def parse_uv_version(output: str) -> tuple[int, int, int]:
    """Parse the semantic version from `uv --version` output."""
    version = output.split()[1]
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def require_supported_uv(output: str) -> None:
    """Fail with upgrade guidance when uv cannot read this project's settings."""
    installed = parse_uv_version(output)
    if installed < MINIMUM_UV_VERSION:
        minimum = ".".join(str(part) for part in MINIMUM_UV_VERSION)
        found = ".".join(str(part) for part in installed)
        raise SystemExit(
            f"uv {minimum} or newer is required because this project uses relative exclude-newer durations. "
            f"Found uv {found}. Upgrade uv, then rerun `uv run setup-for-dev.py`."
        )


def main() -> None:
    uv_version = subprocess.run(["uv", "--version"], check=True, capture_output=True, text=True).stdout.strip()
    print(uv_version, flush=True)
    require_supported_uv(uv_version)
    run("prek --version")
    run("uv sync --frozen --all-extras --all-groups")
    run("prek install")


if __name__ == "__main__":
    main()
