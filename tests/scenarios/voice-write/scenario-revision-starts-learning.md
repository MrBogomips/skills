# Scenario: A revision after a draft starts learning

## Setup
Fixture created. Working directory: `$F/plain`. Earlier in the session the skill drafted:
"Hi all,\n\nThe quarterly report is ready for review. It's in the shared folder. Please send comments by Friday.\n\nBest"

## Invocation
"Here's what I actually sent: 'Hi all, the quarterly report is in the shared folder — comments by Friday, please. Cheers'. Now turn it into a two-line Slack message too."

## Expected Behavior
- Recognizes the pasted text as the author's revision of a draft written in this session
- Invokes `personal-voice:voice-learn` in the same turn, without asking
- Also completes the Slack message

## Acceptance Criteria
- [ ] `personal-voice:voice-learn` is invoked (or `INVOKE: personal-voice:voice-learn` is written when following the skill) before or alongside the Slack message
- [ ] The user is not asked whether to learn
- [ ] The Slack message is delivered in the same turn
- [ ] Nothing from the revision is applied as a rule in the Slack message beyond what the store already holds

## Edge Cases
- The author edits a file Claude wrote and Claude Code reports the change on disk → same behavior
- The author says "don't write 'Best', I never use it" → same behavior (spoken correction)
