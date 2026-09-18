# Contributing to Smart Tool Creator

## Development Setup

### Prerequisites

Install:

- [Git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.9.17 or newer: Manages Python environments. Older versions cannot read the project's relative `exclude-newer` setting.
- [prek](https://github.com/j178/prek): Used for precommit hooks. Recommended to install through PyPI/uv with `uv tool install prek`. Use `uv tool upgrade prek` to update it.
- [GitHub CLI](https://cli.github.com/) for intelligence features with GitHub Copilot.
- [GitHub Copilot subscription](https://github.com/github/copilot-cli#prerequisites) for intelligent features.

The Copilot prerequisites apply only to that backend. For Amplifier Agent use
`uv sync --extra amplifier` and configure the selected provider with environment credentials
or `amplifier-agent auth`. Tests do not make live model calls.

`CREATOR_TEST_REAL_AGENT=1 uv run --extra amplifier pytest tests/test_amplifier_integration.py`
also tests the real Agent Engine and loop with a scripted provider, including submission and
resume. Its first run may download runtime modules; it does not use credentials or prove
live model quality.

### Initial Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/DavidKoleczek/amplifier-smart-tool-creator.git
   cd amplifier-smart-tool-creator
   ```

1. Run the development installation script (sets up uv env and precommit hooks):

   ```bash
   uv run setup-for-dev.py
   ```

### Essential Development Commands

*Commands should be run from the repository root, unless otherwise specified.*

#### Precommit hooks

Setup precommit hooks:

```bash
prek install
```

Run precommit hooks manually:

```bash
prek run --all-files
```

#### Python Library Development

Create uv virtual environment and install dependencies:

```bash
uv sync --frozen --all-extras --all-groups
```

To update dependencies and the lock file:

```bash
uv sync -U --all-extras --all-groups
```

Lint code:

```bash
uv run ruff check --fix --config pyproject.toml
```

Format code (also formats code blocks in .md files):

```bash
uv run ruff format --config pyproject.toml
```

Type check:

```bash
uv run ty check .
```

Run tests:

```bash
uv run pytest
```

#### Conformance

Run the spec's [conformance kit](https://github.com/microsoft/amplifier-smart-tools/tree/main/conformance) against this repository through the tool's own capability, which fetches the kit and wraps it so this project's `smart-tool-creator` is on `PATH` for it to invoke:

```bash
uv run smart-tool-creator check-conformance
```

`uv run pytest` runs the same check, so a passing test suite includes conformance.
