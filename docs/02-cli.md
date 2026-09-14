# CLI Reference

The CLI is a thin wrapper over the [library](01-library.md). Each command maps to one library capability; this page documents only the command-line surface: flags, defaults, and exit behavior.

Results go to stdout and diagnostics to stderr. A failure the library can name prints its message to stderr and exits 1.

## Help

```
smart-tool-creator -h                 terse summary for a person: the commands, a line each
smart-tool-creator --help             the tool's skill, written for an agent driving it
smart-tool-creator <command> --help   one command in full: arguments, defaults, exit codes
```

`--help` on the tool prints what `lib.skill()` returns; the CLI adds nothing of its own. Every command answers both `-h` and `--help` with the same per-command help.

## smart-tool-creator manifest

```bash
# Print the tool's manifest as JSON
smart-tool-creator manifest
```

Deterministic; runs with no provider configured.

## smart-tool-creator init

```bash
# Scaffold a new smart tool into ./release-notes
smart-tool-creator init release-notes --description "Summarizes changelogs into release notes"

# Choose the directory and ship an Agent Skill alongside the tool
smart-tool-creator init release-notes --description "..." --directory ~/src/release-notes --skill
```

```
NAME                   the tool's slug, lowercase alphanumeric and hyphens
--description TEXT     required; becomes the manifest description
--directory PATH       where to create it; NAME under the current directory when omitted
--language             uv-python (default)
--intelligence         copilot-sdk (default)
--skill                also write skills/NAME/SKILL.md
```

Prints a plain summary: where the tool landed, what was written and committed, and which repositories were cloned into `reference/`. 
Deterministic; needs `git` and `uv` on `PATH`, a git identity for the first commit, and network access for `uv sync` and the reference clones.
