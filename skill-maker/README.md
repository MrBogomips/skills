---
summary: Opinionated Claude Code plugin for producing quality skills and plugins, starting with short public READMEs that follow one fixed structure.
---

# skill-maker

A Claude Code plugin for publishing skills and plugins that read as a single catalog. Its first skill checks and drafts the public `README.md` for a plugin and each skill it ships.

## Why

`SKILL.md` and the manifest are written for agents. People deciding whether to install a plugin need a short page explaining what it does and why it exists, yet most plugins format their READMEs inconsistently or omit them for individual skills. `skill-maker` enforces one fixed contract, validates the structure with scripts, and verifies every statement against the component's own files. The contract is opinionated: installing the plugin means adopting it.

## Included components

| Skill | What it does |
|---|---|
| [`skill-readme`](skills/skill-readme/README.md) | Checks and drafts the README for a plugin and each skill it ships. |

## Agents

`readme-reviewer`: read-only agent that rereads each README in a fresh context and checks its facts against the source files.

## Installation

```text
/plugin marketplace add MrBogomips/claude-plugins
/plugin install skill-maker@mrbogomips
```

Standalone skill installation is not supported; the skill depends on the plugin's scripts and reviewer agent.

## Quick start

From a plugin directory:

```text
/skill-maker:skill-readme check .
```

The command reports the plugin's distributed components and review notes for each README, without writing anything to disk.

## Requirements

Python 3.9 or later, available as `python3`.

## Limitations

- `skill-maker` handles one plugin at a time.
- The contract is fixed, and only English READMEs are supported.
- Fact-checking relies on a model, so those results can vary between runs.

## License

MIT
