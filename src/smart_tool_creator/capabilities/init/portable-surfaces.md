# Choosing an optional portable surface

`init --adapter mcp` generates a provider-free, typed `read_manifest` tool over the public
library and a stdio test. `--adapter mcp-app` adds a bundled read-only manifest view using
the official MCP Apps SDK. The view's Refresh button calls the same tool as an agent.

```bash
smart-tool-creator init release-notes --description "Drafts release notes from changelogs" --adapter mcp-app
cd release-notes
uv run --extra mcp pytest
uv run --extra mcp release-notes-mcp
```

The MCP extra remains optional in the generated package. No server starts during import,
scaffolding, or ordinary CLI use. Node.js/npm are required only to build or edit an App;
its compiled HTML ships in the package. MCP transports and resource/view metadata follow
the official SDKs. No host product is a dependency.

The generated `docs/03-portable-adapter.md` explains how to add real domain actions:
library-owned validation, typed shared calls, retained IDs and state preconditions,
idempotent receipts, durable drafts, bounded grants, owned-runner lifecycle, resource and
generated-content isolation, unknown usage, and independent-host tests. These are optional
design recommendations. They do not change v1 manifest fields or the conformance kit.

This starter proves manifest transport, not collaborative domain semantics. Add those in
the library and test them before advertising them. MCP servers may own their intelligence
or negotiate sampling; Smart Tool packaging and MCP interoperability are separate layers.
Sampling, Tasks, elicitation, and device permissions are not implemented by this starter.
