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

The tool's `SMART_TOOL.md` frontmatter as structured data.

```python
def load_manifest() -> Manifest
```
