---
summary: Reviews the current Claude Code session and turns its errors, reworks and ambiguities into small fixes to the project's own files, applied only for the items you name.
---

# kaizen

`kaizen` reviews the Claude Code session you are in. It takes the errors, reworks, corrections and
ambiguities met in it, links each to the skill, rule, `CLAUDE.md` line, hook or setting behind it, and
proposes small edits to the project's own files. You name the items and it applies only those.

## Why

A `CLAUDE.md` line that names the wrong command, a skill that points at a folder that does not exist,
two rules that disagree: each one costs a session an error or a rework. `kaizen` reviews only what this
session ran into, so every proposal cites an incident, and a session with nothing to fix ends with
"nothing to review". A separate read-only
reviewer rereads proposed instruction text before you see it. For an asset the project does not own,
such as a plugin or your user configuration, you get advice and its owner. Nothing changes until you
name the items.

## Installation

The skill comes with the [`kaizen` plugin](../../README.md#installation). It also installs alone with
the [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add MrBogomips/skills/kaizen -g
```

Installed alone it has no Stop hook, so nothing offers the retrospective, and no `kaizen-reviewer`
agent, so the review runs through a general-purpose subagent.

## Usage

```text
/kaizen
```

You can also accept the offer the plugin's hook makes, or ask in words what to fix in the project's
skills, rules or settings after this session. The reply is a recap in the chat: project proposals,
each with options and before and after text, then advice and pointers. Nothing has been changed at
that point.

Reply with item IDs and option letters, for example `apply A1a, A3`. A plain "ok" or "go ahead"
applies nothing. After the apply you get a report of what was applied and how to undo it with git.

## Requirements

- Claude Code: the retrospective reads the Claude Code session and its transcript.
- A project in a git repository: outside one, every finding is advice.

## Limitations

- It edits only files tracked by git in the project. Your user configuration, plugins, managed
  settings, generated files and untracked files get advice only. Auto memory is never edited; a fact
  from it that mattered can be proposed for a project file.
- It never creates skills or agents and never commits.
- It reviews one session, the one it runs in, and leaves no report file: recap and report stay in the chat.
- It points at the tool that owns a finding, such as `/doctor` or `/insights`, instead of doing its
  job.
