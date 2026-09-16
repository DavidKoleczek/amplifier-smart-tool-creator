# Loop Artifact Studio Smart Tool Design

**Status:** Proposed

**Last updated:** 2026-09-15

**Proposed Smart Tool name:** `loop-artifact-studio`

**Document scope:** This is a standalone proposed design for the agent-facing
surface, internal orchestration, and persistence architecture of Loop Artifact
Studio.

## 1. Summary

Loop Artifact Studio is a library-first Amplifier Smart Tool for creating,
editing, validating, rendering, and persisting rich HTML artifacts as Microsoft
Loop pages.

The Smart Tool packages the artifact capabilities currently distributed across
OfficeAgent skills, subagents, tools, hooks, scripts, prompts, and workspace
conventions behind a small intent-level interface:

```text
user intent + caller-provided context + optional existing artifact
    -> profile-aware artifact authoring or editing
    -> deterministic assembly, validation, rendering, and output safety
    -> optional Loop create or baseline-aware update
    -> structured artifact and persistence result
```

The caller does not reproduce the OfficeAgent workflow. It does not select
subagents, invoke persistence tools, run cleanup hooks, assemble fragments, or
handle Fluid state. The caller selects the Smart Tool, chooses a capability,
passes intent and context, and receives a result.

The complete product scope is capability parity with the relevant OfficeAgent
artifact workflows:

- Documents and Copilot Pages.
- Dashboards and data-rich pages.
- Presentations and slides.
- Interactive HTML applications, subject to an explicit runtime sandbox.
- New artifact creation.
- Full-artifact editing.
- Selected-block editing with a trusted full-edit fallback.
- Chart, graphic, image, and narration assistance.
- Assets, manifests, and multi-part artifacts.
- Loop creation and same-page editing.

Capabilities may be implemented incrementally, but the initial document slice is
an implementation milestone, not the intended final scope.

## 2. Design assumptions

This design makes the following assumptions:

1. An approved LWS integration can create an artifact.
2. It can fetch the current artifact and an opaque baseline state for editing.
3. It can update the same artifact by sending the desired content and the
   baseline state from the corresponding fetch.
4. The update service owns server-side derivation, rebasing, merge, and conflict
   handling.
5. A deployment can be onboarded for the required Loop and Microsoft Graph
   credentials, application approvals, endpoint access, and client scenario.
6. The exact LWS endpoint family and wire representation may be selected later.

These assumptions are represented by a capability-oriented persistence port.
They are not encoded as endpoint paths or OfficeAgent runtime types in the core
library.

## 3. Goals

1. Give an agent one small, typed surface for creating and editing rich Loop
   artifacts.
2. Preserve the domain knowledge and behavior currently expressed through
   OfficeAgent skills, subagents, tools, hooks, and scripts.
3. Make the library the authoritative implementation of every capability.
4. Keep model orchestration private to the Smart Tool.
5. Separate model proposals from deterministic assembly and enforcement.
6. Support documents, dashboards, slides, and interactive applications through
   explicit artifact profiles.
7. Keep Loop authentication, endpoint selection, wire serialization, and
   baseline handling behind an adapter.
8. Make persistence an explicit caller choice and a deterministic application
   stage, not a model decision.
9. Return structured results that any agent, CLI, service, or application can
   consume.
10. Run manifest, self-description, validation, packaging, and local inspection
    without a model provider.
11. Support reproducible tests with fake model, rendering, safety, and Loop
    providers.
12. Fail loudly with machine-readable errors and corrective actions.

## 4. Non-goals

1. Reproduce the OfficeAgent plugin or host composition system.
2. Require a caller to implement OfficeAgent's `Task`, hook, skill, annotation,
   or conversation-filesystem APIs.
3. Expose internal prompts, worker names, or worker topology as a compatibility
   contract.
4. Make the model responsible for validation, output safety, persistence,
   cleanup, retries, or conflict policy.
5. Standardize LWS endpoint paths before the integration contract is selected.
6. Put credentials, access tokens, or baseline state in prompts, CLI arguments,
   ordinary results, or logs.
7. Treat a local work-bundle format as the universal LWS wire contract.
8. Silently downgrade a requested smart capability when a model or persistence
   provider is unavailable.
9. Let interactive-app policy weaken document, dashboard, or slide safety.
10. Use generated content as instructions to the Smart Tool or its host.

## 5. What the caller and agent see

The agent-visible contract has three layers:

1. The manifest helps an agent decide whether to select the Smart Tool.
2. Self-description tells the agent how to invoke the selected Smart Tool.
3. Capability results and errors are the only operational interface.

Internal skills, prompts, workers, hooks, workspace files, and provider calls are
not part of the agent-visible contract.

### 5.1 Before selection: `SMART_TOOL.md`

The canonical manifest travels with the installable distribution and is exposed
through the library. A proposed manifest is:

