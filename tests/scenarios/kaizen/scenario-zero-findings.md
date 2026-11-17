# Scenario: Clean session, hook offer, unattended runs

## Case 1: clean session
Setup: fresh fixture; turn 1 is "Print the contents of src/hello.sh."
Invocation: turn 2 `/kaizen`.
- [ ] Replies in one line that there is nothing to review; no recap, no reviewer dispatch
- [ ] The fingerprint diff is empty

## Case 2: no automatic start
Setup: fresh fixture; run turn 1 from the README and do not send `/kaizen`.
- [ ] No Skill call to `kaizen` appears in the session (check the transcript)
- [ ] At most one kaizen offer appears in the whole session, as a single line at the end of a reply

## Case 3: hook offer
Setup: fresh fixture; turn 1 from the README, then two more turns that each run `make test`.
- [ ] Once the transcript holds 3 tool errors, the next reply ends with one line offering `/kaizen`
- [ ] Later turns show no further offer
- [ ] Repeat with `KAIZEN_STOP_HOOK=0 claude …`: no offer appears

## Case 4: unattended run
Run turn 1 headless:
`cd "$F/repo" && claude -p --plugin-dir <repo>/kaizen --plugin-dir "$F/fixture-tools" "<turn 1 task>; then run make test twice more"`
- [ ] The final result is the answer to the task; it contains no kaizen offer and no extra turn
