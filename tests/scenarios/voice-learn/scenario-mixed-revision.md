# Scenario: Mixed content and style revision

## Setup
Fixture created. Working directory: `$F/plain`. Session so far: the user asked
for an email to colleagues about the demo on Tuesday 14; Claude wrote:
"Ciao a tutti,\n\nvi scrivo per informarvi che la demo è fissata per martedì 14. Inoltre, vi chiedo di preparare le slide entro lunedì.\n\nResto a disposizione per qualsiasi chiarimento.\n\nUn saluto e a presto"

## Invocation
"Ecco quella che ho mandato: 'Ciao a tutti,\n\nla demo è fissata per mercoledì 15. E vi chiedo le slide entro lunedì.\n\nSe serve, scrivetemi.\n\nUn saluto e a presto'. Adesso preparami anche un promemoria di una riga per il calendario."

## Expected Behavior
- Skips the date change as content
- Records the style changes; the "Inoltre" change reinforces the existing rule
- Delivers the calendar reminder in the same turn

## Acceptance Criteria
- [ ] No observation mentions the date or "mercoledì 15"
- [ ] The "Inoltre" observation carries `reinforces: languages/it.md › Avoid › …`, and `languages/it.md` is unchanged
- [ ] New observations for dropping the announcing opener and replacing the stock closing offer
- [ ] One notice line; no maintenance suggestion (fewer than 10 pending, last maintenance under 30 days before 2026-09-29)
- [ ] The calendar reminder is delivered
