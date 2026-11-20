---
summary: Retrospective of a Claude Code session that links its errors, reworks and ambiguities to the skill, rule or setting behind each and applies only the small project fixes you name.
---

# kaizen

`kaizen` is a retrospective of the Claude Code session you are in. It links the errors, reworks and
ambiguities of the session to the asset behind each one, a `CLAUDE.md` line, a skill or a rule, and
proposes small fixes to the project's own files, **applied only for the items you name**.

## Why

A session that hits errors, reworks or ambiguities often traces them to an asset: a `CLAUDE.md` line
that names the wrong command, a skill that sends the agent to the wrong folder, two rules that
disagree. The plugin puts the retrospective where it is useful: a hook can offer it when the session
had friction, and a reviewer rereads the text proposed for instruction files, skills and agents before
you see it. The retrospective never starts on its own: you run `/kaizen` or accept the offer.

## Included components

| Skill | What it does |
|---|---|
| [`kaizen`](skills/kaizen/README.md) | Runs the retrospective of the current session and applies the fixes you authorize. |

## Agents

- `kaizen-reviewer`: rereads the edits proposed to instruction files, skills and agents before you see
  them, read-only.

## Hooks

- `Stop`: offers the retrospective in one line, at most once per session, when the session had broad
  changes or friction. Never blocks. Off with `KAIZEN_STOP_HOOK=0`.

## Installation

```bash
claude plugin marketplace add MrBogomips/claude-plugins
claude plugin install kaizen@mrbogomips
```

**Standalone skills: yes, with less.** The `kaizen` skill also installs alone, as its
[README](skills/kaizen/README.md#installation) shows. Installed that way it has no Stop hook, so
nothing offers the retrospective, and no `kaizen-reviewer` agent, so the review runs through a
general-purpose subagent.

Earlier versions were published as `kaizen@mrbogomips-tools` from `MrBogomips/claude-code`.
Installations cannot move between marketplaces: uninstall that one and install `kaizen@mrbogomips`.

## Quick start

At the end of a working session in a project, run:

```text
/kaizen
```

You get a recap in the chat: the proposals, each with its incident and its before and after text, or
one line saying there is nothing to review. Nothing is changed until you reply with the item IDs.

## License

MIT
