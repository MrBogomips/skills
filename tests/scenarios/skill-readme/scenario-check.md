# Scenario: Check mode

## Case 1: plugin in a subfolder
Invocation: `/skill-maker:skill-readme check personal-voice`
- [ ] The inventory lists the plugin and `voice-write`, `voice-learn`, `voice-maintain`, and no skill of the root plugin or of `kaizen`
- [ ] The notes copy the lint findings of `personal-voice/README.md` with their line numbers
- [ ] The three missing skill READMEs appear as findings
- [ ] The `readme-reviewer` agent is dispatched once; its findings carry a `file:line` as evidence
- [ ] Nothing is written to disk; the `git status` diff is empty

## Case 2: one skill
Invocation: `/skill-maker:skill-readme check <eng-artifacts>/skills/erd`
- [ ] The plugin root is found by walking up; only the `erd` README is checked
- [ ] `summary:` is recognized; `Performance` is reported as a custom section, not as an error
- [ ] `git status` in the eng-artifacts checkout is unchanged

## Case 3: excluded skills
Invocation: `/skill-maker:skill-readme check <eng-artifacts>`
- [ ] Skills under `.claude/skills/` and `.agents/skills/` are listed as excluded with a reason and are not checked

## Edge cases
- [ ] A folder with no `.claude-plugin/plugin.json` above it: the skill says so and stops
- [ ] A request with no mode ("look at the README of kaizen"): the skill runs a check or asks, and never drafts