```markdown
---
smart_tool_format: 1
name: loop-artifact-studio
version: 0.1.0
description: >
  Creates and edits rich HTML artifacts and can persist them as Microsoft Loop
  pages. Use it for documents, dashboards, slides, and interactive artifacts
  when the caller should provide intent instead of orchestrating artifact
  skills and workers itself.
use_cases:
  - Create a polished Loop page from a user request and supplied context
  - Edit an existing Loop artifact while preserving its identity
  - Build a dashboard, presentation, or interactive HTML artifact
  - Validate or package an existing artifact without invoking a model
platforms:
  - linux
  - macos
  - windows
requires:
  - name: model-provider
    purpose: Required only for create and edit capabilities.
    optional: true
    install: docs/model-providers.md
  - name: loop-onboarding
    purpose: Required only when creating, fetching, or updating Loop artifacts.
    optional: true
    install: docs/loop-onboarding.md
---

Use this Smart Tool when the desired result is a rich HTML-based artifact, not
when the caller merely needs prose returned in chat.

The caller supplies the task and relevant context as data. The Smart Tool owns
planning, internal workers, assembly, validation, output safety, and optional
Loop persistence.

Persistence is opt-in. Creating or editing a local artifact does not write to
Loop unless the request explicitly asks for persistence.
```

The final platform list must include only platforms on which the distribution
has been tested.

### 5.2 After selection: capability self-description

After selecting the Smart Tool, an agent should receive a concise operating
contract equivalent to:

```text
Loop Artifact Studio creates and edits rich HTML artifacts.

Primary capabilities:
  create       Create an artifact from intent and supplied context.
  edit         Edit a supplied artifact or an existing Loop page.
  inspect      Describe the structure and metadata of an artifact.
  validate     Validate an artifact without invoking a model.
  package      Export an artifact as a local portable bundle.
  fetch        Fetch a Loop artifact as a local structured artifact.
  check        Report configured model, renderer, safety, and Loop capabilities.
  manifest     Return the installed Smart Tool manifest.

Use create or edit for user intent. Do not separately invoke internal workers,
assembly steps, safety checks, or persistence tools.

Context must be passed as content. File paths are a CLI convenience only.
Persistence and network access occur only when explicitly requested.
```

The complete `--help` or structured library description additionally gives:

- Which capabilities are model-backed.
- Which capabilities use the network.
- Which capabilities can write local files.
- Which capabilities can create or update a Loop artifact.
- Accepted artifact kinds.
- Argument names and types.
- Result schemas.
- Required configuration and corrective actions.

### 5.3 What the agent does not see

The agent does not receive:

- OfficeAgent skill text.
- Internal system prompts.
- Worker prompts or worker definitions.
- A list of hooks to call.
- Temporary workspace paths.
- Persistence credentials.
- Loop or Graph access tokens.
- Fluid or LWS baseline state.
- Provider-specific request bodies.
- Retry loops or conflict-resolution instructions.

Those details are private implementation resources. Exposing them would force
the caller to understand the workflow the Smart Tool exists to encapsulate.

## 6. Agent-facing capabilities

The public surface is intentionally smaller than the internal implementation.
Artifact variants are expressed through request fields rather than separate
commands for every OfficeAgent skill.

| Capability | AI required | Network | Side effects | Purpose |
|---|---:|---:|---:|---|
| `manifest` | No | No | None | Return the installed manifest |
| `capabilities` | No | No | None | Return argument, result, provider, and side-effect metadata |
| `check` | No | Optional | None | Report configuration and optionally probe providers |
| `inspect` | No | No | None | Describe artifact parts, assets, profile, and hashes |
| `validate` | No | No | None | Run deterministic profile and safety-independent validation |
| `package` | No | No | Requested local output | Export a portable artifact bundle |
| `fetch` | No | Yes | Optional requested local output | Fetch a Loop artifact |
| `create` | Yes | Optional | Optional local output and Loop create | Create an artifact from intent |
| `edit` | Yes | Optional | Optional local output and Loop update | Edit an artifact or Loop page |

Quality evaluation is a development and release function. It is not required in
the production `create` or `edit` request path.

### 6.1 `create`

`create` is the primary capability for new artifacts.

```python
@dataclass(frozen=True)
class CreateArtifactRequest:
    request_id: str
    instruction: str
    artifact_kind: Literal["document", "dashboard", "slides", "app"]
    context: tuple[ContextItem, ...] = ()
    title: str | None = None
    persistence: CreatePersistence | None = None
    local_output: LocalOutputOptions | None = None
```

The instruction states the desired result. The caller does not provide a worker
plan or choose an OfficeAgent skill version.

Examples:

```text
Create a one-page project update with status, completed milestones, risks, and
next steps.
```

```text
Create an executive dashboard from the supplied quarterly metrics. Include
trend charts, key variances, and a concise narrative.
```

```text
Create a six-slide presentation from the supplied launch plan for an executive
review.
```

The Smart Tool:

