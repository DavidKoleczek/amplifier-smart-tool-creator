---
name: smart-tool-creator
description: >-
  Create, validate, and evaluate smart tools that follow the Amplifier Smart Tool Spec,
  by driving the smart-tool-creator smart tool from a CLI, a library, or an agent. Use
  when (1) packaging domain expertise as a standalone tool any agent can call, (2)
  checking an existing smart tool against the spec and its conformance kit, (3)
  measuring how well a smart tool's model-backed capabilities work. Triggers on "smart
  tool", "smart-tool-creator", "amplifier smart tool", "conformance kit", "SMART_TOOL.md",
  "smart-tool.json".
license: MIT
metadata:
  author: DavidKoleczek
  repository: https://github.com/DavidKoleczek/amplifier-smart-tool-creator
---

# Using smart-tool-creator

A smart tool for building smart tools. It scaffolds the structure the
[spec](https://github.com/microsoft/amplifier-smart-tools) requires, checks a tool against
the spec, and evaluates a tool's model-backed capabilities in isolation.

**The library is the tool.** `smart_tool_creator.lib` holds every capability. The CLI is a
thin wrapper over it, so anything you can do from the shell you can also do from Python.

## Before writing code

Confirm every capability and argument against `--help` before using it. Do not fill gaps
from memory.

```bash
smart-tool-creator --help
smart-tool-creator <command> --help
```

Each command's help says whether it is model-backed. When `--help` is not enough:

```
docs/01-library.md   every capability as Python: signatures and returns
docs/02-cli.md       every capability as a command: flags, defaults, exit codes
```

Both live at <https://github.com/DavidKoleczek/amplifier-smart-tool-creator>.

## Install

```bash
# as a CLI
uv tool install git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator

# as a library
uv add "amplifier-smart-tool-creator @ git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator"

# once, without installing
uvx --from git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator smart-tool-creator --help
```

Verify with `smart-tool-creator manifest`, which needs no credentials.

## Prerequisites

Deterministic capabilities need only `uv`. Model-backed capabilities run through GitHub
Copilot, signed in as the GitHub CLI's user: `gh` must be installed and `gh auth login`
completed with an account that has a Copilot subscription. Without that, a model-backed
capability fails immediately and names what to configure; it never falls back to a
deterministic answer.

Runs on Linux, macOS, and Windows.

## Reading the manifest

The manifest says what the tool is for and what it needs, so a caller can decide whether
to reach for it before invoking anything.

```bash
smart-tool-creator manifest
```

```python
from smart_tool_creator.lib import load_manifest

manifest = load_manifest()
manifest.name, manifest.version, manifest.requires
```

Read it through the library or CLI rather than by locating a file.

## Scaffolding a new smart tool

`init` creates a git repository (no remote) holding a tool that already passes the
conformance kit: manifest, descriptor, library, thin CLI, docs, tests, an `AGENTS.md`
carrying the spec's principles, and a gitignored `reference/` with shallow clones of the
spec and the SDK for you to read while developing. The environment is synced and the
first commit is made. Deterministic, but needs network for `uv sync` and the clones.

```bash
smart-tool-creator init release-notes --description "Summarizes changelogs into release notes" --skill
```

```python
from smart_tool_creator.lib import init

scaffold = init("release-notes", "Summarizes changelogs into release notes", skill=True)
scaffold.root, scaffold.files, scaffold.references
```

Pick a slug name (lowercase, digits, hyphens) and a one-sentence description that says
what the tool is for; both land in the manifest. `--directory` chooses where it goes,
default `./<name>`, which must not exist or must be empty. `--skill` also writes
`skills/<name>/SKILL.md`. Language and intelligence layer default to `uv-python` and
`copilot-sdk`; `--help` lists the choices.

Afterwards, work inside the new repository: read its `AGENTS.md` first, add domain
capabilities to its library, and run the conformance kit as its `CONTRIBUTING.md`
describes. Adding a remote and pushing is the user's call.

## Output and failure contract

Results go to stdout, diagnostics to stderr. A failure prints a message naming what went
wrong and how to fix it, and exits non-zero: 1 for a failure the tool can name, 2 for a
bad invocation. Never treat an empty result as success.

## Choosing a surface

Import the library from Python. Shell out to the CLI from anything that cannot import
Python in-process: a shell script, a CI job, or an agent that can run commands but not
load a Python object. Both reach the same capabilities.
