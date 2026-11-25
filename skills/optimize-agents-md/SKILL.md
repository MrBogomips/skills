---
name: optimize-agents-md
description: >-
  Slims down and restructures a project's agent instruction files (AGENTS.md, CLAUDE.md, nested ones,
  .claude/rules) without changing what they tell agents: removes history, resolves conflicts with the project's
  skills, and moves detail that only some folders or tasks need into files that load on demand. Use when the user
  asks to optimize, slim, shrink, clean up, restructure, split or modularize CLAUDE.md or AGENTS.md, or says the
  instruction file is too long. Not for creating a first AGENTS.md (init-agents-md) or porting a Claude Code setup
  to Codex (port-to-agents).
license: MIT
compatibility: >-
  Any agent harness with a shell and file access. scripts/inventory.sh needs bash and standard BSD/GNU tools; git is
  used when present.
---

# Optimize AGENTS.md / CLAUDE.md

Make the instruction files cost less context on every run and tell agents the same things, or better ones the
user approves. "Instruction file" means `AGENTS.md` and `CLAUDE.md` alike. Every change is proposed as a diff the
user approves; apply none silently.

## Invocation

```text
optimize-agents-md [--check] [--threshold N] [path]
```

- `--check`: report and proposals only, change nothing.
- `--threshold N`: minimum size in lines of a block worth moving out of the root file (default 20).
- `path`: the project root (default: the git root, or the current folder without git).

## Workflow

1. **Inventory.** Run `bash scripts/inventory.sh <root>` (path relative to this skill's folder). It prints the
   layout (`symlink`, `pair-drifted`, `import`, `claude-only`, …), harness signals, every instruction file, rules,
   imports, nested files, skills, and the lines and bytes each harness loads at start: the "before" numbers. Then
   read every instruction file and every skill it lists. With `pair-drifted`, classify the union of both files.
2. **Instruction layer.** Decide which harnesses matter from `signals` (codex, gemini, cursor, copilot, or an
   `AGENTS.md` next to `CLAUDE.md`). If the signals and the user's words disagree, or the user is unsure, this is
   the first question; until it is answered, project the case the signals indicate and give the other in one line.
   - Layout `symlink`: the layer is done; say so.
   - Several harnesses and any other layout: the target is one real `AGENTS.md`, `CLAUDE.md` a relative symlink
     to it, Claude Code-only lines in `.claude/CLAUDE.md`. Recommend the `port-to-agents` skill to get there; if it
     is not installed, give `npx skills add MrBogomips/skills --skill port-to-agents`. Do not redo its work here
     (that includes sharing `.claude/skills/` with other agents): classify the content as it will be after the
     merge. If the user declines, list the drift, ask which side is
     right, and treat `AGENTS.md` as primary, warning that the copies will keep drifting.
   - Only Claude Code: optimize `CLAUDE.md` where it is.
   - Never propose `CLAUDE.md` = `@AGENTS.md`, and never split with `@import`: see "Red flags".
3. **Classify every block** with `references/content-rules.md`. Move a block only if it is needed for some
   folders or tasks **and**, after its safety rules are taken out (they stay in the root file), it still reaches
   the threshold. If the root file is already small and nothing qualifies, say that it is already lean and
   report only drift, stale lines and conflicts: never invent structural changes.
4. **Choose destinations** with `references/split-patterns.md`; why each one saves context, per harness:
   `references/loading-and-limits.md`.
5. **Report**, in one message, in this order:
   1. **Questions**, most important first: which harnesses (if open), conflicts (which side is right, where the
      merged text lives), each new nested file or skill, stale references grouped in one question (fix or delete),
      where documents go if the project records no location. Recommend an option only when it clearly dominates;
      otherwise list the options neutrally.
   2. **Before and after**: lines and bytes loaded at start per harness, and the 200-line / 32 KiB targets. Before
      comes from the inventory; after is measured on drafts written outside the project (scratch folder) and
      labelled as a projection.
   3. **Changes**, numbered: change 0 is the instruction-layer change, if any; then one per block with its
      verdict, destination and diff. A verbatim move shows the line range and destination instead of the full
      text. A change that depends on an answer is marked "pending Qn".
   4. **History**: one note, once, if history is removed (`references/content-rules.md`).
   5. **What stays in the root file and why.**

   With `--check`, stop here.
6. **Apply** only the approved changes. Edit the target of a symlink, never through it. Revise the instruction
   files in place: they must keep their names to load, and git keeps the previous version. Without git, keep a
   copy of each file before editing it.
7. **Verify.**
   - No line lost: `cat <every new or changed file> > <scratch>/new.md`, then for each old file
     `grep -vxF -f <scratch>/new.md <old copy>` and read what it prints; each line must have been moved, reworded
     or deleted with approval.
   - Every path the new files name exists; every command is declared (scripts in the package manifest, Makefile
     targets, workflows) or confirmed by the user.
   - Re-run `bash scripts/inventory.sh`: the "after" numbers match the projection, no new `warn:` line.
   - Classify the new files again as in step 3: nothing new to propose.

## Red flags

| Thought | Instead |
|---|---|
| "`CLAUDE.md` with `@AGENTS.md` keeps one source" | A symlink does it in every launch folder; an import is external from a subfolder, skipped by headless runs, and Codex ignores `@`. |
| "Split the long file into `@docs/x.md` imports" | Imports load at start: zero context saved. Use nested files, pointers or skills. |
| "This 6-line block is only about `api/`, move it too" | Under the threshold a pointer costs almost as much as the block. Keep it. |
| "The skill and the file disagree, the skill looks newer" | Ask. Never pick a side silently. |
| "Merge these rules into fewer lines while moving them" | Rewording is a separate change with its own diff, and the no-loss check covers it. |
| "Codex will find `web/AGENTS.md`" | Only when launched in `web/`. Add a root pointer. |
| "Save the revision as `CLAUDE-1.1.0.md`" | Only the exact names load. Edit in place; git keeps history. |
| "Delete the history section and the reasons with it" | One-line reasons stay: without them agents undo the rule. |
| "Apply the obvious ones, ask about the rest" | Every change waits for approval. |
| "Copy every *never* of the moved block into the root file" | Only safety rules stay in the root file, and they leave the moved block: no duplicates. Style rules move with their block. |
| "Run the commands to see if they are stale" | Check declarations (manifest scripts, Makefile, workflows); never run a command with side effects to test it. |
