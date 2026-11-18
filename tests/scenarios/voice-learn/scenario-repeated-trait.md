# Scenario: Repeated trait adds evidence

## Setup
Fixture created (pending "Avoid 'pertanto'", evidence 1, source "meeting follow-up to the team"). Working directory: `$F/plain`. Session so far: Claude wrote "Ciao a tutti,\n\nla retrospettiva slitta a giovedì. Pertanto, l'invito di mercoledì è annullato.\n\nUn saluto e a presto".

## Invocation
"Togli 'pertanto', non lo uso mai. Per il resto va bene."

## Expected Behavior
- Matches the correction to the pending observation
- Adds a source line with a new text label and raises evidence from 1 to 2

## Acceptance Criteria
- [ ] `observations.md` still has exactly one "pertanto" observation
- [ ] Its `evidence` is 2 and its `sources` has two distinct text labels
- [ ] The notice says the evidence was added (for example "+1 evidence")
- [ ] Mentioning "pertanto" twice in the same text would still count once
