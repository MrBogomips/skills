# Scenario: A stale rule the author keeps is not flagged again at the next run

## Setup
Fixture created. The M-stale rule "Alternate a long sentence with two short ones…" was last
reinforced on 2026-02-10.

## Invocation

### Run 1 — today is 2026-09-29
Run the recap; reply "N keep", where N is the M-stale REVIEW item.

### Run 2 — a new session, today is 2026-10-15
Same fixture, after Run 1. Run the recap.

### Run 3 — a new session, today is 2027-04-01
Same fixture, after Run 2. Run the recap.

## Expected Behavior
- Run 1 keeps the rule and records `reviewed: 2026-09-29` on it
- Run 2 does not flag it: the later of `reinforced` and `reviewed` (2026-09-29) is after the stale
  cutoff (2026-04-15)
- Run 3 flags it again: the stale cutoff is 2026-10-01, and 2026-09-29 is on or before it

## Acceptance Criteria
- [ ] After Run 1 the rule reads "… (evidence: 2, reinforced: 2026-02-10, reviewed: 2026-09-29)"; its text and evidence are unchanged
- [ ] Run 1's recap offered "keep" and "remove" for it, and "keep" changed nothing else in `core.md`
- [ ] Run 2's recap has no REVIEW item for that rule
- [ ] Run 3's recap has a REVIEW item for it, showing both dates
- [ ] Baseline (RED) comparison: without the skill's `reviewed` rule, Run 2 flags the rule again
