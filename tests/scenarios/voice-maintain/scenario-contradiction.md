# Scenario: Contradiction

## Invocation
Run the recap.

## Expected Behavior
- Presents the rule `[it] [to clients] Use "Lei"` and the observation "Use 'tu' with clients" as one CONFLICT item
- Offers: keep A, keep B, or qualify one of them by audience, topic or language

## Acceptance Criteria
- [ ] One item shows both texts side by side with their evidence
- [ ] The item is not applied by a bare number: "N" alone leads to a question about which prevails
- [ ] "N qualify B [to long-standing clients]" → `languages/it.md` gains the qualified "tu" rule, the "Lei" rule stays, the observation is removed
