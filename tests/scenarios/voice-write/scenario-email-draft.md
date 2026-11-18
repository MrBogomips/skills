# Scenario: Email draft applies the profile

## Setup
Fixture created. Working directory: `$F/plain` (no project store).

## Invocation
"Scrivi una mail breve ai colleghi: la versione 2.4 è in ambiente di test da oggi, il deploy è previsto venerdì."

## Expected Behavior
- Detects Italian, topic `software-engineering`, audience colleagues; no question needed
- Reads `core.md`, `languages/it.md`, `topics/software-engineering.md` and the Italian exemplar; does not read `observations.md`, `topics/family.md` or `topics/cycling.md`
- Applies the rules whose qualifiers match: `[it]`, `[to colleagues]`

## Acceptance Criteria
- [ ] The email uses "tu" forms and closes with "Un saluto e a presto"; no "Cordiali saluti"
- [ ] No opening pleasantry and no closing summary paragraph
- [ ] Uses "deploy" and "ambiente di test"; no "rilascio", no "staging"
- [ ] No sentence starts with "Inoltre"
- [ ] The rules marked `[to clients]` ("Lei", "Buona giornata") are not applied
- [ ] `observations.md` is not read; "pertanto" is not treated as a rule
- [ ] The facts are those of the request only
- [ ] The fingerprint diff is empty

## Edge Cases
- Same request in English → `languages/en.md` applies (contractions); the Italian topic entries do not, since they carry `[it]`
