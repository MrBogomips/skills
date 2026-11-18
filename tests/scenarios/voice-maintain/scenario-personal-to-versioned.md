# Scenario: Personal to versioned

## Invocation
"I'd like to share the project glossary with the team."

## Expected Behavior
- Recognizes a git-choice switch: the store is personal (`.personal-voice/` in `.git/info/exclude`)
- Explains the implications again (readers, history, git status noise, merge conflicts, client names) and asks to confirm
- On confirmation, removes the exclusion; does not commit

## Acceptance Criteria
- [ ] Before confirmation, the fingerprint diff is empty
- [ ] The explanation covers all five points
- [ ] After "yes, version it": `.git/info/exclude` no longer lists `.personal-voice/`, and `git status --porcelain` shows `.personal-voice/` as untracked
- [ ] `.gitignore` is not created or modified; nothing is committed
