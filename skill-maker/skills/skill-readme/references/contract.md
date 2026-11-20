# README contract

One `README.md` at the root of every plugin and one next to every distributed `SKILL.md`. The README
is written in English for the people who evaluate or use the component. It also feeds a catalog, so
its blocks are found by heading level and exact title.

`${CLAUDE_PLUGIN_ROOT}/scripts/readme_lint.py` checks everything in this file that a script can check.

## Every README

```markdown
---
summary: One sentence that says what the component does and for whom.
---

# component-name

Introductory paragraph.

## Why
...
```

- **Frontmatter**: `summary:`, one plain-text sentence, at most 200 characters. Other keys are allowed.
- **H1**: one, the first heading, the name of the plugin or skill as it is installed or invoked.
- **Introduction**: the first paragraph after the H1. It says what the component does and what the
  reader gets. More paragraphs may follow; only the first is the short description.
- **`summary:` and introduction say the same thing.** The summary is the one-line form.
- **H2 sections**: unique titles, spelled exactly as below, in the order below.
- **Conditional sections** (in brackets below) are left out when they have nothing to say. Never keep
  one with "None" or "N/A".
- **Custom sections**: any other H2 is allowed after the last contract section (in a plugin README,
  before `License`). Existing custom sections are always kept.
- A heading inside a fenced code block is an example, not a section.

## Plugin profile

| # | H2 | When | What it holds |
|---|---|---|---|
| 1 | `Why` | always | The problem and the value: what the reader gains, and what sets this plugin apart. |
| 2 | `Use cases` | always | Scenarios, one H3 each. |
| 3 | `Included components` | always | Every distributed skill, by name, with a relative link to its README. |
| 4 | `Agents` | the plugin ships agents | Each agent: what it does and what dispatches it. |
| 5 | `Commands` | the plugin ships commands | Each command: how to call it and what it returns. |
| 6 | `Hooks` | the plugin ships hooks | Each hook: the event, what it does, how to switch it off. |
| 7 | `Installation` | always | The install commands, and whether the skills also install alone and what is lost that way. |
| 8 | `Quick start` | always | The first command to run and what the reader should see. |
| 9 | `Requirements` | there are any | Tools, versions, accounts, keys. |
| 10 | `Configuration` | there is any | Settings, with defaults. |
| 11 | `Limitations` | there are any | What it does not do, known gaps. |
| – | custom sections | – | Kept as they are. |
| last | `License` | always | The license in the manifest. |

## Skill profile

| # | H2 | When | What it holds |
|---|---|---|---|
| 1 | `Why` | always | The problem and the value of this skill. |
| 2 | `Use cases` | always | Scenarios, one H3 each. |
| 3 | `Installation` | the skill installs alone, and this was verified | The command, and what differs from the plugin install. |
| 4 | `Usage` | always | How to invoke it, the arguments, an example the reader can run. |
| 5 | `Inputs and outputs` | always | What it reads and what it writes or returns, with paths and formats. |
| 6 | `Requirements` | there are any | Tools, versions, accounts, keys. |
| 7 | `Limitations` | there are any | What it does not do, known gaps. |
| – | custom sections | – | Kept as they are. |

## Use cases

Each scenario is an H3 under `Use cases`, titled with the task in the reader's words, and has three
labeled parts in this order:

```markdown
### Draw a schema from a migration

**Context:** You inherit a service with forty migrations and no diagram.

**Action:** Give the skill the `migrations/` folder and ask for the ERD.

**Result:** One HTML page that opens from disk, with every table and foreign key.
```

The result is concrete: a file, a message, a state the reader can check.

## Words and facts

The descriptions in `plugin.json` and in `SKILL.md` are written for agents that decide when to load
the component. The README is written for people who decide whether to use it. They may be worded
differently and are never copied into each other. They must agree on facts: names, versions,
components, commands, requirements.

`SKILL.md` keeps how the skill behaves. The README explains how to use it and what comes out.

## Extraction

For the catalog, a reader of these files takes:

| Field | Source |
|---|---|
| Plugin name, category, tags | the marketplace manifest entry, where present |
| Plugin version | `version` in the plugin's `plugin.json` |
| Skill identifier | `name` in the frontmatter of `SKILL.md` |
| Catalog key of a skill | the pair plugin name and skill name |
| One-line description | `summary:` in the README frontmatter |
| Short description | the introductory paragraph |
| Value | the `Why` section |
| Scenarios | each H3 under `Use cases`, with its three labeled parts |
| Components (plugin) | the `Included components` section |

A block starts at its heading and ends at the next heading of the same or a higher level. Headings
inside fenced code blocks are skipped. A missing conditional section is an empty field, not an error.
Custom sections are not extracted.
