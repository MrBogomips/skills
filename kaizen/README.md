# kaizen

A session that hits errors, reworks or ambiguities often traces them to a project asset: a CLAUDE.md
line that names the wrong command, a skill that sends the agent to the wrong folder, two rules that
disagree. `kaizen` reviews the assets the session actually used, links each incident to the asset
behind it, and proposes small fixes to the project's own files, **applied only for the items you name**.

## What it does

- Takes the assets active in the session (instruction files, skills, subagents, MCP tools, hooks,
  settings) and the incidents met in it.
- Proposes edits with options, before and after text and net line counts, for files tracked by git in
  the project. A read-only reviewer checks each proposed text for contradictions, duplicates and
  needless growth before you see it.
- Gives advice only for everything else: your user configuration, plugins, managed settings, generated
  files, auto memory. It never creates skills or agents and never commits.
- Points at the tool that owns a finding instead of doing its job: `/doctor prompt-audit` for static
  audits of instruction files, `/doctor` and `/skill-doctor` for unused assets, `/insights` for patterns
  across sessions, `/fewer-permission-prompts` for permission rules.

## When it runs

Only when you ask: `/kaizen`, or by accepting the offer.

A Stop hook makes the offer at most once per session, when the session crosses one of these signals:
more than 7 project files edited, more than 7 files or 200 lines changed in the working tree (counted
only once the session has edited a project file), a change
under `.claude/`, to `CLAUDE.md`, a lockfile or a migration, 3 or more tool errors, or 2 or more
interruptions. The model then judges reworks and ambiguities and, only if the gate trips, ends its reply
with one line offering kaizen. The hook calls no model itself and never blocks.

The hook stays silent in headless and SDK runs. To turn it off, set `KAIZEN_STOP_HOOK=0`.

## Usage

```
/kaizen
```

Reply to the recap with item IDs and option letters, for example `apply A1a, A3`.

## Installation

As a Claude Code plugin, from the `mrbogomips` marketplace (recommended):

```bash
claude plugin marketplace add MrBogomips/claude-plugins
claude plugin install kaizen@mrbogomips
```

**Standalone skill: yes, with less.** The `kaizen` skill also installs alone, in Claude Code or another
agent, with the [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add MrBogomips/skills/kaizen -g
```

Installed that way it has no Stop hook, so nothing offers the retrospective: run it with `/kaizen`. It also
has no `kaizen-reviewer` agent, so the review runs through a general-purpose subagent. The retrospective
reads the Claude Code session transcript, so it is meant for Claude Code.

Earlier versions were published as `kaizen@mrbogomips-tools` from `MrBogomips/claude-code`. Installations
cannot move between marketplaces: uninstall that one and install `kaizen@mrbogomips`.

Version 2.0.0 replaces the KPI loop engine of 1.x (profiles, measurement scripts, `.kaizen/runs/`).
Version 1.2.0 remains in the repository history.

## License

MIT