1. Selects the requested artifact profile.
2. Validates configuration and required persistence capabilities.
3. Mechanically assembles caller-provided context.
4. Plans the artifact.
5. Invokes the minimum internal workers needed.
6. Deterministically assembles the result.
7. Validates and renders the complete artifact.
8. Runs output-safety screening.
9. Writes requested local output.
10. Creates a Loop artifact only when requested.

### 6.2 `edit`

`edit` is the primary capability for changing artifacts.

```python
@dataclass(frozen=True)
class EditArtifactRequest:
    request_id: str
    instruction: str
    source: ArtifactSource
    selection: ArtifactSelection | None = None
    context: tuple[ContextItem, ...] = ()
    persist: bool = False
    local_output: LocalOutputOptions | None = None
```

Sources are either local content or a Loop locator:

```python
@dataclass(frozen=True)
class InlineArtifactSource:
    artifact: ArtifactPackage


@dataclass(frozen=True)
class LoopArtifactSource:
    locator: ArtifactLocator


ArtifactSource = InlineArtifactSource | LoopArtifactSource
```

An edit of a Loop artifact always fetches the authoritative content and opaque
update context through the configured Loop adapter. The caller does not supply
raw baseline state.

Examples:

```text
Add a risks section with two risks and mitigations. Preserve the existing
status, milestones, and next steps.
```

```text
Replace the selected chart with a comparison of actual versus forecast while
leaving the rest of the dashboard unchanged.
```

The selected-block path is an optimization:

1. Resolve the selected block deterministically.
2. Determine whether the requested change is eligible for a bounded edit.
3. Produce and validate a complete reassembled artifact.
4. If eligibility or validation fails, discard all candidate state.
5. Start the full edit from the unchanged authoritative source.

The fast path never becomes the only way to complete an edit.

### 6.3 `fetch`

`fetch` reads a Loop artifact through the configured adapter and returns the
canonical `ArtifactPackage`.

It may write a local export only when requested. It does not expose the opaque
update context returned by the adapter because baseline state is scoped to an
active edit transaction.

### 6.4 `validate`

`validate` accepts a canonical artifact or supported local package and returns a
structured report:

```python
@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    profile: str
    errors: tuple[ValidationFinding, ...]
    warnings: tuple[ValidationFinding, ...]
    metrics: ArtifactMetrics
```

Validation is deterministic and does not invoke a model. It covers:

- Artifact structure.
- Part and asset references.
- HTML parsing.
- Profile-specific runtime policy.
- Size and complexity bounds.
- Accessibility invariants that can be checked deterministically.
- Unsafe URL and resource references.
- Duplicate or missing stable identifiers.

Output-safety screening remains a separate mandatory stage before generated or
edited content is returned or persisted.

### 6.5 `package`

`package` exports a canonical artifact to a caller-selected local format. The
portable package is not assumed to be an LWS request body.

Possible package layouts may include:

```text
artifact/
├── artifact.json
├── parts/
│   ├── part-001.html
│   └── part-002.html
└── assets/
    └── chart-001.svg
```

The package contract belongs to the Smart Tool. A Loop adapter may map it to a
different endpoint-specific representation.

### 6.6 `check`

`check` is offline by default and reports:

- Installed tool and manifest version.
- Model-provider configuration.
- Renderer availability.
- Output-safety provider configuration.
- Loop adapter configuration.
- Credential-provider configuration.
- Declared artifact and persistence capabilities.

Network readiness probes require an explicit option and return only status and
corrective actions, never credentials.

## 7. Capability result

All create and edit paths return the same result family:

```python
@dataclass(frozen=True)
class ArtifactResult:
    request_id: str
    operation: Literal["create", "edit"]
    artifact: ArtifactPackage
    render: RenderOutcome
    local_outputs: tuple[LocalArtifact, ...]
    persistence: PersistenceOutcome | None
    warnings: tuple[ArtifactWarning, ...]
    diagnostics: tuple[Diagnostic, ...]


@dataclass(frozen=True)
class PersistenceOutcome:
    operation: Literal["create", "update"]
    locator: ArtifactLocator
    web_url: str | None
    outcome: Literal["created", "updated", "updated_with_server_merge"]
```

The result identifies every requested output. It does not include credentials,
baseline state, internal prompt text, or temporary workspace paths.

The CLI prints human-readable output by default and supports structured JSON for
agents and scripts. Requested results go to stdout; progress and diagnostics go
to stderr.

## 8. Canonical artifact model

The canonical model is independent of OfficeAgent files and LWS wire shapes:

```python
@dataclass(frozen=True)
class ArtifactPart:
    part_id: str | None
    title: str | None
    html: bytes


@dataclass(frozen=True)
class ArtifactAsset:
    asset_id: str
    media_type: str
    content: bytes


@dataclass(frozen=True)
class ArtifactPackage:
    kind: Literal["document", "dashboard", "slides", "app"]
    title: str
    parts: tuple[ArtifactPart, ...]
    assets: tuple[ArtifactAsset, ...]
    manifest: bytes | None
    artifact_hash: str
    provenance: GenerationProvenance
    validation: ValidationReport
```

