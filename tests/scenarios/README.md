# Scenario tests

Manual checklists for the plugin skills (`kaizen`, `personal-voice`, `skill-maker`). A `baseline.md` records the value-gate outcome of a skill (`DESIGN.md`) and the run of its task without the skill (rule T1), or the desk review that stands in for it until that run is made. The automated checks
(`tests/validate.sh`, `tests/selftest.sh`, `tests/test-kaizen-stop-gate.sh`) run in CI; these
scenarios need a person or a live Claude Code session.

## Skill scenarios

One folder per skill: `kaizen/`, `voice-write/`, `voice-learn/`, `voice-maintain/`, `skill-readme/`, `skill-check/` and `skill-audit/`. Each scenario
file describes setup, invocation, expected behavior and acceptance criteria, and the folder's
`README.md` says how to build its fixture. To use one:

1. Read the scenario file.
2. Invoke the skill in Claude Code with the stated trigger, with the plugin loaded
   (`claude --plugin-dir ./<plugin>`).
3. Check the acceptance criteria.

## Integration scenarios

`integration/` holds tests that run several skills of one plugin in a row.

## Adding a scenario

- Skill scenario: `scenarios/<skill>/scenario-<name>.md`
- Integration scenario: `scenarios/integration/test-<name>.md`

When a skill's `SKILL.md` restates a rule from its `references/`, change both in the same pull
request and re-check the scenarios that cover the rule.
