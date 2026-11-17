# Scenario: Spoken correction

## Setup
Fixture created. Working directory: `$F/plain`. Session so far: the user asked
"Scrivi due righe ai colleghi: il server di test è di nuovo disponibile" and
Claude wrote "Ciao a tutti,\n\nil server di test è altresì di nuovo disponibile.\n\nUn saluto e a presto".

## Invocation
"Non scrivere 'altresì', non lo uso mai. Per il resto va bene."

## Expected Behavior
- Treats the statement as a spoken correction of Claude's draft
- Records one observation without asking, routed to `languages/it.md › Avoid`
- Shows the one-line notice, then gives the corrected text

## Acceptance Criteria
- [ ] `store/observations.md` gains one `###` observation about "altresì": `language: it`, source kind `spoken correction`, evidence 1
- [ ] Its `destination` is `languages/it.md › Avoid`
- [ ] No rule file changes (`core.md`, `languages/*`, `topics/*`)
- [ ] One notice line names one observation and its destination
- [ ] The user is not asked whether to record
- [ ] The corrected text drops "altresì"

## Edge Cases
- "Don't write 'inoltre', I never use it": a rule already covers it, so the observation carries `reinforces: languages/it.md › Avoid › "Inoltre" at the start`