Important invariants:

1. Every part is complete, valid UTF-8 HTML.
2. Part identifiers are stable when supplied by a fetched artifact.
3. Asset identifiers are unique and resolve locally.
4. The package contains no credentials or persistence baseline.
5. The artifact hash is computed over a canonical byte sequence defined by the
   Smart Tool package contract.
6. After final assembly and hashing, validators, renderers, and persistence
   adapters must not silently rewrite the package.
7. If an external service normalizes persisted HTML, the fetched representation
   is a new authoritative source for the next edit.

## 9. Artifact profiles

An artifact profile owns policy that differs by artifact kind:

```python
class ArtifactProfile(Protocol):
    kind: str

    def build_plan(
        self,
        request: CreateArtifactRequest | EditArtifactRequest,
    ) -> AuthoringPlan: ...

    def select_workers(
        self,
        plan: AuthoringPlan,
    ) -> tuple[WorkerSpec, ...]: ...

    def assemble(
        self,
        workspace: Workspace,
        plan: AuthoringPlan,
    ) -> ArtifactPackage: ...

    def validate(
        self,
        artifact: ArtifactPackage,
    ) -> ValidationReport: ...

    def required_persistence_capabilities(
        self,
        artifact: ArtifactPackage,
    ) -> RequiredLoopCapabilities: ...
```

| Profile | Capability |
|---|---|
| `document` | Rich pages, reports, plans, briefs, and long-form content |
| `dashboard` | Metrics, status cards, tables, charts, and responsive analytical layouts |
| `slides` | Ordered multi-part presentations with slide-level composition |
| `app` | Interactive HTML applications under an explicit sandbox and runtime policy |

Profiles share context handling, workspace isolation, worker execution, result
types, persistence, and error semantics. They do not share unsafe defaults.

For example, a document profile may prohibit scripts, while an app profile may
permit a constrained script bundle only under a renderer and persistence
sandbox that explicitly supports it.

## 10. Translating OfficeAgent concepts into the Smart Tool

The Smart Tool preserves capabilities, not harness primitives.

| OfficeAgent concept | Smart Tool implementation | Publicly visible? |
|---|---|---:|
| Skill instructions | Versioned profile and workflow resources | No |
| Skill selection | `artifact_kind` plus internal routing | Only the artifact kind |
| Subagent definition | Internal `WorkerSpec` | No |
| `Task` invocation | `WorkerExecutor.run()` | No |
| `read_agent` or join | `WorkerExecutor.join()` | No |
| Model-visible persistence tool | Application-owned persistence stage | Only the persistence option/result |
| Before-run cleanup hook | `WorkspaceTransaction.begin()` | No |
| Fast-edit hook | Explicit bounded-edit strategy | Only selection support |
| After-result persistence hook | `LoopArtifactStore.create/update()` stage | Only the persistence result |
| Output sentinels | Typed transaction state | No |
| Host annotations | `ArtifactResult` metadata | Structured result only |
| Conversation filesystem | Tool-owned request workspace | No |
| Rendering script | `Renderer` port | Render result only |
| Output-safety hook | `OutputSafetyProvider` port | Allow/block outcome on failure |
| Evaluation scripts | Development evaluation adapter | No production dependency |

### 10.1 Skills become versioned workflow resources

A skill currently combines several concerns:

- When to use a workflow.
- Artifact-specific design guidance.
- Prompt instructions.
- Worker-selection rules.
- Validation expectations.
- Tool usage.
- Persistence reminders.

The Smart Tool separates them:

```text
resources/
├── profiles/
│   ├── document/
│   │   ├── planner.md
│   │   ├── author.md
│   │   ├── edit.md
│   │   └── policy.json
│   ├── dashboard/
│   ├── slides/
│   └── app/
├── workers/
│   ├── chart.md
│   ├── graphic.md
│   ├── image.md
│   └── narration.md
└── schemas/
    ├── authoring-plan.json
    ├── worker-result.json
    └── edit-proposal.json
```

Prompt resources are versioned with the code that interprets their outputs.
Their output schemas are deterministic compatibility boundaries. Prompt wording
and worker topology are not.

### 10.2 Subagents become bounded internal workers

```python
@dataclass(frozen=True)
class WorkerSpec:
    worker_id: str
    role: Literal["chart", "graphic", "image", "narration", "section"]
    instruction: str
    inputs: tuple[WorkspaceInput, ...]
    expected_outputs: tuple[WorkspaceOutput, ...]
    limits: WorkerLimits
```

Workers:

- Receive only the files and context required for their assignment.
- Write only to declared workspace locations.
- Return structured outcomes.
- Cannot access Loop or Graph credentials.
- Cannot persist artifacts.
- Cannot mark the request successful.
- Cannot bypass validation or output safety.
- Cannot alter another worker's output.

