# Scenario: A session-end phrase starts the wrap-up

## Setup
Fixture created. The voice-write skill was used earlier in the session.

## Invocation
In separate sessions: "Ok, per oggi chiudiamo qui, grazie." / "That's all for today." / "On s'arrête là pour aujourd'hui."

## Expected Behavior
- Recognizes the end of the work session in any language
- Invokes `personal-voice:voice-learn` for the session wrap-up

## Acceptance Criteria
- [ ] Each phrase leads to `personal-voice:voice-learn` being invoked for the wrap-up
- [ ] A phrase that ends only one task ("ok, this email is done, next") does not start the wrap-up
- [ ] Nothing is written by the voice-write skill itself
