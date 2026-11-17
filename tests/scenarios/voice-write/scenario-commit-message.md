# Scenario: Commit message does not apply the profile

## Setup
Fixture created. Working directory: `$F/project`.

## Invocation
"I want everything you write for me to sound like me. Write the commit message for a change that adds a /health endpoint to src/app.py returning HTTP 200."

## Expected Behavior
- Treats the commit message as out of scope: the general wish does not name this text
- Writes a plain commit message following the project's conventions

## Acceptance Criteria
- [ ] No store file is read (global or project)
- [ ] The answer does not claim the message is in the author's voice
- [ ] Baseline (RED) comparison: without the skill, an agent told about the store reads it and applies the profile to the commit message

## Edge Cases
- "Write this commit message in my voice" → the profile applies, because the author asked for it on this text
- Code comments and configuration files behave like commit messages
