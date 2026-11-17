# Scenario: Project rule that proves general

## Invocation
Run the recap.

## Expected Behavior
- Sees that the project glossary rule "ambiente di test, not staging" also has global evidence from texts unrelated to the project
- Proposes moving it to the global store, to the file routing selects (`topics/software-engineering.md`), with the evidence summed

## Acceptance Criteria
- [ ] One MOVE item names the source (project › glossary.md), the destination and the combined evidence
- [ ] After approval: the rule is in the global topic file, gone from the project glossary, and the global observation is removed
- [ ] "Sportello" stays in the project glossary
- [ ] The move interacts correctly with the 50-rule limit of the topic file
