# CLI Reference

The CLI is a thin wrapper over the [library](01-library.md): one command per capability, taking the same arguments under the same names, and doing nothing the library does not. 
What each argument means and what a capability returns or raises is documented there. This page covers only what the CLI adds: the invocation shape, and what reaches stdout, stderr, and the exit code.

Results go to stdout and diagnostics to stderr. A failure the library can name prints its message to stderr and exits 1; a bad invocation exits 2.

## Help

```
smart-tool-creator -h                 terse summary for a person: the commands, a line each
smart-tool-creator --help             the tool's skill, written for an agent driving it
smart-tool-creator <command> -h       terse summary of one command: its arguments and defaults
smart-tool-creator <command> --help   that command's skill, written for an agent about to call it
```

`--help` on the tool prints what `lib.skill()` returns and on a command what `lib.skill("<command>")` returns; the CLI adds nothing of its own.

## smart-tool-creator manifest

```bash
smart-tool-creator manifest
```

`lib.load_manifest()`, printed as JSON.

## smart-tool-creator init

```bash
smart-tool-creator init NAME --description TEXT [--directory PATH] [--language uv-python] [--intelligence copilot-sdk] [--skill] [--repository URL]
```

`lib.init(name, description, ...)` with `NAME` positional and every other argument an option of the same name. 
Prints the result's `output_message`: where the tool landed, what was written and committed, the repositories cloned into `reference/`, and the next steps.

## smart-tool-creator add-smart-capability

```bash
smart-tool-creator add-smart-capability REQUEST [--directory PATH] [--context TEXT]... [--model gpt-6-astra] [--reasoning-effort low]
```

`lib.add_smart_capability(request, ...)` with `REQUEST` positional and `--context` repeated once per entry. 
Prints the result's `output_message`: the agent's report, one line per check with its status (a skipped check names why on the same line), the next steps, and any check still failing after the fix rounds. 
When one is, the exit code is 1; the work stays in the tool's working tree either way.
