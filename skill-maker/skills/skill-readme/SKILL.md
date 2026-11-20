---
name: skill-readme
description: Inventories, checks and drafts the public README.md of a Claude Code plugin and of each skill it ships, against a fixed section contract (Why, Use cases, Usage, Installation and so on) that a catalog can extract. Use when asked to write, draft, review, check, audit or restructure the README of a plugin or a skill, to document a plugin for its users or for a marketplace or showcase site, or to list what a plugin distributes. Check mode is read-only; draft mode writes drafts beside the work, never over an existing README. Not for writing SKILL.md, AGENTS.md or API documentation.
license: MIT
argument-hint: "check|draft <plugin or skill folder> [output folder]"
effort: high
---

# README of a plugin and of its skills

Check or draft the public `README.md` of a plugin and of every skill it distributes. The README is for
the people who evaluate or use the component; `SKILL.md` and the manifest stay as they are.

Arguments: `$ARGUMENTS`

## Hard rules

1. **Never write over an existing README** while checking or drafting. Drafts go to the output folder.
2. **Never change** `SKILL.md`, a manifest, a script or a test. Report what is wrong in the notes.
3. **Every statement has a source** in the component's own files. No source: leave it out and record
   the missing data.
4. **Keep what the reader needs.** Still-true content that tells the reader what the component is
   for or how to start survives in the draft. Mechanism and history are cut and listed in the notes.
5. **Condense, never replicate.** A README says what the component does and why it exists, in few
   lines. How it works stays in `SKILL.md` and the agent files: no steps, rules, tools, permissions or
   models. A plugin README does not document its skills: one line and a link each. A lint warning
   about size means cut.
6. **No attribution**: no generator lines, session links or tool credits in a README or in the notes.

## Files of this plugin

- Scripts: `${CLAUDE_PLUGIN_ROOT}/scripts/` (`inventory.py`, `readme_lint.py`, `validate.py`; Python 3).
- Contract: `references/contract.md`. Read it before the first check or draft of the session.
- Writing rules: `references/writing-rules.md`. Read it before drafting.
- Notes format: `references/review-notes.md`. Read it before writing notes.
- Templates: `assets/plugin-readme-template.md`, `assets/skill-readme-template.md`.
- Manifest and frontmatter rules: `${CLAUDE_PLUGIN_ROOT}/shared/official-references.md`. Read it only
  when a finding is about a manifest or a frontmatter.

If `${CLAUDE_PLUGIN_ROOT}` is empty or the scripts are missing, the skill was installed without its
plugin: say so and stop.

## 1. Find the target and the mode

- **Mode**: `check` or `draft`, from the arguments or the request. "Review", "audit", "verify" mean
  check. "Write", "draft", "restructure", "update" mean draft. If unclear, ask.
- **Target**: a folder with `.claude-plugin/plugin.json` is a plugin: its README and the README of
  every skill it ships. A folder with `SKILL.md` is one skill: find its plugin root by walking up to
  the nearest `.claude-plugin/plugin.json`. No target given: use the plugin the working directory is
  in, and say which one.
- A marketplace or a repository with several plugins is several targets: run them one at a time, each
  from its own plugin root.

## 2. Inventory

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/inventory.py" <plugin root>
```

`plugin.readme` is the path of the plugin README: `README.md`, or `skills/README.md` when the plugin
root is a repository that also hosts other plugins (its root README is then the repository's page:
leave it alone). The JSON lists the plugin, its skills, agents, commands and hooks, whether each README exists, and
under `excluded` the `SKILL.md` files that are not distributed (internal skills, fixtures, other
plugins) with the reason. Work only on what is distributed. Show the user the list before going on
when it has more than one component.

## 3. Check the structure

For each README that exists:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/readme_lint.py" --profile plugin --plugin-root <plugin root> <plugin root>/<plugin readme>
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/readme_lint.py" --profile skill <skill folder>/README.md
```

Exit status 1 means errors, and that is a result, not a failure of the script. Keep the output: every
line goes into the notes unchanged.

## 4. Check mode

1. Dispatch the fact review (below) on the existing READMEs.
2. Write the review notes in the reply, in the format of `references/review-notes.md`: inventory,
   script findings, reviewer findings, scenarios, open questions. A missing README is one finding.
3. Write nothing to disk unless the user asks for the notes as a file.

## 5. Draft mode

1. **Output folder**: the one the user gave; otherwise a `readme-drafts/<plugin name>/` folder in the
   session's temporary or scratch directory. Never inside the plugin unless the user says so. Each
   draft keeps the relative path the inventory gives: `<output>/README.md`,
   `<output>/skills/<name>/README.md`.
2. **Read the sources** of each component: manifest, `SKILL.md`, its references, scripts, tests, and
   the existing README in full.
3. **Write the draft** from the template of its profile, following `references/writing-rules.md`.
   Delete the conditional sections that do not apply (`Use cases` included, when the uses are obvious)
   and every placeholder in angle brackets.
4. **Lint the drafts** with the commands of step 3, adding `--base-dir <folder the README is meant
   for>` so that relative links resolve from the component's own folder. Fix every error before the
   review, and cut until no size warning is left.
5. Dispatch the fact review on the drafts, giving the existing READMEs as the previous text.
6. Fix what the review proved wrong, once. Do not start a second review round on your own.
7. Write `<output>/review-notes.md` with what is left: open findings, scenarios marked observed or
   illustrative, kept and moved content, questions for the owner.
8. Report: the output folder, one line per draft, and the open questions.

## Fact review

Use the agent whose type ends in `readme-reviewer` (`skill-maker:readme-reviewer`). If it is not
available, use a general-purpose subagent with the same prompt and say so in the notes. Give it:

- the absolute paths of the READMEs to review and of the component each documents;
- the inventory JSON;
- the absolute paths of `references/contract.md` and `references/review-notes.md` in this skill;
- in draft mode, the path of each existing README as the previous text.

Do not give it your own opinion of the text. Its findings go into the notes with their evidence.

## Applying a draft

Only when the user asks, after they have read the draft and the notes.

1. Follow the project's own instructions on how documents are revised and versioned. If they say
   nothing and the README has no version scheme, ask the user how they want existing documents updated
   before touching one.
2. Show the difference between the existing README and the draft, then copy the draft in place.
3. Run the final validation from the plugin root and report its output as it is:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py" <plugin root>
```

It checks the manifest, the skill and agent frontmatter and every README, and runs
`claude plugin validate --strict` when the `claude` command is available.
