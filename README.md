# Smart Tool Creator

Smart Tool Creator is the [Smart Tool](https://github.com/microsoft/amplifier-smart-tools) for building smart tools.
It scaffolds the structure the spec requires, checks a tool against the spec and its conformance kit, and evaluates a tool's model-backed capabilities in isolation.
The intelligence inside is implemented with the [GitHub Copilot SDK](https://github.com/github/copilot-sdk) behind an interface that other agent SDKs can implement with others to come.

## Installation

Prerequisites:
- Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).
- [GitHub CLI](https://cli.github.com/) signed in to an account with a [GitHub Copilot subscription](https://github.com/github/copilot-cli#prerequisites) for the intelligent features.

```bash
uv tool install git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator
```

To use it as a library:

```bash
uv add "amplifier-smart-tool-creator @ git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator"
```

To upgrade to the latest:

```bash
uv tool upgrade amplifier-smart-tool-creator
```

To run it once without installing:

```bash
uvx --from git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator smart-tool-creator --help
```

To teach a coding agent how to use it, install the [skill](skills/smart-tool-creator/SKILL.md):

```bash
npx skills add DavidKoleczek/amplifier-smart-tool-creator
```

To uninstall:

```bash
uv tool uninstall amplifier-smart-tool-creator
npx skills remove smart-tool-creator   # add --global if the skill was installed globally
```

## Interface

```bash
# Print the tool's manifest as JSON
smart-tool-creator manifest

# Scaffold a new smart tool into ./release-notes, optionally with an Agent Skill. Specify a specific directory with --directory
smart-tool-creator init release-notes --description "Summarizes changelogs into release notes" --skill
```

See the [CLI reference](docs/02-cli.md) for every flag and the [library reference](docs/01-library.md) for the Python surface.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment.
