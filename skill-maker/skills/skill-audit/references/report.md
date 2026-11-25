# Report format

Write the report in the user's language. Leave out a section with nothing in it.

```markdown
# Skill audit · <folder> · <date>

<n> skills · keep <n> · improve <n> · merge <n> · retire <n>

## Recommended tools

- **<tool>**: <what skill-maker hands off to it>. Without it: <what is lost>. Install: `<command>`

## Verdicts

| Skill | Verdict | Reason | Top findings |
|---|---|---|---|
| `release-notes` | improve | Triggers in Italian and test material inside the skill | S3 `release-notes/SKILL.md:3`, P6 `release-notes/tests/` |
| `changelog` | merge with `release-notes` | Answers the same requests; `release-notes` also groups by type | S1 `changelog/SKILL.md:3` |

Review: independent (rulebook-reviewer, <n> batches) | by the same agent (no subagent tool)

## Next steps

- `skill-check <path>` for each skill marked improve.
- Merges and retirements are the owner's decision: nothing was changed.
```

A reason stands on its own: "superseded" alone is not a reason, "superseded by X, which also covers Y"
is.
