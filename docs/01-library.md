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
Setting `AgentRequest.resume` to an earlier `AgentResult.session_id` continues that session instead of starting a fresh one, so the agent keeps what it learned.

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

The files the skill lists under `<skill_resources>`, as paths relative to `skill_directory()`. Every one ships inside the package, so each resolves after installation.

```python
def skill_resources() -> list[str]
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

Returns the created root, the files written under it, the repositories cloned into `reference/`, and an `output_message`: what was created and what to do next in the new tool, for the calling agent, rendered from `capabilities/init/output_message.md.liquid`. 
The next steps start with `docs/00-vision.md` and `docs/01-library.md` because they set the stage for everything implemented afterwards; any surface that scaffolds a tool should pass the message on to its caller. 
Raises `SmartToolCreatorError` when `name` is not a slug, `directory` is not empty, `git` or `uv` is not on `PATH`, or a reference cannot be cloned.

### Languages

- `uv-python`: a [uv](https://docs.astral.sh/uv/) project on Python 3.13 with `ruff`, `ty`, `pytest`, and `prek` hooks configured.

### Intelligence layers

- `copilot-sdk`: the [GitHub Copilot SDK](https://github.com/github/copilot-sdk), signed in through the GitHub CLI.

## Add smart capability

Adds one model-backed capability to a smart tool that already exists. An agent works inside the tool's own repository: it reads the tool, implements the capability in the library, exposes it from the CLI, writes the tests and the documentation, then runs the tool's own checks and fixes what they report. Model-backed.

```python
def add_smart_capability(
    request: str,
    directory: Path | None = None,
    context: list[str] | None = None,
    model: str = DEFAULT_INTELLIGENCE_MODEL,
    reasoning_effort: ReasoningEffort = "low",
    intelligence: Intelligence | None = None,
) -> AddedCapability
```

- `request`: the whole brief for one capability: what it does, for whom, and what it takes in and gives back.
- `directory`: the tool to work in; the current directory when omitted. It must hold a `smart-tool.json` at its root, and no parent directory is searched, so a workspace holding several tools can never be extended by accident.
- `context`: repeatable free text, usually paths to notes, transcripts, or exemplars. The agent reads the paths itself, so name them rather than pasting their contents.
- `model` and `reasoning_effort`: the agent behind the work. Effort is one of `low`, `medium`, `high`, `xhigh`, `max`.
- `intelligence`: the implementation to run through; `default_intelligence()` when omitted. Tests inject a fake.

After the agent finishes, the tool's own checks run in its root: `uv run pytest`, `prek run --all-files`, and the conformance kit. The prek check is `skipped`, never failed, when the tool has no `.pre-commit-config.yaml` or `prek` is not on `PATH`. While any check fails, another agent run gets the failing commands and their output and fixes them, up to `MAX_FIX_ROUNDS` (2). Each fix round continues the implementation run's session, so the agent still has the work it just did in context. Checks still failing after that are returned, not raised: the caller decides what the partial work is worth.

```python
class Check(BaseModel):
    name: str
    command: list[str]
    status: Literal["passed", "failed", "skipped"]
    output: str


class AddedCapability(BaseModel):
    root: Path
    report: str
    checks: list[Check]
    fix_rounds: int
    output_message: str
```

`report` is the agent's final message: the capability's name, the files it touched, the command to try it, and its caveats. 
`output_message` is the whole result for the calling agent, rendered from `capabilities/add_smart_capability/output_message.md.liquid`: the report, one line per check, the next steps, and the checks still failing when there are any. Nothing is committed and the working tree is not required to be clean; git stays the caller's.

Raises `SmartToolCreatorError` when `directory` holds no `smart-tool.json`, `request` is empty, `uv` is not on `PATH`, the intelligence preflight fails, or the agent itself fails. An agent failure may leave partial edits in the tool's working tree, and the message says so.
