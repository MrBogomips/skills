---
summary: Claude Code plugin that checks skills and plugins against one authoring rulebook, audits whole skill collections, and checks or drafts their public READMEs.
---

# skill-maker

A Claude Code plugin for publishing skills and plugins that hold up. It checks one skill or plugin
against an authoring rulebook, audits a whole collection of skills, and checks or drafts their public
READMEs. Every finding comes with its evidence, and your files change only when you approve.

## Why

A skill is written for agents, so its flaws stay hidden until it misfires: a trigger in the wrong
language, test material shipped with it, a description that overlaps another skill. People choosing it
need a README, which is often missing or drifts from the code. skill-maker checks both against fixed
rules, with scripts and an independent read-only reviewer, and hands off to Anthropic's own authoring
tools where they already do the job. The rulebook and the README contract are opinionated: installing
the plugin means adopting them.

## Included components

| Skill | What it does |
|---|---|
| [`skill-check`](skills/skill-check/README.md) | Checks one skill or plugin against the rulebook and fixes only the findings you approve by ID. |
| [`skill-audit`](skills/skill-audit/README.md) | Gives every skill in a collection a keep, improve, merge or retire verdict, read-only. |
| [`skill-readme`](skills/skill-readme/README.md) | Checks and drafts the README of a plugin and of each skill it ships. |

## Agents

- `rulebook-reviewer`: reviews skills, agents and plugins against the rulebook in a fresh context, read-only.
- `readme-reviewer`: rereads each README in a fresh context and checks its facts against the source files, read-only.

## Installation

```text
/plugin marketplace add MrBogomips/claude-plugins
/plugin install skill-maker@mrbogomips
```

**Standalone skills: no, plugin only.** The skills run the plugin's scripts, read its rulebook and
dispatch its reviewer agents.

## Quick start

```text
/skill-maker:skill-check <skill or plugin folder>
```

You get a report of numbered findings, each with its rule ID and `path:line`, and nothing changes until
you answer with the IDs to apply.

## Requirements

Python 3.9 or later, available as `python3`. Strongly recommended: skill-creator and plugin-dev (see
[Recommended tools](#recommended-tools)).

## Limitations

- The skills read files: they never run a skill or its evals.
- The reviews rely on a model, so their findings can vary between runs.

## Authoring rulebook

The rules live in [`shared/rules/`](shared/rules/README.md), grouped by ID: the value of a skill over
native features (V), `SKILL.md` and descriptions (S), testing (T), structure and manifests (P), and
Claude Code agents, hooks and commands (C). Your project's own `AGENTS.md` or `CLAUDE.md` wins over
official guidance, and both win over the rulebook.

## Recommended tools

Strongly recommended. skill-maker works without them, falling back to the manual methods of its
rules, but the reports of `skill-check` and `skill-audit` list each one that is missing, on every run:

- **skill-creator**, for drafting skills, evals and description tuning:
  `/plugin install skill-creator@claude-plugins-official`
- **plugin-dev**, for writing agents, hooks, commands and plugin settings:
  `/plugin install plugin-dev@claude-plugins-official`

What each one adds, and the other official tools skill-maker defers to, are in
[`shared/official-references.md`](shared/official-references.md).

## License

MIT
