# Scenario: Promotion at two pieces of evidence

## Setup
Run the recap. Note the item number N of the "pertanto" promotion.

## Invocation
"N"

## Expected Behavior
- Shows both pieces of evidence in the recap
- On approval, writes the rule and removes the observation

## Acceptance Criteria
- [ ] The recap item shows both sources (2026-09-18 and 2026-09-25) and the destination `languages/it.md › Avoid`
- [ ] After "N": `languages/it.md` › Avoid holds a `[it]` rule about "pertanto" with `evidence: 2` and `reinforced: 2026-09-25`
- [ ] The "pertanto" observation is gone from `observations.md`; the other observations are unchanged
- [ ] `last_maintenance` is `2026-09-29`
- [ ] No other rule file changes

## Edge Cases
- "N edit: [it] Never use "pertanto"." → the edited text is written
- "N scope: [to colleagues]" → the rule gets the audience qualifier
- The author asks to promote "Numbered lists" (evidence 1) → allowed on this explicit request
