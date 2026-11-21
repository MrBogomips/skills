---
summary: Creates a short, repository-specific AGENTS.md and makes CLAUDE.md a symlink to it, so every coding agent reads one instruction file.
---

# init-agents-md

`init-agents-md` creates a short `AGENTS.md` for a repository with only the details an agent cannot quickly discover on its own, and makes `CLAUDE.md` a relative symlink to it. Every coding agent then reads the same instruction file.

## Why

Each line in an instruction file consumes context on every agent run, and separate files for different tools drift apart. This skill explores the repository and keeps a line only if it saves exploration time or prevents a mistake: the commands people actually run, where the important code lives, and the sharp edges.

`AGENTS.md` is the single source, and Claude Code reads it through the symlink. If a `CLAUDE.md` already exists, the skill uses it as seed material and replaces it only after you confirm.

## Installation

```bash
npx skills add MrBogomips/skills --skill init-agents-md
```

This installs the same skill from the `skills` plugin, under the name `init-agents-md` instead of `skills:init-agents-md`.

## Usage

Ask in plain language to create or bootstrap an `AGENTS.md`, or invoke the skill directly in the repository:

```text
/skills:init-agents-md
```

The skill writes `AGENTS.md` at the repository root and symlinks `CLAUDE.md` to it; `readlink CLAUDE.md` prints `AGENTS.md`.

## Inputs and outputs

The skill reads the repository and any existing `CLAUDE.md`, then writes:

- `AGENTS.md` at the repository root, starting with `# AGENTS.md`.
- `CLAUDE.md`, a relative symlink to `AGENTS.md`.
- `.claude/CLAUDE.md`, only when the previous `CLAUDE.md` contained lines specific to Claude Code (hooks, slash commands, and tool names).

## Requirements

You need an agent harness with shell and file access, along with a filesystem and Git setup that support symlinks. If `git config core.symlinks` is `false`, or on a Windows checkout, the symlink appears as a text file unless symlinks are enabled.

## Limitations

- If `AGENTS.md` already exists, the skill stops and asks whether to rewrite it.
- It does not port skills, agents, MCP servers, or hooks from Claude Code to Codex. Use `port-to-agents` for that.
