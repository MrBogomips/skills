---
summary: <One sentence: what the plugin does and for whom. At most 200 characters.>
---

# <plugin-name>

<Introductory paragraph: what the plugin does and what the reader gets. This paragraph is the short
description in the catalog.>

## Why

<The problem the reader has and what this plugin does about it that the alternatives do not. State
each claim with evidence found in the sources.>

## Use cases

### <Task in the reader's words>

**Context:** <Who the reader is and the situation they are in.>

**Action:** <What they run or ask.>

**Result:** <What they get, as something they can check: a file, a message, a state.>

## Included components

| Skill | What it does |
|---|---|
| `<skill-name>` | <One line. Link the name to the skill's README once it exists.> |

## Agents

<Only if the plugin ships agents; otherwise delete this section. Each agent: what it does and what
dispatches it.>

## Commands

<Only if the plugin ships commands; otherwise delete this section. Each command: how to call it and
what it returns.>

## Hooks

<Only if the plugin ships hooks; otherwise delete this section. Each hook: the event, what it does and
how to switch it off.>

## Installation

```text
/plugin marketplace add <owner>/<marketplace-repo>
/plugin install <plugin-name>@<marketplace>
```

**Standalone skills: <yes | yes, with less | no, plugin only>.** <What is lost when a skill is
installed alone, or why it cannot be.>

## Quick start

<The first command or request to try after installing, and what the reader should see.>

## Requirements

<Only if there are any; otherwise delete this section. Tools, versions, accounts, keys.>

## Configuration

<Only if there is any; otherwise delete this section. Each setting with its default.>

## Limitations

<Only if there are any; otherwise delete this section. What the plugin does not do, known gaps.>

## License

<The license in plugin.json.>
