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
Naming a capability returns that capability's own skill instead: the same wrapper, a heading carrying the capability's name, whether it is deterministic or model-backed, and the Markdown beside its code, which covers its arguments, a worked invocation, its result, and its failures. 
The CLI's `--help` prints exactly this, the tool's at the root and the capability's on a command. 
Raises `SmartToolCreatorError` when the name is not a capability, naming the ones that are.

```python
def skill(capability: str | None = None) -> str
```

The capabilities the skill lists, one entry each, driven by the same table the CLI is built from:

```python
class Capability(NamedTuple):
    name: str
    summary: str
    model_backed: bool
    skill: str
    resources: tuple[str, ...] = ()
```

- `name` and `summary`: the command's name and its line in the tool's capability list.
- `model_backed`: whether it runs through the `Intelligence` interface, which decides the kind shown in both skills.
- `skill`: the capability's skill body, a Markdown file relative to `skill_directory()`, written without frontmatter, title, or kind line because the renderer supplies them.
- `resources`: the files that body refers to, relative to `skill_directory()`, listed under `<skill_resources>` in the capability's skill. The block is omitted when there are none.

The installed package root, resolved at runtime, where the files the skill names can be read.

```python
def skill_directory() -> Path
```

The files the skill lists under `<skill_resources>`, as paths relative to `skill_directory()`. Every one ships inside the package, so each resolves after installation. 
The second does the same for one capability's skill, and raises `SmartToolCreatorError` when the name is not a capability.

```python
def skill_resources() -> list[str]


def capability_skill_resources(capability: str) -> list[str]
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
    repository: str | None = None,
) -> Scaffold
```

- `name`: the tool's slug, lowercase alphanumeric and hyphens. It becomes the manifest `name`, the CLI command, and the package name.
- `description`: the manifest `description`, what the tool is for and when to reach for it.
- `directory`: where the tool is created; `name` under the current directory when omitted. Must not exist, or be empty.
- `language` and `intelligence`: the choices made at scaffold time, listed below. Either can be changed later; each is a set of files, not a commitment.
- `skill`: also ship an [Agent Skill](https://agentskills.io/specification) at `skills/<name>/SKILL.md` that teaches a coding agent to drive the tool.
- `repository`: the `https://` URL the tool will be cloned from. It is declared in `pyproject.toml` under `[project.urls]` so `--help` carries it, and every install instruction in the `README.md`, manifest, and skill is built on it: `git+<url>` for the CLI and library, `npx skills add` for the skill, plus update and uninstall commands. When given, it also becomes the `origin` remote; nothing is pushed. When omitted, `https://github.com/<owner>/<name>` stands in everywhere, there is no remote, and the `output_message` says the instructions do not work until the placeholder is replaced and the tool is pushed.

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

## Check conformance

Runs the spec's [conformance kit](https://github.com/microsoft/amplifier-smart-tools/tree/main/conformance) against a smart tool and returns its verdict as the kit gave it. 
The kit is the spec repository's, fetched on each run and never vendored, so what this reports is what the spec says. Deterministic.

```python
def check_conformance(directory: Path | None = None, timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS) -> ConformanceReport
```

- `directory`: the tool's distribution root; the current directory when omitted. Whether it holds a smart tool is the kit's call, so a root without a `smart-tool.json` fails `descriptor-present` rather than raising.
- `timeout`: seconds the kit allows each invocation it makes of the tool. `20.0` by default.

The kit is run from the tool's root with `uv run --no-project`, which resolves its inline dependencies; a root holding a `pyproject.toml` is wrapped in `uv run --` so the tool's own console script is on `PATH`, since the kit never installs the tool under test. The kit's JSON verdict on stdout is parsed into the report; its ids, statuses, and spec sentences are kept as is.

```python
class ConformanceRule(BaseModel):
    id: str
    status: Literal["PASS", "FAIL", "SKIP"]
    spec: str
    detail: str


class ConformanceReport(BaseModel):
    root: Path
    verdict: Literal["PASS", "FAIL"]
    counts: dict[str, int]
    failed_rules: list[str]
    rules: list[ConformanceRule]
    output_message: str
```

`verdict` is `FAIL` when any rule failed; a `SKIP` carries the reason the rule could not be evaluated and never fails a tool. 
`output_message` is the report for the calling agent, rendered from `capabilities/check_conformance/output_message.md.liquid`: one line per rule, the verdict with its counts, and, when rules failed, each one's spec sentence.

Raises `SmartToolCreatorError` when `directory` is not a directory, `uv` is not on `PATH`, or the kit produced no verdict: the network, uv failing to run it, or its output contract changing. The message carries the command to rerun by hand and the kit's stderr.

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

After the agent finishes, the tool's own checks run in its root: `uv run pytest`, `prek run --all-files`, and the conformance kit through `check_conformance`. The prek check is `skipped`, never failed, when the tool has no `.pre-commit-config.yaml` or `prek` is not on `PATH`; the conformance check is `skipped` when the kit itself could not run, and when it fails its output is the failing rules with their details and spec sentences. While any check fails, another agent run gets the failing commands and their output and fixes them, up to `MAX_FIX_ROUNDS` (2). Each fix round continues the implementation run's session, so the agent still has the work it just did in context. Checks still failing after that are returned, not raised: the caller decides what the partial work is worth.

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
