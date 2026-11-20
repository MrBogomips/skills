---
summary: <One sentence: what the plugin does and for whom. At most 200 characters.>
---

# <plugin-name>

<Introductory paragraph, at most 60 words: what the plugin does and what the reader gets. This
paragraph is the short description in the catalog.>

## Why

<Two to four sentences: the problem the reader has and why this plugin exists. No feature list, no
description of how it works.>

## Use cases

<Only if the uses are not obvious from the introduction; otherwise delete this section. At most three
scenarios, one sentence for each part.>

### <Task in the reader's words>

**Context:** <Who the reader is and the situation they are in.>

**Action:** <What they run or ask.>

**Result:** <What they get, as something they can check: a file, a message, a state.>

## Included components

| Skill | What it does |
|---|---|
| `<skill-name>` | <One short line. Link the name to the skill's README: everything else about the skill is there.> |

## Agents

<Only if the plugin ships agents; otherwise delete this section. One line for each agent: what it is
for. Not its tools, permissions, model or steps.>

## Commands

<Only if the plugin ships commands; otherwise delete this section. One line for each command: how to
call it and what for.>

## Hooks

<Only if the plugin ships hooks; otherwise delete this section. One line for each hook: when it fires,
what for, and how to switch it off.>

## Installation

```text
/plugin marketplace add <owner>/<marketplace-repo>
/plugin install <plugin-name>@<marketplace>
```

**Standalone skills: <yes | yes, with less | no, plugin only>.** <What is lost when a skill is
installed alone, or why it cannot be.>

## Quick start

<The first command or request to try after installing, and one sentence on what the reader should
see. The rest is in the skill's README.>

## Requirements

<Only if there are any; otherwise delete this section. Tools, versions, accounts, keys.>

## Configuration

<Only if there is any; otherwise delete this section. Each setting with its default.>

## Limitations

<Only if there are any; otherwise delete this section. What the plugin does not do, known gaps.>

## License

<The license in plugin.json.>
