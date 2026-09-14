---
name: smart-tool-creator
description: >-
  Create, validate, and evaluate smart tools that follow the Amplifier Smart Tool Spec,
  by driving the smart-tool-creator smart tool from a CLI, a library, or an agent. Use
  when (1) packaging domain expertise as a standalone tool any agent can call, (2)
  checking an existing smart tool against the spec and its conformance kit, (3)
  measuring how well a smart tool's model-backed capabilities work. Triggers on "smart
  tool", "smart-tool-creator", "amplifier smart tool", "conformance kit", "SMART_TOOL.md",
  "smart-tool.json".
license: MIT
metadata:
  author: DavidKoleczek
  repository: https://github.com/DavidKoleczek/amplifier-smart-tool-creator
---

# Using smart-tool-creator

A smart tool for building smart tools. It scaffolds the structure the
[spec](https://github.com/microsoft/amplifier-smart-tools) requires, checks a tool against
the spec, and evaluates a tool's model-backed capabilities in isolation.

## Install

```bash
# as a CLI
uv tool install git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator

# as a library
uv add "amplifier-smart-tool-creator @ git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator"

# once, without installing
uvx --from git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator smart-tool-creator --help
```

## Use it

Run `smart-tool-creator --help`. It prints the tool's skill: when to use it, every
capability, worked invocations, sharp edges, and which files to read. Follow it. Confirm
every argument against `smart-tool-creator <command> --help` rather than memory.
