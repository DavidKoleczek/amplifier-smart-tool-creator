`add-smart-capability` extends a smart tool that already exists: an agent reads the tool,
implements one model-backed capability in its library, exposes it from the CLI, writes the
tests and the docs, then runs the tool's own checks (`uv run pytest`, the conformance kit,
and `prek run --all-files` when `prek` is installed) and fixes what they report. Nothing is
committed; the working tree is left for you to review.

```bash
smart-tool-creator add-smart-capability \
  "Given an incident id, fetch its chat transcript and alert timeline from the incident platform and draft a blameless postmortem: summary, impact, contributing factors, and action items with owners" \
  --directory ~/src/incident-postmortem \
  --context "The platform client is src/incident_postmortem/platform.py; fetch through it, never call the API directly" \
  --context "Our postmortem template is at ~/notes/postmortem-template.md; match its headings"
```

```python
from pathlib import Path

from smart_tool_creator.lib import add_smart_capability

added = add_smart_capability(
    "Given an incident id, fetch its chat transcript and alert timeline from the incident platform "
    "and draft a blameless postmortem: summary, impact, contributing factors, and action items with owners",
    directory=Path("~/src/incident-postmortem").expanduser(),
    context=[
        "The platform client is src/incident_postmortem/platform.py; fetch through it, never call the API directly",
        "Our postmortem template is at ~/notes/postmortem-template.md; match its headings",
    ],
)
added.report, added.checks, added.fix_rounds, added.output_message
```

## Arguments

- `--backend`: Creator's runtime, `copilot-sdk` (default) or `amplifier-agent`.
- `--provider`: required with Amplifier, along with an explicit `--model`. For example:
  `add-smart-capability "Summarize a changelog" --backend amplifier-agent --provider anthropic --model claude-sonnet-4-6`.
  Install the `[amplifier]` extra and configure that provider's environment credentials or
  `amplifier-agent auth`. Copilot defaults below do not apply to Amplifier.
  Library callers use `lib.create_intelligence("amplifier-agent", provider="anthropic")`.
  Amplifier fix rounds reuse the same adapter and transcript. Writable runs may execute
  host shell commands; this is not an OS sandbox.

- `REQUEST`: the whole brief for one capability: what it does, for whom, and what it takes in
  and gives back. Required.
- `--directory PATH`: the smart tool to work in; the current directory when omitted. It must
  hold a `smart-tool.json` at its root, and no parent is searched, so a workspace holding
  several tools is never extended by accident.
- `--context TEXT`: repeatable free text, usually paths to notes, transcripts, or exemplars
  the agent should read before it designs anything. It reads the paths itself, so name them
  rather than pasting their contents.
- `--model`: the model the agent runs on. Defaults to `gpt-6-astra`.
- `--reasoning-effort`: how hard the model thinks before it acts, one of `low` (the default),
  `medium`, `high`, `xhigh`, `max`.
- `intelligence`, library only: the `Intelligence` implementation the agent runs through;
  `default_intelligence()` when omitted. Tests inject a fake.

## Result

`AddedCapability` carries `root`, the extended tool's distribution root; `report`, the
agent's final message, which names the capability, the files it touched, the command to try
it, and its caveats; `checks`, one entry per check with its `name`, `command`, `status`
(`passed`, `failed`, or `skipped`), and the tail of its output when it failed or the reason
when it was skipped; `fix_rounds`, the extra agent runs spent on failing checks, at most 2;
and `output_message`, all of that for the calling agent, which is what the CLI prints.

The prek check is skipped, never failed, when the tool has no `.pre-commit-config.yaml` or
`prek` is not on `PATH`; the conformance check is skipped when the kit itself could not run,
and names the failing rules when it fails. A check still failing when the work stops is returned rather than
raised and named in the message, and the CLI exits 1; the work stays in the tool's working
tree either way, and what it is worth is the caller's call.

## Failures

Model-backed: by default it runs through GitHub Copilot, signed in as the GitHub CLI's user, so `gh`
must be installed and `gh auth login` completed with an account that has a Copilot
subscription. With nothing configured it fails immediately and names what to set; it never
falls back to a deterministic answer.

A failure prints its message to stderr and exits 1: the directory holds no `smart-tool.json`
(scaffold it with `init` first), the request is empty, `uv` is not on `PATH`, the
intelligence preflight fails, or the agent itself fails. An agent failure may leave partial
edits in the tool's working tree, and the message says so. A bad invocation exits 2.
