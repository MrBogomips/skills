---
summary: Checks one skill or plugin against skill-maker's authoring rulebook and fixes only the findings you approve by ID.
---

# skill-check

Checks one skill, or every skill and agent of a plugin, against the authoring rulebook. You get a
numbered report in which each finding has its rule ID, severity, `path:line` and a proposed fix. The
skill then fixes only the findings you name and checks again.

## Why

Asked to check and fix a skill before publishing it, an agent without this skill rewrote it at once:
it changed the script's behavior, missed a test folder inside the skill and cited no evidence.
skill-check reports first, backs every finding with a rule and a line, and edits only what you approve.
A validator and an independent read-only reviewer find the problems, so the agent that fixes is not the
only one judging.

## Usage

```text
/skill-maker:skill-check <skill or plugin folder> [--custom]
```

- A folder with `SKILL.md` is one skill, inside a plugin or on its own. A folder with
  `.claude-plugin/plugin.json` is a whole plugin.
- `--custom` marks skills that are never published, which skips the English check. Without it, the
  skill reads your project's instruction files to tell, and asks when they don't say.
- Answer the report with IDs (`F1 F3`) or `all`. "ok" is not an approval: the skill asks again.

Run on a skill with three planted problems, the first report listed all three as F1 to F3 with
`path:line`, and no file changed until the answer `F1 F3`.

## Requirements

The `skill-maker` plugin and Python 3.9 or later as `python3`. skill-creator and plugin-dev are
recommended: see the [plugin README](../../README.md#recommended-tools).

## Limitations

- One skill or plugin per run. For a collection, use `skill-audit`; for READMEs, `skill-readme`.
- It reads files and does not run evals or tune triggers: it points you to skill-creator for those.
- Without a subagent tool, the review is done by the same agent, and the report says so.
