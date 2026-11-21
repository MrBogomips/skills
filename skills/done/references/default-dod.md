# Generic Definition of Done

Used when the repository root has no `DoD.md`. Done criteria in the project instructions are merged in and win
on conflict. Each line is one condition of the report, in this order.

## Goals (always apply)

| Condition | Evidence |
|---|---|
| Every goal met, or dropped or deferred by the user | the file, commit or output that shows it; the user's words |
| No question waiting for the user | the conversation |
| No background task, subagent or long-running command still active | the harness's task list, or `jobs` |

Assumptions the agent made on its own go in the report's residual items.

## Quality

| Condition | Evidence |
|---|---|
| The project's verification passes | its test, lint and build commands, on the current `head_tree` |
| Critical and high review findings resolved | the review output; `pr_unresolved_threads: 0` |

## Delivery

| Condition | Evidence |
|---|---|
| Working tree clean | `modified: 0`, `untracked: 0`, apart from temporary files (fixable) |
| Nothing unpushed | `upstream` set and `ahead: 0` |
| Delivered | see the table below |
| CI green | `pr_checks: pass`, or `ci_head: pass` on the integration branch (`none` when the repository has no CI) |
| No changes requested | `pr_review` is not `CHANGES_REQUESTED` |
| Version, changelog, docs updated where the project requires it | the project instructions, then the diff |

| Where the work is | Delivered when | Closable |
|---|---|---|
| Topic branch, remote | pull request open (not draft, `pr_head_matches: yes`) or merged | once merged |
| Integration branch, remote | pushed, `ci_head` not `fail` | yes |
| No remote | committed; say that nothing was pushed | yes |

## Hygiene

| Condition | Evidence | Fixable |
|---|---|---|
| No draft or temporary file left | `untracked`, plus what the session wrote outside the repository | yes |
| No debug leftovers | each `debug_markers` line judged | no |
| No stash or worktree of the session left | `stashes`, `extra_worktrees`, the conversation | no: ask |
| Merged topic branch deleted | `merged_branches` does not list it | yes |
| Local integration branch aligned | `integration_behind: 0` | yes |

## Outside git

Only the goals and "no draft or temporary file left" apply.
