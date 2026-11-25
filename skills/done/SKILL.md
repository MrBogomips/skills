---
name: done
description: >-
  Checks on evidence whether a work session is done against a Definition of Done (the repository's DoD.md,
  project instructions or a generic default), then tidies up: temporary files, merged branches, the local
  integration branch, the session title. Use when the user asks whether the work is done, or to finalize, wrap
  up, clean up or close the session ("finalize and cleanup", "are we done?", "let's close"), or to create or
  revise a DoD.md.
license: MIT
compatibility: >-
  Any agent harness with a shell. Uses git when the work is in a repository and the GitHub CLI (gh) when it is
  installed; without them the related checks are reported as not verifiable.
model: sonnet
---

# Done

Decide whether the session's work is done, prove it, leave the workspace tidy, report in a fixed format. Every
criterion is checked with a command or a file, never from memory. Cleanup removes only what is provably
disposable. Be fast: one snapshot, batched commands, at most one question at the end.

## Invocation

```text
done [init] [--check] [free text]
```

- No argument: evaluate, then run the treatments the verdict allows.
- `--check`: report the verdict and the treatments that would run; change nothing.
- `init`: create or revise the `DoD.md`, without evaluating: follow [references/init.md](references/init.md).
- Free text amends this run only: "ignore the docs PR", "also delete the spike branch".

## The Definition of Done

Three parts, evaluated and reported in this order. What the user said in this session overrides them; the
project's safety and git rules always hold.

1. **Goals**, always:

   | Condition | Evidence |
   |---|---|
   | Every goal met, or dropped or deferred by the user | the file, commit or output that shows it; the user's words |
   | No question waiting for the user | the conversation |
   | No background task, subagent or long-running command still active | the harness's task list, or `jobs` |

2. **Quality and delivery**: the `Requirements` of the `DoD.md` the snapshot names under `dod_file` (read it
   now). With `dod_file: none`: the criteria in [references/default-dod.md](references/default-dod.md), with
   the done criteria of the project instructions merged in.

3. **Hygiene**, always:

   | Condition | Evidence | Fixable |
   |---|---|---|
   | Working tree clean | `modified: 0`, `untracked: 0` | temporary files only |
   | No draft or temporary file left | `untracked`, plus what the session wrote outside the repository | yes |
   | No debug leftovers | each `debug_markers` line judged; test fixtures are fine | no |
   | No stash or worktree of the session left | `stashes`, `extra_worktrees`, the conversation | no: ask |
   | Merged topic branch deleted | `merged_branches` does not list it | yes |
   | Local integration branch aligned | `integration_behind: 0` | yes |

   Outside git only the first two apply.

Only the `DoD.md` at the repository root counts. Reading its `Requirements`:

- An item that ends with `: <command in backticks>` passes when the command exits 0, run from the repository
  root. Any other item is judged on evidence; backticks elsewhere in an item are paths and names.
- A parent item with sub-items states a trigger or a scope ("When the manual changed:"): when it does not hold,
  the whole group is not applicable.
- A section titled `## Definition of Done` (older files) is read as `Requirements`.

## Steps

1. **Snapshot.** `bash <skill-dir>/scripts/dod_check.sh`, where `<skill-dir>` is the directory of this file
   (never a `scripts/dod_check.sh` of the project). Add `--since <rev>` when the session committed directly on
   the integration branch, with `<rev>` the commit before the session's first one. Read the output once.
2. **Goals.** List what the user asked for in this session; mark each met (with evidence), not met, or dropped
   or deferred by the user. If earlier context was summarized and the list is uncertain, ask the user to
   confirm: the only question allowed before the verdict.
3. **Criteria.** Run every `Requirements` command in **one** shell call that prints each command's exit
   status. Skip the project's tests when they already passed in this session on the same `head_tree`. Judge the
   rest from the snapshot.
4. **Classify** each failure. *Fixable*: a hygiene condition marked fixable, or a pull request with
   `pr_ready: yes` and `pr_review: APPROVED` whose merge the `DoD.md` authorizes. Everything else is
   *blocking*. An open pull request with `pr_ready: yes` is not a failure of a "merged" requirement: it only
   rules out "closable".
5. **Gate.** Any blocking failure: NOT DONE, no treatment. With `--check`: report and stop.
6. **Treat**, following [references/on-done.md](references/on-done.md). The `--finish` output is the new
   snapshot: no other re-evaluation is needed.
7. **Report**, in the format below.

Judge only this session's work: its branches, its pull requests, the files it created. Other stale items are
listed apart and never change the verdict.

