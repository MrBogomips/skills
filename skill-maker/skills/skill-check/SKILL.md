---
name: skill-check
description: Checks one skill or plugin against skill-maker's authoring rulebook (descriptions, language, progressive disclosure, scripts, test material, agents and hooks) with the validator and an independent read-only reviewer, then fixes only the findings the user approves by ID. Use when asked to check, review, lint or vet a skill, an agent or a plugin before publishing it, or after skill-creator or plugin-dev wrote one. Not for READMEs (skill-readme), a whole collection of skills (skill-audit), running evals, or instruction files.
license: MIT
argument-hint: "<skill or plugin folder> [--custom]"
effort: high
---

# Check a skill or plugin

Check one skill, or every skill and agent of one plugin, against the rulebook. Report first; change only
what the user approves.

Arguments: `$ARGUMENTS`

## Files of this plugin

- Rulebook: `${CLAUDE_PLUGIN_ROOT}/shared/rules/` (start with its `README.md`).
- Official tools and what is lost without them: `${CLAUDE_PLUGIN_ROOT}/shared/official-references.md`.
- Validator: `${CLAUDE_PLUGIN_ROOT}/scripts/validate.py` for a plugin, `skill_lint.py` for a skill alone (Python 3.9+).
- Report format: `references/report.md`.

If `${CLAUDE_PLUGIN_ROOT}` is empty or these files are missing, the skill was installed without its
plugin: say so and stop.

## Steps

1. **Target.** Resolve the folder given. A folder with `SKILL.md` is one skill: its plugin root is the
   nearest parent with `.claude-plugin/plugin.json`. A folder with `.claude-plugin/plugin.json` is a
   plugin: check every skill and agent it distributes. With no plugin root, check the skill alone and
   skip the manifest checks.
2. **Channel and audience.** `--portable` applies when the skills are also distributed through the
   `skills` CLI; `--custom` when they are project- or user-scoped and never published. Infer both from
   the project's instruction files; ask only if they do not say.
3. **Validator.** Run it and keep its output:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py" --no-claude [--portable] [--custom] <plugin root>
   ```

   For a skill with no plugin root, run the skill checks alone:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/skill_lint.py" [--portable] [--custom] <skill folder>`.

   Keep only the findings for the target. Errors from the README contract belong to skill-readme: list
   them under Next steps instead of fixing them here.
4. **Independent review.** Dispatch the `rulebook-reviewer` agent in `check` mode with the target's
   paths, the rulebook path, the path of `official-references.md` and the validator output. Never pass
   your own opinion of the files. Without a subagent tool, apply the rules marked `reviewer` or `both`
   yourself, one file at a time, confirm or reject each `S3` warning, and say in the report that the
   review was not independent.
5. **Report**, in the format of `references/report.md`:
   - **Recommended tools** first, when skill-creator or plugin-dev is missing. Read the session's
     available skills, or `claude plugin list` when unsure. Show the rows of the Recommended tools table
     in `official-references.md` for each missing tool, every run until it is installed.
   - Findings from the validator and the reviewer, merged, numbered F1, F2…, most severe first, each
     with its rule ID and `path:line`. Drop the `S3` warnings the reviewer rejected.
   - Next steps: evals and trigger tuning go to skill-creator, agents, hooks and commands to plugin-dev;
     when one is missing, give the manual method of the matching T or C rule.
6. **Fix only approved findings.** Ask which IDs to apply. Edit only for the IDs the user names, or for
   all of them when the user says "all". Fix the finding and nothing else: a change of behavior the
   rules do not require is a suggestion in the report, not an edit.
7. **Re-check.** Run step 3 again on what changed and report what is left.

## Approval is by ID

The point of the report is that the user decides what changes in their skill. An edit before that
decision takes the decision away.

| Excuse | Answer |
|---|---|
| "The user said ok" | "ok" acknowledges the report. Ask which IDs, or whether "all". |
| "The fix is obvious" | Obvious to you. Put it in the report; it is applied in seconds once approved. |
| "I'll fix the small things and report the rest" | Small edits still change someone else's skill without asking. |
| "While I'm in the file, I'll improve the script too" | Not a finding. Suggest it; don't do it. |
| "The user is in a hurry" | Offer "all" as an answer. Still ask. |
