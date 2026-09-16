# Smart Tool Creator

Smart Tool Creator is the [Smart Tool](https://github.com/microsoft/amplifier-smart-tools) for building smart tools.
It scaffolds the structure the spec requires, checks a tool against the spec and its conformance kit, and evaluates a tool's model-backed capabilities in isolation.
The intelligence inside is implemented with the [GitHub Copilot SDK](https://github.com/github/copilot-sdk) behind an interface that other agent SDKs can implement with others to come.

## Installation

Prerequisites:
- Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.9.17 or newer.
- [GitHub CLI](https://cli.github.com/) signed in to an account with a [GitHub Copilot subscription](https://github.com/github/copilot-cli#prerequisites) for the intelligent features.

```bash
uv tool install git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator
```

To use it as a library:

```bash
uv add "amplifier-smart-tool-creator @ git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator"
```

To run it once without installing:

```bash
uvx --from git+https://github.com/DavidKoleczek/amplifier-smart-tool-creator smart-tool-creator --help
```

To teach a coding agent how to use it, install the [skill](skills/smart-tool-creator/SKILL.md):

```bash
npx skills add DavidKoleczek/amplifier-smart-tool-creator
```

To update:

```bash
uv tool upgrade amplifier-smart-tool-creator
npx skills update smart-tool-creator   # add --global if the skill was installed globally
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

# Scaffold a new smart tool into ./incident-postmortem, optionally with an Agent Skill and the repository it will be pushed to. Specify a specific directory with --directory
smart-tool-creator init incident-postmortem --description "Writes, reviews, and tracks blameless postmortems from your incident platform's records" --skill --repository https://github.com/org/incident-postmortem

# Add one model-backed capability to an existing smart tool, verified against that tool's own checks
smart-tool-creator add-smart-capability "Given an incident id, fetch its chat transcript and alert timeline from the incident platform and draft a blameless postmortem: summary, impact, contributing factors, and action items with owners" --directory ./incident-postmortem
```

See the [CLI reference](docs/02-cli.md) for every flag and the [library reference](docs/01-library.md) for the Python surface.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment.
