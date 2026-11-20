---
summary: Slims down and restructures a project's AGENTS.md and CLAUDE.md without changing what they tell agents, with every change proposed as a diff you approve.
---

# optimize-agents-md

`optimize-agents-md` makes a project's instruction files (`AGENTS.md`, `CLAUDE.md`, nested ones, `.claude/rules`) cost less context on every run while they tell agents the same things. It removes history, settles conflicts with the project's skills, and moves detail that only some folders or tasks need into files that load on demand.

## Why

Instruction files grow: history, rules that a skill already states, detail about one folder that every run pays for. Trimming them by hand risks dropping a rule.

This skill measures the lines and bytes each harness loads at start, before and after. It proposes every change as a diff you approve, and afterwards checks that no line was lost without approval. When the file is already lean it says so and invents no change.

## Installation

```bash
npx skills add MrBogomips/skills --skill optimize-agents-md
```

It is the same skill as in the `skills` plugin, installed under the name `optimize-agents-md` instead of `skills:optimize-agents-md`.

## Usage

```text
/skills:optimize-agents-md [--check] [--threshold N] [path]
```

- `--check`: report and proposals only; change nothing.
- `--threshold N`: the minimum size, in lines, of a block worth moving out of the root file (default 20).
- `path`: the project root (default: the git root, or the current folder without git).

```text
/skills:optimize-agents-md --check
```

You get one report: the questions only you can answer, the lines and bytes loaded at start per harness before and after, and the numbered changes with their diffs. Without `--check`, the skill then applies only the changes you approve.

## Requirements

An agent harness with a shell and file access, bash and the standard BSD or GNU tools. git is used when present.

## Limitations

- It does not create a first `AGENTS.md` (use `init-agents-md`) and does not port a Claude Code setup to Codex (use `port-to-agents`).
- The files are revised in place, since they must keep their names to load: git keeps the previous version, and without git the skill keeps a copy of each file before editing it.
