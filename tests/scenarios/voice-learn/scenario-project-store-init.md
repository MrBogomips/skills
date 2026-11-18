# Scenario: Project store initialization

## Setup
Fixture created, plus `$F/newproj` (git, no `.personal-voice/`). Working
directory: `$F/newproj`. Session so far: Claude wrote for the client "Hi team,
the new order screen goes live on Monday. Best".

## Invocation
"I sent 'Hi team, the new Order Desk goes live on Monday. Thanks' — 'Order Desk' is what they call it."

### Case A — default
Answer to the project-store question: "ok".

### Case B — decline
Answer: "No, lascia stare, niente cartelle nel progetto." Later in the same
session: "I changed 'The order export runs every night' to 'The Order Desk
export runs every night' — their name."

## Expected Behavior
- Records the global trait ("Thanks" to clients) first
- Before creating the project store, explains readers, history, git status noise, merge conflicts and client-name exposure, and asks personal, versioned or skip

## Acceptance Criteria
Case A:
- [ ] `.personal-voice/` exists and `.git/info/exclude` lists `.personal-voice/`
- [ ] `.gitignore` does not exist or is unchanged; `git status --porcelain` is empty
- [ ] The "Order Desk" observation is in `.personal-voice/observations.md`, not in the global store
- [ ] The notice names both destinations

Case B:
- [ ] No `.personal-voice/` folder; `.git/info/exclude` unchanged
- [ ] No "Order Desk" observation anywhere
- [ ] In the later turn, the question is not asked again

## Edge Cases
- Outside a git repository: the skill asks only whether to create the store, with no git explanation
