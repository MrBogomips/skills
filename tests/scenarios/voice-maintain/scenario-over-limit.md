# Scenario: Promotion over the 50-rule limit

## Invocation
Run the recap.

## Expected Behavior
- The "rollback" promotion would make `topics/software-engineering.md` hold 51 rules
- The same recap proposes a merge or removal that keeps the file at 50, linked to the promotion

## Acceptance Criteria
- [ ] The promotion item and a linked MERGE or REMOVE item appear in the same recap
- [ ] Approving the promotion alone does not leave 51 rules: the skill skips it and says why, or asks for the linked item
- [ ] Approving both leaves exactly 50 rules (`grep -c '^- ' topics/software-engineering.md`)
- [ ] No rule is removed that the author did not name
