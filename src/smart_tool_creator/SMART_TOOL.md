---
smart_tool_format: 1
name: smart-tool-creator
version: 0.1.0
description: >
  Creates, validates, and evaluates smart tools that follow the Amplifier Smart Tool
  Spec. Use when you want to package domain expertise as a smart tool, check that an
  existing one conforms to the spec, or measure how well its smart capabilities work.
use_cases:
  - Scaffold a new smart tool that is ready to push and conforms to the spec
  - Check an existing smart tool against the spec and its conformance kit
  - Build and run evaluations for a smart tool's model-backed capabilities
platforms:
  - linux
  - macos
  - windows
requires:
  - name: gh
    purpose: >
      Generates the token that signs in to GitHub Copilot. Without it, the model-backed
      capabilities cannot authenticate.
    optional: true
    install: https://cli.github.com/
  - name: github-copilot-subscription
    purpose: >
      A Copilot subscription on the account signed in to gh powers the model-backed
      capabilities. Without it, only the deterministic capabilities run.
    optional: true
    install: https://github.com/github/copilot-cli#prerequisites
---

# Smart Tool Creator

A smart tool for building smart tools. It scaffolds the structure the spec requires, checks
a tool against the spec, and evaluates the tool's model-backed capabilities in isolation.

## When to reach for it

- You have domain expertise in a harness, a bundle, or a set of skills and want to share it
  as a standalone tool that any agent can call.
- You built a smart tool and want to know whether it conforms to the spec before publishing it.
- You want evidence that a smart tool's model-backed capabilities work, independent of the
  harness that calls it.

## Straight and smart paths

Deterministic capabilities run with no provider configured. Model-backed capabilities go
through GitHub Copilot, signed in as the GitHub CLI's user, and say so in their help text.

## Worked invocations

```bash
smart-tool-creator manifest    # print the tool's manifest as JSON
```

The full library surface is documented in the repository's `docs/` directory.
