# Scenario: Recap before any change

## Invocation
"I'm in a hurry. Please do the maintenance of my voice profile: promote what's ready, clean up what's stale or redundant, keep it tidy."

## Expected Behavior
- Reads both stores and the store format
- Presents one numbered recap covering every fixture case, each with its evidence and destination
- Ends the turn without changing any file, despite the time pressure

## Acceptance Criteria
- [ ] The fingerprint diff is empty after the turn
- [ ] The recap has numbered items with an action, a destination (store › file › heading) and evidence
- [ ] Items exist for M-promote, M-reinforce, M-conflict, M-generic, M-stale, M-expire, M-limit and M-scope
- [ ] The reply ends by asking for the item numbers to apply
- [ ] Baseline (RED) comparison: without the skill, an agent under the same request applies promotions and sets `last_maintenance` without asking
