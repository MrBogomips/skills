# Scenario: Edited file

## Setup
Fixture created. Working directory: `$F/plain`. In the session, Claude wrote
`q3-summary.md` for the team with:
"Hi all,\n\nThe Q3 summary is ready. It covers revenue, churn and hiring.\n\nIn addition, the appendix lists the open risks.\n\nBest regards\n"
Then overwrite the file on disk:

```bash
printf 'Hi all,\n\nThe Q3 summary is ready: revenue, churn, hiring.\n\nThe appendix lists the open risks.\n\nCheers\n' > "$F/plain/q3-summary.md"
```

## Invocation
"I edited q3-summary.md, have a look."

## Expected Behavior
- Reads the whole file from disk and compares it with the content Claude wrote
- Records the style changes as observations in the global store

## Acceptance Criteria
- [ ] Observations recorded for: dropping "In addition,", the "Cheers" closing, the list introduced by a colon
- [ ] Each has source kind `revision`, `language: en`, and before → after excerpts quoted verbatim
- [ ] The file itself is not modified
- [ ] One notice line

## Edge Cases
- The author does not say anything, and Claude Code reports the change on disk on the next turn: the voice-write skill's standing instruction starts learning; the result is the same
