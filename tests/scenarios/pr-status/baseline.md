# pr-status baseline — 2026-11-27

**Value gate: go, as a shortcut skill with a script** (DESIGN.md, Shortcut skills). A short request does not give the fixed list. The baseline got every state right, so the script does not rest on a baseline failure: it exists because the list must come out the same on every run (skill-maker rule S7) and the rules proved easy to get wrong while writing it (bot reviews counted as reviews, earlier runs of a re-run check kept). Human-invoked only (`disable-model-invocation: true`); scope: work on two or more pull requests at once.

Run: a fresh agent on the session model, no skill, one request: "Show me the status of these PRs in cli/cli: #14196 #13013 #15180 #13899 #13400 #14455". Ground truth read with `gh pr view` right after.

| Check (skill standard) | Run |
|---|---|
| State read from GitHub at that moment | ✓ one `gh pr view` per pull request |
| Fixed list: one line each, status emoji, full URL as plain text | ✗ an eight-column table, no emoji, no URL |
| One state per pull request, by a fixed precedence | ✗ raw fields side by side, the reader works out the state |
| "Not reviewed yet" only when no person reviewed | ✓ #13400 reported as "no review yet": its 4 reviews are 3 replies by the author and 1 by a bot. Inferred from `reviewDecision`, which does not say it |
| Merge state in words | ✗ `BLOCKED` on a closed pull request, `UNKNOWN (merged)` on a merged one |
| Conflicts, failed check, changes requested, draft, merged | ✓ |

Failures: the fixed format is not produced (1/1); raw merge states are passed on (1/1). No state was wrong.

Not exercised: a merge state still `UNKNOWN` right after a push, a failed check that is not required (`UNSTABLE`), a re-run check, and a pull request reviewed only by a bot and not otherwise blocked. All are covered by the script's unit tests (`tests/test_pr_status.py`), not by a live run.

One run on one model: repeat with a second model before changing the skill's scope.
