# skill-check scenarios

## Fixture

Create a skill folder `release-notes/` outside the repository:

- `SKILL.md` with `name: release-notes`, a description that includes the trigger phrase
  "scrivi le note di rilascio", and a step whose code block runs `scripts/collect.sh <last-tag>`;
- `scripts/collect.sh`, any one-line shell script;
- `tests/pressure.md`, any text.

Run Claude Code with the plugin loaded: `claude --plugin-dir ./skill-maker`.

## Scenarios

- [baseline.md](baseline.md): the run without the skill (rule T1), with its recorded result.
- [scenario-approval.md](scenario-approval.md): findings, approval by ID, re-check.
