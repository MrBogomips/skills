---
summary: Opinionated Claude Code plugin for producing quality skills and plugins, starting with public READMEs that follow one fixed structure.
---

# skill-maker

Tools for people who publish skills and plugins and want them to read as one catalog. The first skill
checks and drafts the public `README.md` of a plugin and of every skill it ships, against a fixed
section contract, with every statement traced to the component's own files.

## Why

A plugin's `SKILL.md` and manifest are written for agents: they say when to load a skill and how it
behaves. People deciding whether to install it need something else, and most plugins give it to them
in a README with its own structure, or give nothing at all for the single skills.

`skill-maker` settles the structure once:

- **One contract** for every README: the same sections, with the same titles, in the same order. A
  reader who has seen one knows where to look in the next, and a catalog can extract them by heading.
- **Facts, not prose.** A draft states only what the manifest, `SKILL.md`, scripts and tests support.
  An independent reviewer rereads it in a fresh context and reports contradictions with their source.
- **Nothing is lost.** Valid content and custom sections of an existing README are kept, and drafts
  never overwrite a file.
- **Repeatable checks.** The structure is checked by scripts with tests, not by reading.

The contract is opinionated. Installing the plugin means adopting it.

## Use cases

### Check a plugin before publishing it

**Context:** You are about to list a plugin with three skills in a marketplace, and only the plugin has
a README.

**Action:** Run `/skill-maker:skill-readme check .` from the plugin folder.

**Result:** Review notes in the reply: the components the plugin distributes, the three missing skill
READMEs, each structural error of the existing README with its line, and the statements that
contradict the manifest or the scripts.

### Draft the missing READMEs

**Context:** The check listed four READMEs to write or restructure.

**Action:** Run `/skill-maker:skill-readme draft . ../readme-drafts`.

**Result:** One draft per component under `../readme-drafts`, at the same relative paths as in the
plugin, and a `review-notes.md` with the open questions. No file of the plugin changes.

### Validate a plugin in a pipeline

**Context:** You want a pull request to fail when a skill is added without a README.

**Action:** Run `python3 scripts/validate.py --no-claude <plugin folder>` from a checkout of this
plugin.

**Result:** One line per finding with file, line and section, and exit status 1 when there is an
error.

## Included components

| Skill | What it does |
|---|---|
| [`skill-readme`](skills/skill-readme/README.md) | Inventories, checks and drafts the README of a plugin and of each skill it ships. |

## Agents

`readme-reviewer` is a read-only reviewer. The `skill-readme` skill dispatches it to compare a README,
existing or drafted, with the component's manifest, `SKILL.md`, references, scripts and tests. It
returns findings with their evidence and never edits a file.

## Installation

```text
/plugin marketplace add MrBogomips/claude-plugins
/plugin install skill-maker@mrbogomips
```

**Standalone skills: no, plugin only.** The skill runs the scripts in the plugin's `scripts/` folder
and dispatches the plugin's reviewer agent, so it does not work installed alone.

## Quick start

From the folder of a plugin, the one that contains `.claude-plugin/plugin.json`:

```text
/skill-maker:skill-readme check .
```

You get the list of the components the plugin distributes, then the review notes: one table of
findings per README, each with its section and its evidence. Nothing is written to disk.

## Requirements

- Claude Code with plugin support.
- Python 3.9 or later on `PATH` as `python3`. The scripts use the standard library only.

## Limitations

- One plugin at a time. A marketplace or a repository with several plugins is checked one plugin
  folder after the other.
- The contract is fixed: sections, titles and order cannot be configured.
- READMEs are written and checked in English.
- The scripts check structure. Whether a statement is true is judged by the reviewer agent, so that
  part of a check can vary between runs.
- No extractor for a catalog site is included; the contract only makes one possible.

## License

MIT
