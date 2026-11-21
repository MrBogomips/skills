---
summary: Reviews the current Claude Code session and turns its errors, reworks and ambiguities into small fixes to the project's own files, applied only for the items you name.
---

# kaizen

`kaizen` reviews your current Claude Code session. It traces the errors, corrections, rework, and
ambiguities from the session back to the skill, rule, `CLAUDE.md` line, hook, or setting behind
them, and proposes small edits to the project's own files. It applies only the items you name.

## Why

When a `CLAUDE.md` line names the wrong command, a skill points to a missing folder, or two rules
conflict, the session pays for it in errors and rework. `kaizen` examines only what happened in the
current session, so every proposal cites an incident; if there is nothing to fix, it stops with
"nothing to review". A separate read-only reviewer checks proposed instruction text before you see
it. For assets the project does not own, such as a plugin or your user configuration, it gives
advice and identifies the owner. No files change until you name the items to apply.

## Installation

The skill is included in the [`kaizen` plugin](../../README.md#installation). You can also install
it standalone with the [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add MrBogomips/skills/kaizen -g
```

When installed standalone, there is no Stop hook to offer the retrospective, and no `kaizen-reviewer`
agent, so the review runs through a general-purpose subagent.

## Usage

Run the skill from the chat:

```text
/kaizen
```

You can also accept the offer from the plugin's hook, or ask in plain language what to fix in the
project's skills, rules, or settings after the session. `kaizen` replies in the chat with a recap:
project proposals, each with options and before-and-after text, followed by advice and pointers. No
files have changed at this point.

To apply changes, reply with the item IDs and option letters, such as `apply A1a, A3`. A plain "ok"
or "go ahead" applies nothing. Once the edits are applied, you get a report of what changed and how
to undo it with git.

## Requirements

- Claude Code: the retrospective reads the current session and its transcript.
- A project in a git repository: outside one, every finding is given as advice only.

## Limitations

- Edits only git-tracked files in the project. User configuration, plugins, managed settings,
  generated files, and untracked files receive advice only. Auto memory is never edited, though a
  fact from it that mattered can be proposed for a project file.
- Never creates skills or agents, and never commits changes.
- Reviews only the session it runs in and writes no report file; both the recap and the report stay
  in the chat.
- Points to the tool that owns a finding, such as `/doctor` or `/insights`, instead of doing that
  tool's job.