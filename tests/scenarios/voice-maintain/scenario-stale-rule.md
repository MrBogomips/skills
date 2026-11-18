# Scenario: Stale rule

## Invocation
Run the recap; then reply with the other items but not this one.

## Expected Behavior
- Flags "Alternate a long sentence with two short ones…" (last reinforced 2026-02-10, more than six months before 2026-09-29) for review
- Keeps it unless the author approves removal

## Acceptance Criteria
- [ ] One REVIEW item names the rule and its last-reinforced date
- [ ] After a reply that does not name it, the rule is still in `core.md`
- [ ] "N remove" removes it; "N keep" leaves its text and evidence unchanged and adds `reviewed: 2026-09-29` (see scenario-stale-kept.md for the next runs)
- [ ] Baseline (RED) comparison: without the skill, the stale rule is not flagged
