---
summary: Creates a short, repository-specific AGENTS.md and makes CLAUDE.md a symlink to it, so every coding agent reads one instruction file.
---

# init-agents-md

`init-agents-md` writes a short `AGENTS.md` for a repository, with only what an agent could not quickly work out by itself, and makes `CLAUDE.md` a relative symlink to it. Every agent then reads the same instruction file.

## Why

Each line of an instruction file costs context on every agent run, and two files for two tools drift apart. This skill explores the repository and keeps a line only if it saves an agent exploration time or prevents a mistake: the commands people really run, where the important code lives, the sharp edges.

`AGENTS.md` is the single source, and Claude Code reads it through the link. An existing `CLAUDE.md` is used as seed material and replaced only after you agree.

## Installation

```bash
npx skills add MrBogomips/skills --skill init-agents-md
```

It is the same skill as in the `skills` plugin, installed under the name `init-agents-md` instead of `skills:init-agents-md`.

## Usage

Run it in the repository, or ask in words to create or bootstrap an `AGENTS.md`:

```text
/skills:init-agents-md
```

You get an `AGENTS.md` at the repository root and a `CLAUDE.md` that links to it: `readlink CLAUDE.md` prints `AGENTS.md`.

## Inputs and outputs

- `AGENTS.md` at the repository root, starting with `# AGENTS.md`.
- `CLAUDE.md`, a relative symlink to `AGENTS.md`.
- `.claude/CLAUDE.md`, only when the old `CLAUDE.md` held lines that concern Claude Code alone (its hooks, slash commands, tool names).

## Requirements

An agent harness with a shell and file access, and a filesystem and git setup that support symlinks. Where `git config core.symlinks` is `false`, or on a Windows checkout, the link arrives as a text file unless symlinks are enabled.

## Limitations

- When `AGENTS.md` already exists, the skill stops and asks whether to rewrite it.
- It does not port skills, agents, MCP servers or hooks from Claude Code to Codex: use `port-to-agents` for that.