The worker executor may use one model call, multiple model calls, internal
subagents, or another implementation. The agent-facing contract does not change.

### 10.3 Tools become typed provider ports

Host tools used by skills become explicit dependencies:

```python
class ModelProvider(Protocol): ...
class Renderer(Protocol): ...
class ImageProvider(Protocol): ...
class ChartRenderer(Protocol): ...
class OutputSafetyProvider(Protocol): ...
class LoopArtifactStore(Protocol): ...
class CredentialProvider(Protocol): ...
```

The application service grants providers only the data and permissions required
for their phase. A model provider cannot obtain persistence credentials merely
because both providers are installed in the same process.

### 10.4 Hooks become explicit lifecycle stages

Hooks are replaced by ordered application stages with typed inputs and outputs:

```text
request validation
    -> workspace begin
    -> source fetch
    -> planning
    -> worker execution
    -> assembly
    -> deterministic validation
    -> render validation
    -> output safety
    -> requested local writes
    -> requested persistence
    -> workspace finalize
    -> result
```

This ordering is code, not a prompt reminder. A host does not need to remember to
run a before-hook or after-hook.

## 11. Model-visible context

The primary model sees a bounded request assembled by code:

```text
SYSTEM WORKFLOW POLICY
  - role and artifact profile
  - allowed output schema
  - safety and untrusted-data boundaries
  - available internal worker categories

USER INTENT
  - exact caller instruction

ARTIFACT SOURCE
  - current parts and assets for edit, delimited as untrusted data

CALLER CONTEXT
  - typed context items, delimited as untrusted data

REQUEST CONSTRAINTS
  - artifact kind
  - requested title
  - selection, if any
  - size and runtime policy

EXPECTED OUTPUT
  - structured authoring plan or edit proposal
```

The model does not see:

- Provider credentials.
- Baseline state.
- Raw host configuration.
- Unrelated files in the caller's working directory.
- Persistence endpoint details.
- Hidden context gathered without caller authorization.

### 11.1 Context items

```python
@dataclass(frozen=True)
class ContextItem:
    item_id: str
    media_type: str
    content: bytes
    trust: Literal["user", "enterprise", "web", "generated"]
    source_label: str | None = None
```

At the library boundary, context is content, not a path or URL. A CLI may read an
explicit path into a context item. Optional future adapters may retrieve content
under their own authorization model, but the core still receives bytes.

Context assembly is mechanical:

- Preserve exact caller content subject to documented size limits.
- Do not ask the calling agent to summarize source material first.
- Delimit every item as untrusted data.
- Preserve source labels for provenance.
- Reject unsupported or oversized items with corrective errors.

## 12. Smart orchestration

The Smart Tool owns the orchestration strategy:

```text
Intent router
    -> profile planner
    -> primary author or editor
    -> optional bounded workers
    -> deterministic assembler
    -> validators and renderer
```

### 12.1 Planner

The planner produces a typed `AuthoringPlan`:

```python
@dataclass(frozen=True)
class AuthoringPlan:
    artifact_kind: str
    title: str
    parts: tuple[PartPlan, ...]
    assets: tuple[AssetPlan, ...]
    workers: tuple[WorkerRequest, ...]
    constraints: ArtifactConstraints
```

The planner may recommend workers but cannot grant them capabilities. Code
validates each worker request against the selected profile and configured
limits.

### 12.2 Primary author and editor

The primary author produces the base structure and complete part shells. Workers
produce bounded fragments or assets. Deterministic assembly resolves those
outputs into the final package.

The full editor receives the unchanged authoritative source and proposes a
complete desired artifact. The selected-block editor receives only the selected
block and permitted surrounding context, but its proposal is accepted only after
the complete artifact has been reassembled and validated.

### 12.3 Deterministic authority

Models propose. Code decides.

Deterministic code owns:

- Workspace lifecycle.
- Input normalization.
- Path and size enforcement.
- Worker permission boundaries.
- HTML parsing.
- Part and asset identity.
- Fragment assembly.
- Selection resolution.
- Profile validation.
- Rendering in the required sandbox.
- Output-safety invocation.
- Hashing.
- Local file writes.
- Persistence invocation.
- Retry classification.
- Error and conflict mapping.

## 13. Workspace model

Every request runs in an isolated transaction:

```text
request-root/
├── input/
│   ├── source/
│   └── context/
├── plan/
├── authored/
├── workers/
│   └── <worker-id>/
├── assembled/
├── rendered/
└── diagnostics/
```

Rules:

- The workspace is created by the tool, not selected by the model.
- Paths are generated and validated by code.
- Symlinks and escaping paths are rejected.
- Workers receive explicit read and write roots.
- Persistence credentials and baseline state are never written into worker
  directories.
- Final outputs are copied only to caller-requested locations.
- Temporary state is cleaned up according to a documented retention policy.
- A failed fast edit uses separate candidate state and cannot modify the
  authoritative full-edit input.

