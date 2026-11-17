# Scenario: Uncertain topic asks one question

## Setup
Fixture created. Working directory: `$F/plain`.

## Invocation
"Scrivi un messaggio breve per il gruppo sulla sessione di sabato: si parte alle 8 dal solito posto."

## Expected Behavior
- "Group" and "session" fit more than one topic (a cycling outing, a work session)
- Asks one short question naming the candidate topics, and waits
- After the answer "è l'uscita in bici", writes with `topics/cycling.md`

## Acceptance Criteria
- [ ] The first reply is one short question (one or two sentences) naming two or three candidates, with no draft
- [ ] No rule text or personal detail from the store (for example the family nickname) appears in the question
- [ ] After the answer, the message calls the ride an "uscita", not a "giro"
- [ ] If the answer names a topic with no file (for example "il coro"), the skill writes with core and language rules only and does not ask again

## Edge Cases
- Request that settles the topic ("per il gruppo bici") → no question
