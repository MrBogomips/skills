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

## Keep what is valid

- Read the whole existing README first. Every statement that is still true has a place in the draft.
- An existing section that is a contract section under another title (`Install`, `Getting started`)
  becomes that contract section, with its text.
- **Every other existing H2 is a custom section and stays**: same title, same text, after the contract
  sections. Do not dissolve it into `Usage` or `Inputs and outputs`, even when it would fit there.
- Write the contract sections new, from the sources. Where a custom section already holds the detail
  (options, a long example, a format, measurements), say the essential in the contract section and
  link to the custom section for the rest. Do not repeat it.
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
- Three to six sentences, or a short list of concrete gains.

## Use cases

- Two to four scenarios, each a different kind of reader or task.
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
  the skill triggers on its own), the arguments, one complete example with its result.
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
