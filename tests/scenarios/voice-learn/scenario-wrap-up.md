# Scenario: Session wrap-up

## Setup
Fixture created. Add observations until `store/observations.md` holds 10
pending. Working directory: `$F/plain`. Load both the voice-write and the voice-learn skill.
Session so far:
- Claude wrote an email; the author pasted a revision; learn recorded 4
  observations and showed the notice.
- Claude wrote `q3-summary.md` (content as in scenario-edited-file.md); the
  author later edited it on disk and did not mention it.

## Invocation
"Ok, that's all for today. Thanks!"

### Case — plugin not used
Same phrase in a session where no personal-voice skill was used.

## Expected Behavior
- Re-reads `q3-summary.md`, finds the edit, and records it before the recap
- Recap of at most two lines: observations recorded in the session, total pending
- Pending is 10 or more, so asks whether to run maintenance now

## Acceptance Criteria
- [ ] Observations from the `q3-summary.md` edit are recorded before the recap
- [ ] The recap is at most two lines and reports both numbers
- [ ] The reply asks whether to run maintenance now, and does not run it unasked
- [ ] Plugin not used: nothing is said about the voice profile and nothing is written
