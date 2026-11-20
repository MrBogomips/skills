# Writing a README draft

Read this before drafting. The structure is in `contract.md`; this file is about the content.

## Sources, in order of trust

1. Tests, scripts and bundled files: what the component really does.
2. `SKILL.md` and its references: how it is told to behave.
3. The manifest: name, version, license, components, settings.
4. The existing README: what the author chose to tell readers.

Write a statement only when a source in 1 to 3 supports it. When the existing README says something
no other source confirms, keep it and record it in the review notes as unverified. Never fill a gap
with a guess: leave the statement out and record the missing data.

## Condense, do not replicate

The README says what the component does and why it was made. It does not explain how it works. The
reader who wants the mechanism reads `SKILL.md` or the agent file, which are a click away.

- Read the sources to understand the component and to check facts, not to retell them.
- Leave out: the steps and phases of a skill, its rules and checks, the tools and permissions of an
  agent, the model and effort, thresholds and internal file names, the logic of a hook or script.
  Keep one of these only when the reader must act on it (a switch to turn a hook off, a file they
  have to provide).
- One line per component. "`reviewer`: rereads each draft in a fresh context, read-only" is the level.
  Three lines for one agent are too many.
- Prefer one sentence to a list, and a list to a table. Add a conditional section only when it tells
  the reader something they need before using the component.
- Stay within the budgets in `contract.md`. A warning from the script means cut, not reword.
- When in doubt whether a sentence describes intent or mechanism, ask: would it change if the
  implementation were rewritten with the same purpose? If yes, it is mechanism: leave it out.

## Plugin README: point to the skills, do not document them

- `Included components` gives each skill one short line and the link to its README. That is all the
  plugin README says about a skill.
- How a skill is invoked, its arguments, options, outputs, requirements and limits belong to the
  skill README. Move them there when the existing plugin README holds them, and record the move in
  the review notes.
- `Why` is the reason the plugin exists as a whole. `Quick start` is one command and one sentence on
  what comes back. `Requirements` and `Limitations` hold only what is true for the whole plugin.
- With a single skill, the plugin README is close to a cover page: why, the link, the other
  components in a line each, how to install.

## Keep what is valid

- Read the whole existing README first. Every statement that is still true has a place in the draft.
- An existing section that is a contract section under another title (`Install`, `Getting started`)
  becomes that contract section, with its text.
- **Every other existing H2 is a custom section and stays**: same title, same text, after the contract
  sections. In a plugin README, a custom section that documents one skill moves, whole, to that
  skill's README. Do not dissolve it into `Usage` or `Inputs and outputs`, even when it would fit there.
- Write the contract sections new, from the sources. Where a custom section already holds the detail
  (options, a long example, a format, measurements, how a hook decides), the contract section is one
  line that links to it. Do not repeat it.
- Content a tool generates (a table between markers, a performance section) stays byte for byte.
- Fix a statement the sources contradict wherever it stands, custom sections included, and record
  the correction in the review notes.
- In the review notes, list what became a contract section, what stayed as custom, and anything you
  could not place.

## Why

The Why sells the component honestly. It answers: what problem does the reader have, and what does
this component do about it that the alternatives do not.

- Look for the value everywhere: the introduction, the custom sections, the tests, the measurements.
  A result buried in a detail section belongs in the Why as a claim, with the detail left where it is.
  For a component that generates artifacts, measured performance is usually the value: state it in the
  Why and link to the section with the numbers.
- State a claim only with its evidence in the sources. No superlatives, no "powerful", no "seamless".
- Two to four sentences, or up to four short bullets of concrete gains. It is the reason the component
  exists, not a list of its features.

## Use cases

- Optional. Write the section only when the component serves tasks a reader would not guess from the
  introduction. A component that does one thing when asked (a retrospective, a formatter) has none.
- One to three scenarios, each a different kind of reader or task, each part one sentence.
- Take scenarios first from tests, examples and recorded runs: those are observed. Add illustrative
  ones only for tasks the sources show the component can do.
- In the review notes, mark every scenario observed (with its source) or illustrative. The README does
  not carry the mark.
- The result names something the reader can check: a file and where it lands, a message, a state.

## First command

A reader must find the first command to run and predict what happens.

- Plugin `Quick start`: after installation, the one command or request to try first, and what the
  reader sees.
- Skill `Usage`: the invocation as the reader types it (`/plugin:skill`, or the request in words when
  the skill triggers on its own), the arguments, one example with its result. Not the steps the skill
  then follows.
- Copy commands from the sources. Never write a command you have not found there.

## Installation

- Plugin: the marketplace commands, then one bold line that says whether the skills also install alone
  (`**Standalone skills: yes.**`, `**yes, with less.**` or `**no, plugin only.**`) and what is lost.
  A skill that reads `${CLAUDE_PLUGIN_ROOT}`, plugin settings or files outside its own folder is
  plugin only.
- Skill: only when a standalone install was verified, for example by a listing command in the
  repository's own instructions.

## Voice

- Address the reader as "you". Present tense. Short sentences.
- No history, no maintainer notes, no internal process, no roadmap. Migration notes a current user
  needs go in `Installation`.
- No attribution or generator lines, no session links, no badges about how the text was produced.
- Name files and commands in backticks. Fence commands with their language.

## Summary and introduction

Write the introduction first, then compress it into the `summary:` sentence. After any change to one,
reread the other. Do not copy the manifest or `SKILL.md` description: those are written for agents.
