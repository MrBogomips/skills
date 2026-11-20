---
summary: Checks and drafts the public README of a Claude Code plugin and of each skill it ships, against one fixed section contract.
---

# skill-readme

Checks and drafts the public `README.md` of a plugin and of every skill it distributes. You get review
notes that name each problem with its file, section and evidence, and, in draft mode, a README per
component written from the component's own files.

## Why

A README written by hand drifts from the code: an option is renamed, a requirement changes, a skill is
added and never listed. A README written by a model without checks invents commands.

This skill takes both problems apart:

- It lists what the plugin really distributes from the manifest and the folders, and leaves out
  internal skills, test fixtures and other plugins in the same repository.
- A script checks the structure: frontmatter, title, introduction, section titles and order, scenarios,
  relative links, and that every distributed component is documented.
- A separate reviewer, which has not seen how the text was written, checks each command, dependency,
  output and limit against the manifest, `SKILL.md`, scripts and tests.
- Existing content is kept. Custom sections stay where the author put them, and the value they hold,
  such as measured performance, is raised into the Why.

## Use cases

### Find what is wrong with an existing README

**Context:** Your plugin's README was written a year ago and the plugin has gained an agent and a
setting since.

**Action:** Run `/skill-maker:skill-readme check <plugin folder>`.

**Result:** Review notes in the reply: the missing `Agents` section, the setting no section mentions,
the sections whose titles or order differ from the contract, each with its line.

### Write the README of a skill that has none

**Context:** A skill has a `SKILL.md`, two scripts and tests, and no README.

**Action:** Run `/skill-maker:skill-readme draft <plugin folder>/skills/<skill> <output folder>`.

**Result:** `<output folder>/skills/<skill>/README.md` with the contract sections filled from the
skill's files, and `<output folder>/review-notes.md` listing which scenarios are illustrative and what
the sources did not say.

### Restructure a README without losing its content

**Context:** A skill README already has `Options`, `Example` and a generated `Performance` section.

**Action:** Run the skill in draft mode on that skill.

**Result:** A draft with the contract sections first and the three existing sections kept after them,
the generated one unchanged. The notes list what moved and where.

## Usage

```text
/skill-maker:skill-readme check|draft <plugin or skill folder> [output folder]
```

- `check` is read-only and answers with the review notes.
- `draft` writes drafts and notes to the output folder. Without one, it uses a `readme-drafts/` folder
  in the session's temporary directory and tells you where.
- The folder is a plugin (it contains `.claude-plugin/plugin.json`) or one skill (it contains
  `SKILL.md`). Without a folder, the skill uses the plugin of the working directory.

You can also ask in words, for example "check the README of this plugin".

A draft replaces an existing README only when you ask for it after reading it. The skill then shows
the difference and runs the final validation.

## Inputs and outputs

| | What |
|---|---|
| Reads | `.claude-plugin/plugin.json`, every distributed `SKILL.md` with its references, scripts and tests, agent, command and hook files, and the existing READMEs. |
| Writes, check mode | Nothing. The review notes are in the reply. |
| Writes, draft mode | `<output>/README.md`, `<output>/skills/<name>/README.md` for each skill, and `<output>/review-notes.md`. |

The review notes hold the inventory, one table of findings per README (section, kind, finding,
evidence), the scenarios marked observed or illustrative, the content kept or moved, and the open
questions for the owner.

The sections a README must have are in [references/contract.md](references/contract.md).

## Requirements

- The `skill-maker` plugin: the skill uses its scripts and its reviewer agent.
- Python 3.9 or later as `python3`.

## Limitations

- Works on one plugin at a time.
- Does not change `SKILL.md`, manifests, scripts or tests: it reports what is wrong with them.
- Statements are checked against files, not by running the component.
