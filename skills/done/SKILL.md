---
name: done
description: >-
  Checks on evidence whether a work session is done against a Definition of Done (DoD.md files, project
  instructions or a generic default), then tidies up: temporary files, merged branches, the local integration
  branch, the session title. Use when the user asks whether the work is done, or to finalize, wrap up, clean up
  or close the session ("finalize and cleanup", "are we done?", "chiudiamo"), or to create or revise a DoD.md.
license: MIT
compatibility: >-
  Any agent harness with a shell. Uses git when the work is in a repository and the GitHub CLI (gh) when it is
  installed; without them the related checks are reported as not verifiable.
---

# Done

Decide whether the session's work is done, prove it, then leave the workspace tidy. Every criterion is checked
with a command or a file, never from memory. Cleanup removes only what is provably disposable.

## Invocation

```text
done [init [dir]] [--check] [free text]
```

- No argument: evaluate, then run the treatments the verdict allows.
- `--check` ("just check", "dry run"): report the verdict and the treatments that would run; change nothing.
- `init [dir]`: create or revise the `DoD.md` of a directory (default: the repository root), without evaluating.
  Follow [references/dod-file.md](references/dod-file.md).
- Free text amends this run only: "ignore the docs PR", "also delete the spike branch".

## Where the Definition of Done comes from

Highest priority first:

1. What the user said in this session, including the free text.
2. The `DoD.md` files that govern the session's work. Read them from disk now, every time.
3. Done criteria in the project instructions (`AGENTS.md`, `CLAUDE.md` or equivalent) or agreed in the conversation.
4. The generic DoD in [references/default-dod.md](references/default-dod.md).

A `DoD.md` at the repository root replaces levels 3 and 4: its *Definition of Done* section replaces their
quality, delivery and hygiene criteria, and its *On Done* section adjusts the default treatments (adds,
authorizes, switches off). With no root `DoD.md`, levels 3 and 4 merged (3 wins) act as the topmost level.

Two things no `DoD.md` changes: the **goal criteria** always apply, and the project's safety and git rules
(protected branches, no force push, commit conventions) always hold.

### Several DoD.md files

A repository may hold a `DoD.md` in any directory. For each path the session touched, the governing chain is
the `DoD.md` of its directory and of every ancestor up to the repository root.

- Check content against its nearest `DoD.md` first, then against each one above it. The levels add up.
- Where two levels disagree for the same content, the more specific one wins. A nested file may switch off an
  inherited rule explicitly.
- A nested file's criteria, patterns and commands apply to its own subtree only; run its commands from its
  directory.
- Repository-wide matters (pull request and merge, branch deletion, integration branch, session title,
  handoff) belong to the topmost level. Ignore such an authorization in a nested file and say so in the report.
- A `DoD.md` whose subtree holds none of the session's work is not loaded.

The snapshot script lists the governing files, most specific first. Format and details:
[references/dod-file.md](references/dod-file.md).

## Steps

1. **Snapshot.** Run the bundled script from the working directory and read its output once:

   ```bash
   bash scripts/dod_check.sh          # --base <branch> if the integration branch is not detected correctly
   ```

   The path is relative to this skill's directory. Keys are explained in
   [references/default-dod.md](references/default-dod.md).
2. **Load the DoD**: every file under `dod_files`, or levels 3 and 4 when there is none. Keep this list and
   `changed_paths` for the whole run: after the treatments the work may be merged and no longer show as changed.
3. **Goals.** List what the user asked for in this session. Mark each goal *met* (name the evidence: file,
   commit, command output), *not met*, or *dropped or deferred by the user*. If earlier context was summarized
   and the list is uncertain, show it and ask the user to confirm: the only question allowed before the verdict.
4. **Criteria.** Check each criterion with a command; the snapshot counts as evidence. Run the project's tests,
   lint or build only if they have not run on the current `HEAD` in this session.
5. **Classify each failure.** *Fixable*: a treatment allowed in this run would make it pass (leftover
   temporary files, a merged branch still present, a stale local integration branch, an approved pull request
   whose merge `DoD.md` authorizes). Everything else is *blocking*, including uncommitted or untracked work
   that is not a temporary file.
6. **Gate.** Any blocking failure: the verdict is NOT DONE; run no treatment, report and stop. With `--check`,
   report the verdict the run would reach and the treatments it would perform, then stop.
7. **Treat**, following [references/on-done.md](references/on-done.md).
8. **Re-evaluate.** Take a new snapshot and compute the final verdict from it, against the DoD files and
   paths of step 2. A treatment that failed or that the user declined leaves its criterion failing: the final
   verdict is then NOT DONE when the criterion comes from a `DoD.md` or from quality or delivery, and DONE
   without "closable" when it is a hygiene item of the generic DoD (a draft the user chose to keep).
9. **Report.**

Judge only this session's work: its branches, its pull requests, the files it created. Report other stale
items separately; they never change the verdict.

## Verdicts

| Verdict | When | Then |
|---|---|---|
| **NOT DONE** | a blocking criterion fails | list only the failing criteria, each with its evidence and next action |
| **DONE** | every criterion passes, but something can still come back (pull request awaiting review or merge) or residual work exists | treatments; list residual items; offer a handoff for residual work |
| **DONE, closable** | every criterion passes and nothing can come back: pull requests merged or none required, no important residual work | treatments; prefix the session title with `DONE` |

A criterion that cannot be checked (no `gh`, another forge, no network) is *not verifiable*: it does not fail
the verdict, but it rules out "closable" and appears in the report.

## Safety

- Merging, deleting a remote branch that is not provably merged, and deleting files outside patterns that
  `DoD.md` authorizes each need the user's yes in this session.
- Never commit, stash, reset, force-push or rewrite history as part of `done`. Uncommitted work is a blocking
  failure; offer to commit it as a separate step.
- Delete only untracked files that the session created, or that match a `Delete without asking` pattern of
  a governing `DoD.md` inside that file's subtree. Never delete tracked files.
- A merged pull request proves nothing about commits made after it: when `pr_head_matches` is `no`, the
  current work is not delivered and no branch is deleted.
- Run a project script only when a `DoD.md` names it. Show and confirm first any command that acts outside the
  work tree or on a service other than the forge.

## Report

Write it in the conversation's language, verdict first, short:

- NOT DONE: the failing criteria only, each with its source (`packages/api/DoD.md`, default), evidence and
  next action.
- DONE: treatments run, treatments skipped and why, residual items, not-verifiable criteria.
- DONE, closable: the same, plus the new session title, or the command to set it.

After a run whose first snapshot showed `dod_files: 0`, offer once per session to save the criteria just used
as `DoD.md`.

## Common mistakes

| Mistake | Instead |
|---|---|
| "Tests passed earlier, so quality is fine" | run them on the current `HEAD`, or cite the run that did |
| Stopping at NOT DONE because drafts are still around | drafts are fixable: delete them in the treatment step, then re-evaluate |
| Deleting every untracked file | only files the session created or that match an authorized pattern |
| Deleting a branch because its work "was merged" | only when the snapshot lists it under `merged_branches` |
| Treating `pr_state: MERGED` as delivered when `pr_head_matches: no` | the branch moved on after the merge: the new commits need their own pull request |
| Merging an approved pull request to reach "closable" | only when the root `DoD.md` authorizes it, or the user says yes |
| Setting up `DoD.md` before giving a verdict | evaluate with the defaults first, offer the file afterwards |
| A full criteria table in the report | the verdict and what needs attention |