## Snapshot keys that need care

| Key | Meaning |
|---|---|
| `fetch: failed`, `gh` not `ok`, `forge: unknown` | remote facts are *not verifiable*: no "closable" |
| `head_tree` | identity of the tested content: same tree, no need to rerun tests |
| `ci_head` | on the integration branch: CI of `HEAD` (`pass`, `fail`, `pending`, `none`) |
| `pr_head_matches: no` | the pull request describes an earlier state; the new commits are undelivered |
| `pr_ready` | open pull request: `yes` when it is not a draft, has the current `HEAD`, checks `pass` or `none`, no changes requested and no unresolved thread; `no (<what is in the way>)` |
| `merged_branches` | local branches safe to delete (`via=ancestor` or `via=pr`, `remote=yes`, `current=yes`) |
| `changed_paths` | the session's work: changes since the merge base (and `--since`), plus local changes |
| `stashes`, `extra_worktrees` | may not be the session's |

## Verdicts

| Verdict | When |
|---|---|
| **NOT DONE** | a blocking criterion fails |
| **DONE** | everything passes, but something can still come back (pull request awaiting review or merge), residual work exists, or a criterion is not verifiable |
| **DONE, closable** | everything passes and nothing can come back |

A treatment that fails or that the user declines leaves its criterion failing: NOT DONE for a goal, quality or
delivery criterion; DONE without "closable" for a hygiene one.

## Safety

- Merging, deleting a remote branch that is not provably merged, and deleting files outside an authorized
  pattern each need the user's yes in this session.
- Never commit, stash, reset, force-push or rewrite history. Uncommitted work that is not temporary is
  blocking; offer to commit it as a separate step.
- Delete only untracked files the session created, or that match a `Delete without asking` pattern of the
  `DoD.md`. Never tracked files.
- Delete a branch only through `--finish` or when `merged_branches` lists it. `pr_state: MERGED` with
  `pr_head_matches: no` deletes nothing.
- Run a project command only when the `DoD.md` names it; confirm first one that acts outside the work tree or
  on a service other than the forge.

## Report

Always this format, in the conversation's language. The marks and outcomes never change.

```text
<VERDICT>[ (--check)]

<Conditions heading>
<mark> <condition> (<source>) — <evidence>[ → <next action>]

<Actions heading>
<action>: <OUTCOME>[ — <details>]

[<Residual heading>
- <item>]

[<one question collecting every yes still needed>]
```

- **Conditions**: every condition of the three parts, one line each, in their order (`Requirements` in file
  order). Source: `session`, `DoD.md`, `instructions` or `default`. A group of sub-items is one line per
  sub-item, prefixed with its trigger or scope; a group whose trigger does not hold is a single ➖ line.
  Marks: ✅ passed; ❌ failed, with `→` the next action; ⚠️ not verifiable, with why and `→` how to make it
  verifiable; ➖ not applicable, or not evaluated because the gate stopped the run.
- **Actions**: every treatment of `on-done.md`, in its order, one line each. Outcomes: `OK`; `FAILED` with the
  error; `SKIPPED` (not needed or not allowed) with why; `DECLINED` by the user; `PENDING` (waiting for the
  user or for the next message); `WOULD RUN` only with `--check`. When the gate stopped the run, a single
  line: `None: the gate stopped the treatments (<n> failed)`.
- **Residual**: only when there is some (deferred goals, undelivered commits, assumptions the agent made).
- **Question**: at most one, at the end, grouping every confirmation (files to delete, other branches, the
  `DoD.md` offer after a run with `dod_file: none`, handoff). Nothing else is asked after the verdict.
- A session title set by printing a command: that command is the very last line.

```text
DONE, closable

Conditions
✅ Goal: fix the login redirect (session) — PR #23
✅ Tests pass (DoD.md) — `npm test` exit 0
✅ Pull request merged into main (DoD.md) — #23 MERGED, pr_head_matches: yes
✅ Working tree clean (default) — modified: 0, untracked: 0
✅ No debug leftovers (default) — debug_markers: 0

Actions
Temporary files: SKIPPED — none
Merge pull request: SKIPPED — already merged
Close branch fix/login: OK — main pulled, local -D (via=pr), remote deleted
Other merged branches: PENDING — feature/old: asked below
Project commands: OK — scripts/sync.sh exit 0
Session title: PENDING — DONE-ACME-API-Fixing-Login, applied at your next message
Handoff: SKIPPED — no residual work

Delete the merged branch feature/old, which is not from this session? (yes/no)
```
