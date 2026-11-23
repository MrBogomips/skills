# Generic quality and delivery criteria

Used when the repository root has no `DoD.md`. Done criteria in the project instructions are merged in and win
on conflict. Each line is one condition of the report, in this order, with source `default` (or
`instructions`).

## Quality

| Condition | Evidence |
|---|---|
| The project's verification passes | its test, lint and build commands, on the current `head_tree` |
| Critical and high review findings resolved | the review output; `pr_unresolved_threads: 0` |

## Delivery

| Condition | Evidence |
|---|---|
| Nothing unpushed | `upstream` set and `ahead: 0` |
| Delivered | see the table below |
| CI green | `pr_checks: pass`, or `ci_head: pass` on the integration branch (`none` when the repository has no CI) |
| No changes requested | `pr_review` is not `CHANGES_REQUESTED` |
| Version, changelog, docs updated where the project requires it | the project instructions, then the diff |

| Where the work is | Delivered when | Closable |
|---|---|---|
| Topic branch, remote | pull request open with `pr_ready: yes`, or merged with `pr_head_matches: yes` | once merged |
| Integration branch, remote | pushed, `ci_head` not `fail` | yes |
| No remote | committed; say that nothing was pushed | yes |

Outside git neither section applies.
