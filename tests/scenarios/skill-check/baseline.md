# Baseline: checking a skill without skill-check

Rule T1: the run of the task without the skill, recorded before `skill-check` was written.

## Setup

The fixture of [README.md](README.md): a `release-notes` skill with three planted problems.

1. A trigger phrase in Italian in the description.
2. A bundled script run by bare path (`scripts/collect.sh <last-tag>`).
3. A `tests/` folder inside the skill directory.

## Prompt

A fresh agent with no rulebook and no skill:

> Check this agent skill against best practices and fix what's wrong: `<fixture>`. It's going to be
> published in a public skills repository. Work only inside that folder. At the end, list what you found
> and what you changed.

## Result (2026-11-25)

The agent's report, condensed; quoted phrases are its own words.

- **Edited before asking.** Five changes were applied straight away: the trigger replaced, the script
  made executable and called with `sh`, the script rewritten "with `set -eu`, a usage message, a
  repository check and a ref check", step 1 reworded, step 3 and step 2 rewritten.
- **Went beyond a check.** It rewrote the script's behavior ("The tag is now optional: it defaults to the
  latest tag") and the workflow, none of which a review was asked to change.
- **Missed the development folder.** `tests/pressure.md` stayed inside the skill; the agent suggested
  expanding it: "it could use expected-behavior criteria".
- **No evidence.** Findings had no rule and no `path:line`; no validator was run ("I did not run the repo
  validator or other checks on the folder").
- **Found:** the Italian trigger (problem 1) and the script call (problem 2, fixed with `chmod` plus `sh`).

## What skill-check answers

| Failure | Where skill-check answers it |
|---|---|
| Edited before asking | Report first; edits only for finding IDs the user names (step 5 and its excuses table) |
| Went beyond a check | Fixes are limited to the findings; anything else is a suggestion in the report |
| Missed the development folder | The validator's P6 check runs first |
| No evidence | Rule IDs and `path:line` on every finding (T8) |
