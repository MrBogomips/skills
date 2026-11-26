# What loads when, and the size limits

Moving a line only saves context if the place it moves to loads later, or never on tasks that don't need it.
Sources: Claude Code `code.claude.com/docs/en/memory` and `/skills` (page dated 2026-11-14, newest version cited
v2.1.309); Codex AGENTS.md guide and config reference, checked on Codex 0.167.0 (2026-11-10). Re-check after a
major release of either tool.

## Claude Code

| Place | Loads |
|---|---|
| `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md` in the launch folder and every folder above it | at start |
| `@path` imports in those files (up to 4 hops) | at start, with the importing file: "they don't reduce its context cost" |
| `.claude/rules/*.md` without `paths:` | at start |
| `.claude/rules/*.md` with `paths:` | when Claude reads, writes or edits a matching file |
| `CLAUDE.md` in a subfolder | when Claude reads, writes or edits a file in that subfolder |
| A skill | its description at start; its body only when invoked or judged relevant |
| Any other file named in a pointer | only if the agent decides to read it |

- `AGENTS.md` is read only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists from the launch folder up, under a per-user setting a project cannot enforce. A `CLAUDE.md` symlink to `AGENTS.md` loads everywhere.
- An `@import` that resolves outside the launch folder is external: it waits for a per-person approval and headless runs (`claude -p`, CI) skip it silently.
- The docs (checked 2026-11-26) give three ways to share one file: `AGENTS.md` alone, a `CLAUDE.md` symlink "if you don't need Claude-specific content", and a `CLAUDE.md` with `@AGENTS.md` for Claude-specific content and for Windows, where Git checks a symlink out as a one-line text file unless `core.symlinks` is on. A symlink plus `.claude/CLAUDE.md` gives both files from every launch folder; the import is the fallback only for Windows clones without symlinks. Verify with `/context all`.
- Path-scoped rule syntax:
  ```markdown
  ---
  paths:
    - "web/**/*.tsx"
  ---
  ```
- Size: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." Files loaded on demand are also cut off past a per-file limit (40,000 characters with a 200K context window).
- The docs' own rule of thumb: "If an entry is a multi-step procedure or only matters for one part of the codebase, move it to a skill or a path-scoped rule instead."

## Codex

- Reads `AGENTS.override.md` or else `AGENTS.md` in each folder from the project root (normally the git root) **down to the launch folder**, at start. Never above the git root.
- A nested `sub/AGENTS.md` therefore reaches only sessions launched in `sub/` or below. A session launched at the root never sees it unless the root file points to it.
- No `@path` imports: an `@` line is plain text.
- No `.claude/rules/`, no `CLAUDE.md`: Codex ignores both.
- Size: at most `project_doc_max_bytes` (32 KiB by default) of all those files together; the rest is dropped.
- Follows a symlinked `AGENTS.md`.

## Other harnesses

Most agents that read `AGENTS.md` (Cursor, Copilot, Gemini CLI when configured, Antigravity) read the root file at
start; their nested-file behaviour varies. The safe portable assumptions: the root `AGENTS.md` is read, an `@`
import is not, and a plain pointer works if the agent follows it.

## Who sees which skills

| Folder | Claude Code | Codex and other `skills`-CLI agents |
|---|---|---|
| `.claude/skills/` | yes | no |
| `.agents/skills/` | no, unless `.claude/skills/<x>` links to it | yes |

A skill in only one of them is invisible to the other harnesses; any agent can still read its `SKILL.md` through a
pointer.

## What this means for a split

| Mechanism | Saves context in Claude Code | Saves context in Codex | Reliable for every agent |
|---|---|---|---|
| `@import` | no | — (not resolved) | no |
| Nested `CLAUDE.md` / `AGENTS.md` | yes | yes, but invisible from the root launch | needs a root pointer |
| `.claude/rules` with `paths:` | yes | — (ignored) | Claude Code only |
| Skill | yes | yes (skills discovered by description) | where skills are installed |
| Plain pointer ("Before X, read `docs/x.md`") | yes | yes | depends on the agent following it |
