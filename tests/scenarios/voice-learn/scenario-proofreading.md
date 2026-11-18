# Scenario: Proofreading the author's text

## Setup
Fixture created. Working directory: `$F/plain`. Load both the voice-write and the voice-learn skill.

## Invocation
Turn 1: "Correggimi questa mail che ho scritto per un cliente: 'Gentile dott. Rossi,\n\nle confermo che il documento e' pronto, glielo mando entro domani mattina.\n\nBuona giornata'"
Turn 2: "Perfetta, grazie. La mando così."

## Expected Behavior
- Corrects the email
- Treats Claude's corrections as Claude's, not the author's preferences
- Records nothing

## Acceptance Criteria
- [ ] No store file changes (fingerprint diff empty)
- [ ] No notice line
- [ ] `personal-voice:voice-learn` is not invoked on Claude's own corrections

## Edge Cases
- The author rejects one correction ("no, lascia 'glielo mando', è come scrivo io"): that rejection is a spoken correction and may be recorded