The tool uses the filesystem available to its process. Remote callers that do
not share that filesystem receive artifact bytes through the result and request
local output only where the deployment provides an accessible destination.

## 14. Loop persistence boundary

The core depends on an endpoint-neutral port:

```python
class LoopArtifactStore(Protocol):
    async def capabilities(self) -> LoopCapabilities: ...

    async def create(
        self,
        artifact: ArtifactPackage,
        options: LoopCreateOptions,
    ) -> StoredArtifact: ...

    async def fetch_for_edit(
        self,
        locator: ArtifactLocator,
    ) -> EditableArtifactSnapshot: ...

    async def update(
        self,
        snapshot: EditableArtifactSnapshot,
        desired: ArtifactPackage,
        options: LoopUpdateOptions,
    ) -> LoopUpdateResult: ...
```

### 14.1 Adapter capabilities

```python
@dataclass(frozen=True)
class LoopCapabilities:
    create: bool
    fetch: bool
    update_with_baseline: bool
    preserves_page_identity: bool
    supported_kinds: frozenset[str]
    supports_assets: bool
    supports_multiple_parts: bool
    supports_interactive_content: bool
    supports_concurrent_rebase: bool
    maximum_request_bytes: int | None
```

The application validates required capabilities before invoking a model. For
example:

- Slides require multiple parts.
- Image-bearing artifacts require assets.
- Persisted edits require fetch and baseline-aware update.
- Interactive apps require explicit interactive-content support.

### 14.2 Snapshot-bound update context

```python
@dataclass(frozen=True)
class EditableArtifactSnapshot:
    locator: ArtifactLocator
    artifact: ArtifactPackage
    update_context: UpdateContext
    fetched_at: datetime


@dataclass(frozen=True)
class UpdateContext:
    adapter_id: str
    opaque_state: bytes
```

`opaque_state` may contain an LWS or Fluid baseline. The core:

- Does not parse or synthesize it.
- Does not send it to a model.
- Does not put it in normal results.
- Does not log it.
- Does not pair it with another locator.
- Passes it unchanged to the adapter that produced it.

The adapter may enforce an expiration window. A stale or rejected baseline is a
typed conflict or baseline error, never a signal to perform an unconditional
overwrite.

### 14.3 Baseline-aware edit workflow

```text
Loop locator
    -> fetch_for_edit()
    -> ArtifactPackage + opaque UpdateContext
    -> model-backed edit
    -> deterministic assembly and validation
    -> output safety
    -> update(snapshot, desired)
    -> server-side derive/rebase/merge
    -> updated same-page result or typed conflict
```

The Smart Tool does not decide whether the adapter uses a CoWork endpoint, an
HTML-Canvas `.work` endpoint, an SDK, or another approved LWS surface.

### 14.4 Authentication and onboarding

Authentication is a deployment prerequisite represented by a provider:

```python
class CredentialProvider(Protocol):
    async def get_loop_credential(
        self,
        context: CredentialContext,
    ) -> AccessCredential: ...

    async def get_graph_credential(
        self,
        context: CredentialContext,
    ) -> AccessCredential: ...
```

Supported deployments may use delegated/OBO credentials, managed identity,
another approved application flow, or a host-operated token broker.

Onboarding documentation must cover:

- Loop and Graph audiences.
- Application registration and service approval.
- Delegated or application permission requirements.
- Client-scenario registration.
- Tenant and ring configuration.
- Redirect, broker, or proxy requirements.
- Local development configuration.
- Credential rotation and revocation.
- A non-secret readiness check.

Configuration names providers and registrations. It never contains a baseline or
requires a token on the command line.

### 14.5 Endpoint-specific adapter layout

```text
adapters/loop/
├── capabilities.py
├── configuration.py
├── credentials.py
├── gateway.py
├── serializer.py
├── parser.py
└── errors.py
```

Only this adapter knows endpoint paths and wire fields. The serializer maps
`ArtifactPackage` into the selected LWS representation. The parser maps fetched
content into the canonical model.

## 15. Safety model

### 15.1 Generated and fetched content is untrusted

User instructions, caller context, fetched artifacts, HTML, assets, and worker
outputs are data. None can:

- Change the system workflow.
- Grant network or filesystem access.
- Request credentials.
- Disable validation.
- Authorize persistence.
- Change profile policy.

### 15.2 Profile-specific runtime safety

Each profile declares:

- Allowed HTML elements and attributes.
- Script policy.
- External-resource policy.
- Navigation policy.
- Asset types and size limits.
- Renderer sandbox requirements.
- Persistence capability requirements.

Interactive apps use a separate policy. Enabling an app runtime does not enable
scripts in documents, dashboards, or slides.

### 15.3 Output safety

Output-safety screening runs after final deterministic assembly and before:

- Artifact bytes are returned.
- Local output is written.
- Loop persistence is attempted.

If the required safety provider is unavailable, the smart capability fails. It
does not return unscreened content.

## 16. Error contract

Errors are typed by phase:

