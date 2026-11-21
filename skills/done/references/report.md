# Report

Always this format, in the conversation's language. The markers and outcomes below never change.

```text
<VERDICT>[ (--check)]

<Conditions heading>
<mark> <condition> (<source>) — <evidence>[ → <next action>]
...

<Actions heading>
<action>: <OUTCOME>[ — <details>]
...

[<Residual heading>
- <item>]

[<one question collecting every yes still needed>]
```

- **Verdict**: `NOT DONE`, `DONE` or `DONE, closable`.
- **Conditions**: every condition, one line each, in this order: goals; the `Requirements` of each governing
  `DoD.md` (most specific file first, in file order); then the generic quality, delivery and hygiene
  conditions that are not replaced. Source: `session`, the `DoD.md` path, `instructions` or `default`.
  A group of sub-items is one line per sub-item, prefixed with the group's trigger or scope; a group whose
  trigger does not hold is a single ➖ line. An item that still bundles several conditions is reported as
  failed or not verifiable when any of them is.
  Marks:
  - ✅ passed
  - ❌ failed: add `→` the next action
  - ⚠️ not verifiable: add why and `→` how to make it verifiable
  - ➖ not applicable, or not evaluated because the gate stopped the run
- **Actions**: every treatment of `on-done.md`, in its order, one line each. Outcomes:
  - `OK` done
  - `FAILED` tried and failed: the error
  - `SKIPPED` not needed or not allowed: why
  - `DECLINED` the user said no
  - `PENDING` waiting for the user or for the next message (questions below, session title)
  - `WOULD RUN` only with `--check`

  When the gate stopped the run, a single line: `None: the gate stopped the treatments (<n> failed)`.
  `--finish` steps are summarized on the branch-closing line.
- **Residual**: only when there is some (deferred goals, undelivered commits, assumptions made).
- **Question**: at most one, at the end, grouping every confirmation (files to delete, other branches,
  `DoD.md` offer after a run with `dod_files: 0`, handoff). Nothing else is asked after the verdict.
- When the title is set by printing a command, that command is the very last line.

## Example

```text
DONE, closable

Conditions
✅ Goal: simplify the done skill (session) — PR #23
✅ Bundled-script tests pass (DoD.md) — `python3 -m unittest …` exit 0
✅ Pull request merged, CI green (DoD.md) — #23 MERGED, pr_head_matches: yes, checks: pass
✅ No unresolved review thread (default) — pr_unresolved_threads: 0
✅ No debug leftovers (default) — 3 markers, all test fixtures
✅ Working tree clean (default) — modified: 0, untracked: 0

Actions
Temporary files: SKIPPED — none
Merge pull request: SKIPPED — already merged
Close branch feature/x: OK — main pulled, local -D (via=pr), remote deleted
Other merged branches: PENDING — feature/old: asked below
Project commands: OK — scripts/sync.sh exit 0
Session title: PENDING — DONE-ACME-API-Fixing-Login, applied at your next message
Handoff: SKIPPED — no residual work

Delete the merged branch feature/old, which is not from this session? (yes/no)
```
