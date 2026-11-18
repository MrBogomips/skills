# Scenario: Review of proposed edits

## Setup
Fresh fixture and turn 1 (see README).

## Invocation
Turn 2: `/kaizen`. Inspect the tool calls of the turn (transcript or `ctrl+o`).

## Expected Behavior
1. Dispatches the reviewer once, with every A item that edits CLAUDE.md, a rule or the skill.
2. Applies the verdicts before the recap and shows one per A item.

## Acceptance Criteria
- [ ] Exactly one Agent call, whose type ends in `kaizen-reviewer`, before the recap
- [ ] Its prompt carries the checklist, the options, the target paths and the loaded instruction files
- [ ] Every A item shows `OK`, `REVISED (…)` or `DROPPED (…)`
- [ ] If a K-b option adds a line that keeps both indentation rules, it comes back REVISED or DROPPED with a `CONTRADICTS` citation of `style.md` or `CLAUDE.md`
- [ ] Options that add net instruction lines carry `⚠ growth`
- [ ] No new file appears under `repo/.claude/skills/` or `repo/.claude/agents/` after any apply

## Variant: missing skill
Turn 1 adds: "and next time remind me to bump the version". After `/kaizen`:
- [ ] A missing release or version skill, if raised, is a B item; no file is proposed or created

## Variant: skill without the plugin
Copy `kaizen/skills/kaizen/` into `$F/repo/.claude/skills/` (untracked) and start the session without
`--plugin-dir <repo>/kaizen`.
- [ ] The review runs through a general-purpose subagent told to stay read-only, with the same checklist
- [ ] The recap still shows a verdict per A item
