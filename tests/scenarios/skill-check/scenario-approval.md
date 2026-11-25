# Scenario: findings first, fixes only by ID

## Steps

1. `/skill-maker:skill-check <fixture>/release-notes`
2. When the report appears, answer `ok`.
3. Answer `F1 F3` (or the IDs of the trigger and the `tests/` findings).

## Acceptance criteria

- The report lists the three planted problems with rule IDs (S3, S7, P6) and `path:line`.
- The report opens with **Recommended tools** when skill-creator or plugin-dev is not installed.
- After `ok`, no file has changed and the agent asks which IDs to apply.
- After the IDs, only those findings are fixed; the script's behavior is unchanged.
- The re-check at the end shows the remaining finding (the script call) and nothing new.

## Last run (2026-11-25)

Headless, `claude -p --plugin-dir ./skill-maker`, on the fixture. Passed.

- Turn 1: report only. The three planted problems came first as F1 (P6), F2 (S7) and F3 (S3), with
  `path:line`. Recommended tools listed plugin-dev, which was missing; skill-creator was installed. The
  reviewer added nine findings on the fixture's own weaknesses. No file changed.
- Turn 2, `ok`: no file changed; the agent asked for IDs.
- Turn 3, `F1 F3`: `tests/` moved out of the skill and the trigger translated. The script and step 1 were
  unchanged. The re-check showed F2 still open.
- Gap found and fixed: `validate.py` needs a plugin root, so a loose skill is now checked with
  `skill_lint.py`.
