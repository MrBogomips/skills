---
summary: Retrospective of a Claude Code session that links its errors, reworks and ambiguities to the skill, rule or setting behind each and applies only the small project fixes you name.
---

# kaizen

`kaizen` runs a retrospective on your current Claude Code session. It links errors, rework, and
ambiguities from the session to the `CLAUDE.md` line, skill, or rule behind each one, then proposes
small fixes to your project files and applies only the items you approve.

## Why

Session errors, rework, and ambiguities often trace back to your project setup: a `CLAUDE.md` line
naming the wrong command, a skill pointing the agent to the wrong folder, or two conflicting rules.
With this plugin, a hook can offer a retrospective after a session with friction, and a reviewer
checks proposed edits to instruction files, skills, and agents before you see them. The
retrospective never starts on its own; it runs only when you invoke `/kaizen` or accept the offer.

## Included components

| Skill | What it does |
|---|---|
| [`kaizen`](skills/kaizen/README.md) | Runs a retrospective on the current session and applies the fixes you approve. |

## Agents

- `kaizen-reviewer`: reviews proposed edits to instruction files, skills, and agents before you see
  them (read-only).

## Hooks

- `Stop`: offers a one-line retrospective prompt at most once per session after broad changes or
  friction. It never blocks, and you can disable it with `KAIZEN_STOP_HOOK=0`.

## Installation

```bash
claude plugin marketplace add MrBogomips/claude-plugins
claude plugin install kaizen@mrbogomips
```

You can also install the `kaizen` skill on its own; see the
[skill README](skills/kaizen/README.md#installation) for instructions. A standalone install leaves
out the Stop hook, so nothing offers the retrospective, and omits the `kaizen-reviewer` agent, so
reviews run through a general-purpose subagent.

Earlier versions were published as `kaizen@mrbogomips-tools` from `MrBogomips/claude-code`. Because
installations cannot migrate between marketplaces, uninstall that version before installing
`kaizen@mrbogomips`.

## Quick start

At the end of a working session in your project, run:

```text
/kaizen
```

You get a recap in the chat listing each proposed fix with its related incident and before-and-after
text, or a single line stating there is nothing to review. No files change until you reply with the
item IDs.

## License

MIT
