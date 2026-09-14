# Library Reference

Every capability of Smart Tool Creator is reachable from `smart_tool_creator.lib`. 
All other surfaces, including the CLI, are thin wrappers over the library and add no capability of their own.

## Intelligence

Model-backed capabilities run through the `Intelligence` protocol in `smart_tool_creator.intelligence.interface`:

```python
class Intelligence(Protocol):
    implementation: str

    def preflight(self) -> None: ...
    def run(self, request: AgentRequest) -> AgentResult: ...
```

`preflight` raises `SmartToolCreatorError` naming what to configure when the implementation cannot run. 
`run` executes one agent: `AgentRequest` holds the prompt, model, optional workspace, and optional output schema; `AgentResult` holds the text, structured output, or error.

`default_intelligence()` returns the shipped implementation, `CopilotIntelligence`, built on the [GitHub Copilot SDK](https://github.com/github/copilot-sdk) and signed in through the GitHub CLI. 
Another implementation is a module satisfying the protocol and a branch in that factory.

## Manifest

The tool's `SMART_TOOL.md` as structured data: the frontmatter as fields, the Markdown below it as `Manifest.body`.

```python
def load_manifest() -> Manifest
```

## Skill

What an agent reads once it has decided to drive the tool: the manifest body and the capability list, wrapped so the reader knows where the tool's files are. 
The CLI's `--help` prints exactly this.

```python
def skill() -> str
```

The installed package root, resolved at runtime, where the files the skill names can be read.

```python
def skill_directory() -> Path
```

The tool's canonical source, read from the package metadata's `[project.urls]` `Repository` entry, or `None` when the package declares none. 
The skill carries it so a caller that can run the tool but not read its files still reaches the documentation.

```python
def repository_url() -> str | None
```

## Init

Scaffolds a new smart tool: a git repository with no remote, holding everything the spec requires and passing the conformance kit before a line of domain code is written. 
The result is a working tool, not a template: its environment is synced, its first commit is made, and `<name> manifest` runs.

```python
def init(
    name: str,
    description: str,
    directory: Path | None = None,
    language: Language = "uv-python",
    intelligence: IntelligenceLayer = "copilot-sdk",
    skill: bool = False,
) -> Scaffold
```

- `name`: the tool's slug, lowercase alphanumeric and hyphens. It becomes the manifest `name`, the CLI command, and the package name.
- `description`: the manifest `description`, what the tool is for and when to reach for it.
- `directory`: where the tool is created; `name` under the current directory when omitted. Must not exist, or be empty.
- `language` and `intelligence`: the choices made at scaffold time, listed below. Either can be changed later; each is a set of files, not a commitment.
- `skill`: also ship an [Agent Skill](https://agentskills.io/specification) at `skills/<name>/SKILL.md` that teaches a coding agent to drive the tool.

Every scaffold carries the same shape as this repository: the manifest and descriptor, a library with a thin CLI over it, a `README.md`, `CONTRIBUTING.md`, and `docs/` written for the new tool, and an `AGENTS.md` holding the principles the spec asks of a smart tool. 
The model-backed capabilities sit behind an `Intelligence` interface so the SDK underneath is a module, not a rewrite.

A `reference/` directory holds shallow, gitignored clones of the repositories an agent developing the tool should read rather than recall: the [spec](https://github.com/microsoft/amplifier-smart-tools), the chosen SDK, and the [Agent Skills spec](https://github.com/agentskills/agentskills) when `skill` is set. 
`AGENTS.md` lists them and the development setup script restores any that are missing, so a fresh clone of the tool recovers them.

Returns the created root, the files written under it, and the repositories cloned into `reference/`. 
Raises `SmartToolCreatorError` when `name` is not a slug, `directory` is not empty, `git` or `uv` is not on `PATH`, or a reference cannot be cloned.

### Languages

- `uv-python`: a [uv](https://docs.astral.sh/uv/) project on Python 3.13 with `ruff`, `ty`, `pytest`, and `prek` hooks configured.

### Intelligence layers

- `copilot-sdk`: the [GitHub Copilot SDK](https://github.com/github/copilot-sdk), signed in through the GitHub CLI.
