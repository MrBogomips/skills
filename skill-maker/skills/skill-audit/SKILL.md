---
name: skill-audit
description: Audits a collection of skills or plugins against skill-maker's authoring rulebook and gives each skill a verdict (keep, improve, merge or retire) with its reasons and top findings, without changing anything. Use when asked to audit, take stock of, review, clean up or deduplicate a set of skills or plugins, such as a repository, a marketplace folder or a user's skills folder. Not for checking or fixing one skill (skill-check) or for READMEs (skill-readme).
license: MIT
argument-hint: "<folder holding skills or plugins> [--custom]"
effort: high
---

# Audit a collection of skills

Give every skill in a folder a verdict against the rulebook, read-only.

Arguments: `$ARGUMENTS`

## Files of this plugin

- Rulebook: `${CLAUDE_PLUGIN_ROOT}/shared/rules/` (start with its `README.md`).
- Official tools and what is lost without them: `${CLAUDE_PLUGIN_ROOT}/shared/official-references.md`.
- Scripts (Python 3.9+): `inventory.py`, `validate.py` and `skill_lint.py` in `${CLAUDE_PLUGIN_ROOT}/scripts/`.
- Report format: `references/report.md`.

If `${CLAUDE_PLUGIN_ROOT}` is empty or these files are missing, the skill was installed without its
plugin: say so and stop.

## Steps

1. **Find the skills.** Every folder holding `.claude-plugin/plugin.json` under the target is a plugin:
   list its skills with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/inventory.py" <plugin root>`. Every other
   `SKILL.md` is a loose skill. Skip folders that version control ignores.
2. **Channel and audience.** Pass `--portable` for plugins whose skills are also distributed through
   the `skills` CLI, and `--custom` for skills that are project- or user-scoped and never published.
   Infer both from the project's instruction files; ask only if they do not say.
3. **Validator.** Run `validate.py --no-claude` on each plugin and `skill_lint.py` on the loose skills,
   with the flags of step 2, and keep the findings per skill.
4. **Review in batches.** Split the skills into batches of about 20 and dispatch the `rulebook-reviewer`
   agent in `audit` mode for each batch, in parallel when the harness allows, with the batch's paths,
   the rulebook path, the path of `official-references.md` and the validator findings for that batch.
   Without a subagent tool, judge the batches yourself and say so in the report.
5. **Overlaps.** Compare the descriptions across batches: two skills that answer the same requests are
   merge candidates, even when they sit in different batches.
6. **Report**, in the format of `references/report.md`. When skill-creator or plugin-dev is missing
   (check the session's available skills, or `claude plugin list` when unsure), open the report with
   **Recommended tools**: the rows of the Recommended tools table in `official-references.md` for each
   missing tool, on every run until it is installed. Save the report where the project's instruction
   files put working documents, otherwise in the session scratchpad, otherwise in the system temporary
   directory; never inside a skill folder. Give the user its path and the counts per verdict.
7. **No edits.** Offer `skill-check` on the skills marked `improve`, one at a time.