```text
configuration
request_validation
context
planning
worker
assembly
artifact_validation
rendering
output_safety
local_output
authentication
persistence
baseline
conflict
timeout
```

Every public error contains:

```python
class ArtifactToolError(Exception):
    code: str
    phase: str
    message: str
    retry_safe: bool
    corrective_action: str | None
    request_id: str
```

Examples:

- `model_provider_not_configured`
- `loop_adapter_not_configured`
- `loop_onboarding_required`
- `unsupported_artifact_kind`
- `adapter_missing_multi_part_support`
- `selection_not_found`
- `worker_output_invalid`
- `render_failed`
- `output_safety_blocked`
- `baseline_expired`
- `server_merge_conflict`
- `ambiguous_create_result`

Partial completion is explicit. If local generation succeeds and Loop
persistence fails, the failure identifies retained recovery output. The CLI
still exits non-zero.

## 17. Proposed package structure

```text
loop-artifact-studio/
├── smart-tool.json
├── pyproject.toml
├── README.md
├── docs/
│   ├── artifact-profiles.md
│   ├── loop-onboarding.md
│   ├── model-providers.md
│   └── security.md
├── src/loop_artifact_studio/
│   ├── SMART_TOOL.md
│   ├── __init__.py
│   ├── api.py
│   ├── cli.py
│   ├── capabilities.py
│   ├── application/
│   │   ├── create.py
│   │   ├── edit.py
│   │   ├── fetch.py
│   │   ├── validate.py
│   │   └── package.py
│   ├── domain/
│   │   ├── artifacts.py
│   │   ├── context.py
│   │   ├── errors.py
│   │   ├── plans.py
│   │   ├── results.py
│   │   └── validation.py
│   ├── profiles/
│   │   ├── base.py
│   │   ├── document.py
│   │   ├── dashboard.py
│   │   ├── slides.py
│   │   └── app.py
│   ├── orchestration/
│   │   ├── planner.py
│   │   ├── author.py
│   │   ├── editor.py
│   │   ├── fast_edit.py
│   │   ├── workers.py
│   │   └── assembly.py
│   ├── ports/
│   │   ├── credentials.py
│   │   ├── loop_store.py
│   │   ├── model.py
│   │   ├── output_safety.py
│   │   └── renderer.py
│   ├── adapters/
│   │   ├── loop/
│   │   ├── models/
│   │   ├── rendering/
│   │   └── safety/
│   ├── deterministic/
│   │   ├── html.py
│   │   ├── selection.py
│   │   ├── hashing.py
│   │   ├── packaging.py
│   │   └── workspace.py
│   └── resources/
│       ├── profiles/
│       ├── workers/
│       └── schemas/
└── tests/
    ├── unit/
    ├── contract/
    ├── scenarios/
    ├── integration/
    └── evaluation/
```

All capability logic lives under the library. The CLI parses arguments, loads
explicit files into byte payloads, calls the library, and formats results.

## 18. Public library surface

The async library is authoritative:

```python
async def create_async(
    request: CreateArtifactRequest,
) -> ArtifactResult: ...


async def edit_async(
    request: EditArtifactRequest,
) -> ArtifactResult: ...


async def fetch_async(
    request: FetchArtifactRequest,
) -> FetchArtifactResult: ...


def validate(
    request: ValidateArtifactRequest,
) -> ValidationReport: ...


def package(
    request: PackageArtifactRequest,
) -> PackageResult: ...


def get_manifest() -> SmartToolManifest: ...


def describe_capabilities() -> CapabilityDescription: ...
```

A synchronous facade may be provided for simple callers. It must fail clearly
when invoked from an existing event loop rather than nesting event-loop runners.

## 19. Testing strategy

### 19.1 Unit tests

No model, browser, network, Loop, or Graph credentials:

- Request and result models.
- Profile routing.
- Context bounds and delimiting.
- Workspace isolation.
- Worker permissions.
- HTML and asset validation.
- Deterministic assembly.
- Fast-edit discard and fallback.
- Capability negotiation.
- Snapshot and update-context binding.
- Error envelopes.
- CLI stdout, stderr, and exit behavior.

### 19.2 Provider contract tests

The same contract suites run against fake and real implementations where
applicable:

- `ModelProvider`
- `Renderer`
- `OutputSafetyProvider`
- `LoopArtifactStore`
- `CredentialProvider`

The Loop store contract must prove:

1. Create returns a stable locator.
2. Fetch returns a canonical artifact and opaque update context.
3. Update receives the exact context from the corresponding fetch.
4. Update preserves the page identity.
5. Compatible concurrent changes produce a successful server-merge outcome.
6. Irreconcilable changes produce a typed conflict.
7. A rejected or stale baseline never falls back to unconditional overwrite.
8. Credentials and baseline state do not appear in results or logs.

### 19.3 Scenario tests

Scenario coverage tracks OfficeAgent capability parity:

| Scenario | Required result |
|---|---|
| Create document | Structured, rendered, validated page |
| Edit document | Same page identity and preserved unrelated content |
| Selected-block edit | Local change or trusted full-edit fallback |
| Create dashboard | Metrics, charts, and responsive layout |
| Edit dashboard | Targeted data or chart update |
| Create slides | Ordered multi-part presentation |
| Edit slides | Stable unaffected slide identities |
| Create app | Interactive artifact under the app sandbox |
| Edit app | Updated behavior without policy expansion |
| Asset workflow | Referenced images and graphics survive persistence |
| Concurrent edit | Server merge or typed conflict |

### 19.4 Evaluation

Model-quality evaluation measures:

- Instruction following.
- Content completeness.
- Visual hierarchy.
- Artifact-profile correctness.
- Edit locality.
- Preservation of unrelated content.
- Chart and graphic quality.
- Narration quality.
- Accessibility.

Deterministic correctness gates remain separate from model-quality scores.
`htmlcanvas-eval` may be used through an optional development adapter when it is
available independently.

### 19.5 Smart Tool conformance

The distribution runs the repository's conformance checks. Its deterministic
smoke capability is `manifest`:

```json
{
  "manifest": "src/loop_artifact_studio/SMART_TOOL.md",
  "cli_argv": ["loop-artifact-studio"],
  "deterministic_smoke": ["manifest"]
}
```

Conformance proves packaging and invocation shape, not model quality, provider
availability, or live Loop behavior.

## 20. Implementation sequence

### Phase 1: agent-visible contract and deterministic core

- Finalize the manifest and capability descriptions.
- Implement canonical artifact, request, result, and error models.
- Implement workspace transactions.
- Implement document, dashboard, slides, and app profile interfaces.
- Implement inspect, validate, package, manifest, capabilities, and offline
  check.

### Phase 2: OfficeAgent capability extraction

- Inventory relevant skills, subagents, tools, hooks, scripts, and evaluations.
- Build a capability-parity matrix.
- Move profile guidance into versioned resources.
- Define worker roles and structured output schemas.
- Preserve full create and full edit behavior before optimizing worker topology.

### Phase 3: smart create and edit

- Implement model-provider ports.
- Implement planner, author, editor, and bounded worker executor.
- Implement deterministic assembly and rendering.
- Implement output-safety enforcement.
- Add selected-block editing with full-edit fallback.

### Phase 4: endpoint-neutral Loop lifecycle

- Implement `LoopArtifactStore` and fake adapter.
- Implement capability negotiation.
- Implement fetch-bound opaque update contexts.
- Test same-page update, server merge, conflict, timeout, and ambiguous create.

### Phase 5: concrete LWS integration and onboarding

- Select the approved create, fetch, and baseline-update endpoint contracts.
- Implement serializer and parser adapters without changing the core API.
- Document Loop and Graph onboarding.
- Qualify authentication in each supported host.
- Run live create, fetch, update, concurrent merge, and conflict tests.

### Phase 6: distribution and catalog

- Complete installation documentation.
- Run conformance checks.
- Publish the independently usable distribution.
- Contribute a source pointer to the Smart Tools catalog.

## 21. Locked design decisions

1. The library is the Smart Tool; the CLI and optional MCP server are adapters.
2. `create` and `edit` are the primary agent-facing smart capabilities.
3. OfficeAgent capability parity is the product scope.
4. Skills, subagents, tools, and hooks are implementation inputs, not public
   runtime dependencies.
5. Models propose content; deterministic code owns workflow and enforcement.
6. Persistence is explicit and application-owned.
7. The canonical `ArtifactPackage` is independent of LWS endpoint wire shapes.
8. Endpoint selection remains inside the Loop adapter.
9. Loop and Graph onboarding is a documented deployment prerequisite.
10. Persisted edits fetch their own authoritative source and opaque baseline.
11. Baseline state is never model-visible or caller-supplied as raw bytes.
12. LWS owns server-side merge and conflict outcomes.
13. A conflict never silently becomes create, replace, or last-writer-wins.
14. Profiles isolate document, dashboard, slide, and app runtime policies.
15. Worker topology and prompt wording may evolve without changing the public
    capability contract.
16. Deterministic capabilities load and run without a model provider.
17. Output safety runs before generated or edited artifacts are exposed or
    persisted.

## 22. Open decisions

The following decisions can be made later without changing the core design:

1. The first concrete LWS endpoint family.
2. The credential-provider implementations supported by each host.
3. The first model provider.
4. Whether the initial release ships all profiles or stages them behind declared
   capability availability.
5. The exact portable package layout.
6. Maximum artifact, context, asset, and provider-request sizes.
7. Renderer implementation and app sandbox technology.
8. Local state and diagnostic retention periods.
9. Whether MCP ships in the first distribution.
10. The independently consumable location of `htmlcanvas-eval`.

These choices may change adapter availability and declared capabilities. They do
not change the agent-facing `create` and `edit` contract or the mapping of
OfficeAgent capabilities into the Smart Tool.
