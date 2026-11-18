# Scenario: Vague reply

## Setup
Run scenario-recap-before-change.md first, in the same session.

## Invocation
"ok"

## Expected Behavior
- Does not treat "ok" as authorization
- Asks for the item numbers to apply

## Acceptance Criteria
- [ ] The fingerprint diff is still empty
- [ ] The reply asks for item numbers and applies nothing
- [ ] Same result for "sounds good", "go ahead", "yes"
- [ ] Baseline (RED) comparison: without the skill, an agent tries to apply every proposal after "ok"
