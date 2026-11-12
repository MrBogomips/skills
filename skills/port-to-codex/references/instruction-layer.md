# The instruction layer: one shared file

`AGENTS.md` holds the instructions for every agent and is the only real instruction file. `CLAUDE.md` is a symlink to it (`ln -s AGENTS.md CLAUDE.md`), and what Claude Code alone uses goes in `.claude/CLAUDE.md`, which Claude Code loads beside it. Why this form, and not a fallback, an import or a generated copy: `instruction-files.md`. Each check below is a reading no tool can do. Each finding becomes a diff the user approves.

## 1. Make `AGENTS.md` the shared file

- **Only `CLAUDE.md`:** `git mv CLAUDE.md AGENTS.md`, so the history follows the content. Move Claude Code's own lines (§3) into `.claude/CLAUDE.md`, then `ln -s AGENTS.md CLAUDE.md`.
- **`AGENTS.md` written by an earlier codex-port run** (first line `<!-- Generated from CLAUDE.md by codex-port`): it is a copy of `CLAUDE.md`. Remove it, then proceed as above. The block refuses to run while the marker is there, and never deletes `AGENTS.md`, even when an old manifest lists it.
- **Both written by hand:** merge the shared content into `AGENTS.md`, one statement per topic (versions, commands, git rules), and Claude Code's own lines into `.claude/CLAUDE.md`. Drop the framing lines ("`CLAUDE.md` imports this file", "read `CLAUDE.md` as well"). Then replace `CLAUDE.md` with the link.
- **`CLAUDE.md` imports `AGENTS.md`** (`@AGENTS.md`, an earlier form): move what else it holds into `.claude/CLAUDE.md`, then replace it with the link.
- **`.claude/CLAUDE.md` already exists:** it stays, as the Claude Code-only file; check that it holds nothing shared and does not import `AGENTS.md`.

Git stores the link as a link (mode `120000`); commit it like any file. Check that no line is lost: `cat AGENTS.md .claude/CLAUDE.md > <scratch>/new.md; grep -vxF -f <scratch>/new.md <old CLAUDE.md>`, then read what it prints; each line must have been merged or dropped on purpose.

## 2. `@path` imports

- **In `AGENTS.md`:** Codex resolves none, so `AGENTS.md` holds none. Inline a short imported file; otherwise replace the import with a plain pointer ("read `docs/x.md`") and tell the user that Codex gets only the pointer. The block fails while `AGENTS.md` has an `@` line.
- **In `.claude/CLAUDE.md`:** an import of a file only Claude Code needs can stay. Say that it is external, and skipped by headless runs, when the session starts below the folder that holds it (`instruction-files.md`).

## 3. What goes in `.claude/CLAUDE.md`, and how shared text is worded

`.claude/CLAUDE.md` keeps only lines no other agent can act on: settings read by Claude Code hooks or plugins, notes on Claude Code's own harness, model or plugins. Everything else goes to `AGENTS.md`, worded for every agent:
- **"This file guides Claude Code…"** → "the rules for every coding agent".
- **Slash commands** (`/x`) → name the step, then how each tool runs it: Claude Code `/x`, Codex the skill that does it. If none exists, give the CLI steps.
- **Harness tools** (EnterWorktree, Agent with a model, plan mode, TodoWrite) → Claude Code wording plus the plain equivalent for other agents (for example `git worktree add …`).
- **Agent model, effort, tools, preloaded skills** → say they hold for Claude Code only.

Leave product content alone: in a project whose subject is Claude Code, sentences about Claude Code as the product stay as they are.

## 4. References to the instruction files

`grep -rn 'CLAUDE.md\|AGENTS.md' AGENTS.md .claude` and the project config (for example `openspec/config.yaml`). A reference that means "the shared rules" points to `AGENTS.md`; one about Claude Code's own setup points to `.claude/CLAUDE.md`. Leave alone references about other people's projects (product text, templates, tests) and history (archives, changelogs). Tell the user that edits go to `AGENTS.md`: Claude Code refuses to write through the link and points there itself.

## 5. Nested, path-scoped and parent instructions

- **A `CLAUDE.md` in a subdirectory:** apply the same pattern there, an `AGENTS.md` with a `CLAUDE.md` link beside it. Codex reads `AGENTS.md` from the git root down to the working directory; Claude Code loads the subdirectory's `CLAUDE.md` when it reads files there.
- **`.claude/rules/`:** Codex reads none of it. Move the rules every agent needs into `AGENTS.md`, and a rule scoped to a folder into an `AGENTS.md` in that folder; keep the Claude Code-only ones.
- **Instructions above the git root** (a workspace's `CLAUDE.md`, read by sessions in the repositories it contains): Claude Code reads them through the link, Codex does not. Record it as a gap.

## 6. `CLAUDE.local.md` and local settings

They are personal and never ported: the block copies neither `CLAUDE.local.md` nor `.claude/settings.local.json`. If they hold rules the team needs, propose moving those rules into `AGENTS.md`.

## 7. Windows checkouts

On a checkout without `core.symlinks` (Windows without Developer Mode), the link arrives as a text file holding `AGENTS.md`, Claude Code reads that line instead of the rules, and its own `AGENTS.md` fallback stays off because a `CLAUDE.md` exists. The block reports this case. If the team works on Windows, record in `AGENTS.md` that `core.symlinks` must be on before cloning.

## 8. Size

Codex reads at most `project_doc_max_bytes` (32 KiB by default) of `AGENTS.md` files in all, from the root to the working directory. The block warns when the root `AGENTS.md` alone passes 32 KiB; propose moving detail into documents and leaving pointers.

## 9. Generated tooling of a framework

Tooling regenerated by a framework (for example OpenSpec's `.claude/skills/openspec-*` and `.claude/commands/opsx/`) is a source like any other skill. Record in the interop section that the Codex files are regenerated after the framework regenerates its tooling. Never hand-edit that tooling to suit Codex.
