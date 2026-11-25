# Scenario: one verdict per skill, read-only

## Steps

1. `/skill-maker:skill-audit .`

## Acceptance criteria

- Every skill of every plugin in the snapshot appears exactly once, with a verdict (keep, improve,
  merge or retire) and a reason that stands on its own.
- Top findings cite rule IDs and `path:line`.
- Overlapping skills are named as merge candidates, or kept apart with the line that separates them.
- The report is saved outside the snapshot's skill folders and its path is given.
- `git status` in the snapshot is clean afterwards.

## Last run (2026-11-25)

Headless, on a snapshot of the branch. Passed: 20 skills, keep 6, improve 12, merge 2, retire 0, in two
reviewer batches; `git status` clean. The run found two defects in skill-audit itself (the reviewer
dispatch omitted `official-references.md`; "as in skill-check" pointed to text the skill never loads),
both fixed, and Italian examples in personal-voice and `pause` that the validator's heuristic missed
because they sit in code blocks or single words, fixed in the same pull request.
