---
summary: Opinionated Claude Code plugin for producing quality skills and plugins, starting with short public READMEs that follow one fixed structure.
---

# skill-maker

Tools for people who publish skills and plugins and want them to read as one catalog. The first skill
checks and drafts the public `README.md` of a plugin and of each skill it ships.

## Why

`SKILL.md` and the manifest are written for agents. People deciding whether to install a plugin need
a short page that says what it does and why it exists, and most plugins give each a different shape,
or none for the single skills. `skill-maker` fixes one structure, checks it with scripts, and checks
every statement against the component's own files. The contract is opinionated: installing the
plugin means adopting it.

## Included components

| Skill | What it does |
|---|---|
| [`skill-readme`](skills/skill-readme/README.md) | Checks and drafts the README of a plugin and of each skill it ships. |

## Agents

`readme-reviewer`: rereads each README in a fresh context and checks its facts against the sources,
read-only.

## Installation

```text
/plugin marketplace add MrBogomips/claude-plugins
/plugin install skill-maker@mrbogomips
```

**Standalone skills: no, plugin only.** The skill needs the plugin's scripts and reviewer agent.

## Quick start

From the folder of a plugin:

```text
/skill-maker:skill-readme check .
```

You get the components the plugin distributes and the review notes for each README. Nothing is
written to disk.

## Requirements

Python 3.9 or later as `python3`.

## Limitations

- One plugin at a time.
- The contract is fixed, and READMEs are in English.
- Facts are judged by a model, so that part of a check can vary between runs.

## License

MIT
