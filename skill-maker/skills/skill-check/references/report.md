# Report format

Write the report in the user's language. Leave out a section with nothing in it.

```markdown
## Recommended tools

skill-maker works without these, but you get more with them:

- **<tool>**: <what skill-maker hands off to it>. Without it: <what is lost>. Install: `<command>`

## Findings · <target> · <n> errors, <n> warnings, <n> suggestions

| ID | Rule | Severity | Where | Problem | Proposed fix |
|---|---|---|---|---|---|
| F1 | P6 | error | `release-notes/tests/` | Test material ships with the skill | Move it to the repository's test folder |

Review: independent (rulebook-reviewer) | by the same agent (no subagent tool)

## Next steps

- <evals, trigger tuning, README findings for skill-readme, suggestions outside the rules>

Which findings should I apply? Answer with IDs (for example `F1 F3`) or `all`.
```

Severity: `error` breaks a rule that the validator enforces or that makes the skill fail; `warning` breaks
a rule; `suggestion` improves the skill without a rule requiring it.
