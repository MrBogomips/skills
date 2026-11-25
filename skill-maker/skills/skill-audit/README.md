---
summary: Audits a folder of skills or plugins and gives each skill a keep, improve, merge or retire verdict, without changing anything.
---

# skill-audit

Audits every skill in a folder, such as a repository, a marketplace folder or your own skills folder,
against the authoring rulebook. You get one report with a verdict for each skill (keep, improve, merge
with another, retire), its reason and its top findings, and the count per verdict. Nothing is changed.

## Why

Checking skills one at a time does not show which two answer the same requests, or which ones have
fallen behind the rules. skill-audit judges the whole set at once, flags merge candidates across the
collection, and gives each verdict a reason that stands on its own. Every decision stays with you: it
edits nothing, and offers `skill-check` for the skills worth improving.

## Usage

```text
/skill-maker:skill-audit <folder holding skills or plugins> [--custom]
```

- The folder can mix plugins and loose skills.
- `--custom` marks skills that are never published, which skips the English check. Without it, the
  skill reads your project's instruction files to tell, and asks when they don't say.

The reply gives the path of the report and the counts per verdict, then offers `skill-check` on each
skill marked improve, one at a time.

## Inputs and outputs

The report is a Markdown file saved where your project's instruction files put working documents,
otherwise in the session scratchpad, otherwise in the system temporary folder. It is never written
inside a skill folder.

## Requirements

The `skill-maker` plugin and Python 3.9 or later as `python3`. skill-creator and plugin-dev are
recommended: see the [plugin README](../../README.md#recommended-tools).

## Limitations

- Read-only: merges and retirements are yours to carry out.
- It does not fix a skill (use `skill-check`) or review READMEs (use `skill-readme`).
- Without a subagent tool, the review is done by the same agent, and the report says so.
