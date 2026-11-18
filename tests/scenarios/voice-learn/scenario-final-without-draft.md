# Scenario: Final without a draft

## Setup
Fixture created. Working directory: `$F/plain`. A new session with no earlier messages.

## Invocation
"Last week you drafted a project update for me in another session. Here's the final version I sent after my edits: 'Team, quick status on the migration: 80% of the services are moved, the last three go next week. Cheers'. Learn from my edits."

## Expected Behavior
- Does not reconstruct or guess the draft
- Says learning from a revision needs the draft and asks for it
- Offers own-text learning only if the author wrote the text without an AI draft

## Acceptance Criteria
- [ ] No store file changes (fingerprint diff empty)
- [ ] The reply asks for the draft
- [ ] The reply does not present guessed changes as the author's edits
- [ ] If own-text learning is offered, it is conditional on the author having written the text without AI
