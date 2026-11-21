---
summary: Slims down and restructures a project's AGENTS.md and CLAUDE.md without changing what they tell agents, with every change proposed as a diff you approve.
---

# optimize-agents-md

`optimize-agents-md` trims and restructures a project's instruction files (`AGENTS.md`, `CLAUDE.md`, nested files, and `.claude/rules`) so they use less context on every run without changing what they tell agents. It removes history, resolves conflicts with the project's skills, and moves details needed only for specific folders or tasks into files that load on demand.

## Why

Over time, instruction files accumulate history, rules already covered by a skill, and details for a single folder that still load on every run. Trimming them by hand risks dropping a rule.

This skill measures how many lines and bytes each harness loads at startup, before and after. It proposes every change as a diff for you to approve, then checks that no line was dropped without approval. If the file is already lean, it says so and proposes no changes.

## Installation

```bash
npx skills add MrBogomips/skills --skill optimize-agents-md
```

This installs the same skill included in the `skills` plugin, under the name `optimize-agents-md` instead of `skills:optimize-agents-md`.

## Usage

```text
/skills:optimize-agents-md [--check] [--threshold N] [path]
```

| Argument | Description |
| --- | --- |
| `--check` | Report and proposals only; changes no files. |
| `--threshold N` | Minimum size, in lines, of a block worth moving out of the root file (default: 20). |
| `path` | Project root (default: the git root, or the current folder without git). |

To preview the report without modifying files, run:

```text
/skills:optimize-agents-md --check
```

Each run produces a single report containing the questions only you can answer, the lines and bytes each harness loads at startup before and after, and the numbered changes with their diffs. Without `--check`, the skill then applies only the changes you approve.

## Requirements

Requires an agent harness with shell and file access, bash, and the standard BSD or GNU tools. The skill uses git when present.

## Limitations

- Does not create an initial `AGENTS.md` (use `init-agents-md`) or port a Claude Code setup to Codex (use `port-to-agents`).
- Edits files in place because they must keep their names to load. When present, git keeps the previous version; without git, the skill saves a copy of each file before editing it.