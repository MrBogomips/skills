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

Decide whether the session's work is done, prove it, leave the workspace tidy, report in a fixed format. Every
criterion is checked with a command or a file, never from memory. Cleanup removes only what is provably
disposable. Be fast: one snapshot, batched commands, at most one question at the end.

## Invocation

```text
done [init [dir]] [--check] [free text]
```

- No argument: evaluate, then run the treatments the verdict allows.
- `--check`: report the verdict and the treatments that would run; change nothing.
- `init [dir]`: create or revise a `DoD.md`, without evaluating: follow [references/init.md](references/init.md).
- Free text amends this run only: "ignore the docs PR", "also delete the spike branch".

## The Definition of Done

Highest priority first: what the user said in this session; the `DoD.md` files the snapshot lists under
`dod_files` (read them from disk now); done criteria in the project instructions or the conversation; the
generic DoD in [references/default-dod.md](references/default-dod.md).

- A `DoD.md` at the repository root replaces the last two levels: do not load `default-dod.md` then.
- Nested `DoD.md` files add to the ones above them for their own subtree; on conflict the more specific wins.
  Pull request, merge, branch, title and handoff lines count only in the root file. Format:
  [references/dod-file.md](references/dod-file.md), loaded only when a `DoD.md` has an *On Done* section or
  there is more than one.
- Always, whatever a `DoD.md` says: the session's goals, and the project's safety and git rules.

## Steps

1. **Snapshot.** `bash <skill-dir>/scripts/dod_check.sh`, where `<skill-dir>` is the directory of this file
   (never a `scripts/dod_check.sh` of the project). Add `--since <rev>` when the session committed directly on
   the integration branch, with `<rev>` the commit before the session's first one. Read the output once; keys
   are below.
2. **Goals.** List what the user asked for in this session; mark each met (with evidence), not met, or dropped
   or deferred by the user. If earlier context was summarized and the list is uncertain, ask the user to
   confirm: the only question allowed before the verdict.
3. **Criteria.** Run every `Requirements` command of the governing `DoD.md` files in **one** shell call that
   prints each command's exit status, each from its file's directory. Skip the project's tests when they
   already passed in this session on the same `head_tree`. Judge the rest from the snapshot.
4. **Classify** each failure. *Fixable*: a treatment allowed in this run makes it pass (temporary files, a
   merged branch still present, a stale local integration branch, an approved pull request whose merge the
   root `DoD.md` authorizes). Everything else is *blocking*, including uncommitted work that is not temporary.
   A pull request that is open, not draft, green, with no changes requested and `pr_head_matches: yes` is not
   a failure of a "merged" requirement: it only rules out "closable".
5. **Gate.** Any blocking failure: NOT DONE, no treatment. With `--check`: report and stop.
6. **Treat**, following [references/on-done.md](references/on-done.md). The `--finish` output is the new
   snapshot: no other re-evaluation is needed.
7. **Report**, exactly as in [references/report.md](references/report.md).

Judge only this session's work: its branches, its pull requests, the files it created. Other stale items are
listed apart and never change the verdict.

## Snapshot keys

| Key | Use |
|---|---|
| `fetch: failed`, `gh` not `ok`, `forge: unknown` | remote facts are *not verifiable*: no "closable" |
| `head_tree` | identity of the tested content: same tree, no need to rerun tests |
| `upstream`, `ahead`, `behind`, `integration_behind` | pushed? local integration branch stale? |
| `modified`, `untracked`, `stashes`, `extra_worktrees` | working tree state; stashes and worktrees may not be the session's |
| `ci_head` | on the integration branch: CI of `HEAD` (`pass`, `fail`, `pending`, `none`) |
| `pr_number` … `pr_checks`, `pr_unresolved_threads` | the current branch's latest pull request |
| `pr_head_matches` | `no`: the pull request describes an earlier state; the new commits are undelivered |
| `merged_branches` | local branches safe to delete (`via=ancestor` or `via=pr`, `remote=yes`, `current=yes`) |
| `changed_paths` | the session's work: changes since the merge base (and `--since`), plus local changes |
| `debug_markers` | added lines that look like debug leftovers: judge each, test fixtures are fine |
| `dod_files` | governing `DoD.md` files, most specific first, with how many changed paths each governs |
| `no_dod_paths`, `dod_name_conflict` | paths with no `DoD.md` above them; two spellings in one directory: ask |

## Verdicts

| Verdict | When |
|---|---|
| **NOT DONE** | a blocking criterion fails |
| **DONE** | everything passes, but something can still come back (pull request awaiting review or merge), residual work exists, or a criterion is not verifiable |
| **DONE, closable** | everything passes and nothing can come back |

A treatment that fails or that the user declines leaves its criterion failing: NOT DONE when it comes from a
`DoD.md`, quality or delivery; DONE without "closable" for a generic hygiene item.

## Safety

- Merging, deleting a remote branch that is not provably merged, and deleting files outside an authorized
  pattern each need the user's yes in this session.
- Never commit, stash, reset, force-push or rewrite history. Uncommitted work is blocking; offer to commit it
  as a separate step.
- Delete only untracked files the session created, or that match a `Delete without asking` pattern of a
  governing `DoD.md` in that file's subtree. Never tracked files.
- Delete a branch only through `--finish` or when `merged_branches` lists it. `pr_state: MERGED` with
  `pr_head_matches: no` deletes nothing.
- Run a project command only when a `DoD.md` names it; confirm first one that acts outside the work tree or on
  a service other than the forge.

## Common mistakes

| Mistake | Instead |
|---|---|
| "Tests passed earlier" | cite the run on the same `head_tree`, or run them |
| Stopping at NOT DONE for leftover drafts | drafts are fixable: delete them, then report |
| `DONE-<current title>` with the placeholder left in, or "title updated" with no confirmation | the real title; a marker or a printed command is `PENDING` |
