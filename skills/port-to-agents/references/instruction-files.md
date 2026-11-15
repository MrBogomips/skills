# How Claude Code and Codex find the instruction files

Verified on Claude Code 2.1.321 and Codex 0.167.0 (2026-11-10) with codewords in throwaway repositories, and against the docs: Claude Code `code.claude.com/docs/en/memory` and CHANGELOG; Codex AGENTS.md guide and config reference. Re-check after a major release of either tool.

## Claude Code

- **Since 2.1.277** it can read `AGENTS.md` (CHANGELOG: "in a project with no CLAUDE.md, Claude Code reads AGENTS.md instead").
- **Setting "Project instructions"** (`/config`; in settings `pluginConfigs."cc-plugin-agents-md@builtin".options.instructionFiles`, older id `agents-md@builtin`): `claude-md-or-agents-md` (default), `claude-md-and-agents-md`, `claude-md`, `managed-only`. It is honoured in user, `--settings` and managed settings and ignored in project and local settings: **a project cannot choose it**.
- **Default rule:** `AGENTS.md` is read only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the working directory or in any directory above it, also above the git root. `~/.claude/CLAUDE.md` does not count. Then every `AGENTS.md` from the working directory up loads at start, and subdirectory ones load on demand. One `CLAUDE.md` anywhere in that chain switches all of them off, silently.
- **External imports:** an `@path` import is external when it resolves outside the working directory, the folder the session started in. The first time, an interactive session asks for approval once per project; declined, the imports stay off, and no way to turn them back on is documented. A headless run (`claude -p`, SDK, CI) shows no dialog and skips them. So the `@AGENTS.md` of a `CLAUDE.md` above the launch folder (a repository root seen from a subfolder, a workspace seen from a nested repository) is external.
- **Symlinks:** Claude Code reads a `CLAUDE.md` that is a link, from any launch folder, with no approval. Edit and Write refuse to write through a link and point to its target. Git on Windows checks symlinks out as plain text files unless `core.symlinks` is on.

| Test | Loaded |
|---|---|
| only `AGENTS.md` | `AGENTS.md` |
| `CLAUDE.md` and `AGENTS.md` in the same folder | `CLAUDE.md` only (both with `claude-md-and-agents-md`) |
| `CLAUDE.md` at the root, `AGENTS.md` in the working subfolder | `CLAUDE.md` only |
| `CLAUDE.md` in a parent folder, `AGENTS.md` in the repository | `CLAUDE.md` only |
| `AGENTS.md` at the root and in the working subfolder, or above the git root, no `CLAUDE.md` | all of them |
| `CLAUDE.md` with `@AGENTS.md`, session in the same folder | `AGENTS.md` through the import, once under every setting |
| `CLAUDE.md` with `@AGENTS.md`, session in a subfolder or a nested repository, headless | `CLAUDE.md` only: the import is external and skipped |
| `CLAUDE.md` → `AGENTS.md` symlink, session in the same folder, a subfolder or a nested repository | `AGENTS.md` through the link |
| `CLAUDE.md` → `AGENTS.md` symlink and `.claude/CLAUDE.md` in the same folder, from there or a nested repository | both |

## Codex

- Reads `AGENTS.md` (`AGENTS.override.md` first) in each directory from the project root, normally the git root, down to the working directory. It never reads above the git root: a workspace's `AGENTS.md` does not reach sessions inside the repositories it contains.
- Follows a symlinked `AGENTS.md`.
- Reads at most `project_doc_max_bytes` (32 KiB by default) of these files in all.
- `project_doc_fallback_filenames` names other files to read when `AGENTS.md` is missing. It is a per-user setting; whether a project's `.codex/config.toml` can set it is not documented.
- Resolves no `@path` import.

## Why `CLAUDE.md` is a symlink to `AGENTS.md`

| Option | Verdict |
|---|---|
| `AGENTS.md` only, read by Claude Code's fallback | Rejected. Needs 2.1.277 or later and the default setting on every machine, which a project cannot enforce; a personal `CLAUDE.local.md` or a `CLAUDE.md` in a parent folder turns the team rules off without a word. |
| `CLAUDE.md` with `@AGENTS.md` | Rejected. Seen from a subfolder or a nested repository the import is external: it waits for a per-person, per-folder approval, stays off if declined, and headless runs skip it, silently. |
| `AGENTS.md` generated from `CLAUDE.md` | Rejected. A copy that drifts after every edit unless it is regenerated. |
| `CLAUDE.md` → `AGENTS.md` symlink, Claude Code's own lines in `.claude/CLAUDE.md` | **Chosen.** One real file, read by Claude Code from every launch folder, under every setting and version, headless included, and by Codex directly. Cost: Windows checkouts need `core.symlinks` (Developer Mode); without it `CLAUDE.md` arrives as a text file holding `AGENTS.md`, and the block reports it. |
