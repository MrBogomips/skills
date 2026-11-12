---
name: init-agents-md
description: >-
  Creates a short, repository-specific AGENTS.md for coding agents and makes CLAUDE.md a symlink to it, so every
  agent reads one instruction file. Use when the user asks to create, initialize or bootstrap AGENTS.md (or an
  agent instruction file) for a repository, or to turn an existing CLAUDE.md into a shared AGENTS.md.
license: MIT
compatibility: Any agent harness with a shell and file access. Symlinks need a filesystem and git setup that support them.
---

# Initialize AGENTS.md

Write a short `AGENTS.md` that holds only what an agent could not quickly work out from the repository. `AGENTS.md` is the single source; `CLAUDE.md` is a relative symlink to it.

## Workflow

1. **Check what exists**, at the repository root.
   - `AGENTS.md` exists: stop. Tell the user and ask whether to rewrite it; if they agree, treat the current file as seed material.
   - `CLAUDE.md` is a regular file: read it as seed material.
   - `CLAUDE.md` is missing or already a symlink to `AGENTS.md`: nothing to carry over.
2. **Explore the repository**, only as far as needed to describe its real shape.
   - Start from the root listing and the README.
   - Find the commands people actually run (build, test, lint, run), where the important code lives, whether tests exist, and what an agent would get wrong.
   - Read targeted files; do not dump trees.
3. **Draft `AGENTS.md`** following the content rules below, starting with `# AGENTS.md`.
4. **Link `CLAUDE.md`.**
   - If `CLAUDE.md` was a regular file, first show the user what you carried into `AGENTS.md` and what you dropped, and replace the file only after they agree. Lines that only concern Claude Code (its hooks, slash commands, tool names) go to `.claude/CLAUDE.md`, not to `AGENTS.md`.
   - Create the link from the root: `ln -s AGENTS.md CLAUDE.md` (remove the old regular file first; never use an absolute target).
   - If `git config core.symlinks` is `false`, or the project is checked out on Windows, tell the user: the link arrives there as a text file unless symlinks are enabled.
5. **Verify.**
   - `readlink CLAUDE.md` prints `AGENTS.md`.
   - Every command and path in `AGENTS.md` exists in the repository: run or list each one.
   - The file is still short. If it is not, cut again.

## Content rules

Each line costs context on every agent run, so a line stays only if it saves an agent exploration time or prevents a mistake.

- **Include**: what the repository is, in a line or two; where the important code or content lives; the exact commands for the main workflows; how to validate a change; non-obvious conventions and sharp edges.
- **Leave out**: generic coding advice, architecture history, full file trees, tool documentation, and anything the README already says unless it is agent-specific and easy to miss.
- If the repository has no meaningful tests or automation, say so plainly.
- Write terse, developer-style bullets under a few short sections.

Name sections after what the repository really has. A common shape, using only the sections that earn their place:

```md
# AGENTS.md

## Overview
## Layout
## Commands
## Validation
## Notes
```

Prefer specific names where the repository has clear topics, for example `Styling System`, `Path Aliases` or `Admin Scripts`.

To also port skills, agents, MCP servers and hooks from a Claude Code setup to Codex, use the `port-to-codex` skill instead.
