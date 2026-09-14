# CLI Reference

The CLI is a thin wrapper over the [library](01-library.md). Each command maps to one library capability; this page documents only the command-line surface: flags, defaults, and exit behavior. 
`-h` and `--help` print the same help, on the tool and on every command.

Results go to stdout and diagnostics to stderr. A failure the library can name prints its message to stderr and exits 1.

## smart-tool-creator manifest

```bash
# Print the tool's manifest as JSON
smart-tool-creator manifest
```

Deterministic; runs with no provider configured.
