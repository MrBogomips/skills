# Rules for SKILL.md

### S1. The description says what, when and what not

Say what the skill does, when to use it (concrete situations and the words a user would use) and what it
is not for, in the third person. Never summarize the workflow step by step: an agent that reads a summary
of the steps tends to follow the summary and skip the body. Keep it within 1024 characters and as short
as the triggers allow, because every description is loaded into every session.

Official source: docs-skills · Checked by: both

### S2. Triggers use the user's words

Cover what a user would actually type: the symptoms they see, error messages, tool names and synonyms.
A description written in the author's vocabulary is not found by a user who uses another.

Checked by: reviewer

### S3. Language

A public skill is written in English: frontmatter, `SKILL.md`, references, agent files, README and
examples. Trigger phrases are English too. A term from another language is allowed only when English
speakers commonly use it (*ad hoc*, *kaizen*). There is no exception for skills whose subject is writing
in several languages: the description can say "in any language". The skill still talks to the user in
the user's language.

A custom skill follows the language set by the project's instruction file, then by the user's own
instructions, and is written in English when neither sets one.

Checked by: both (the validator warns on likely foreign phrases; the reviewer confirms)

### S4. Load only what a run needs

Keep the body under 500 lines. Move detail into reference files one level below the skill, each loaded by
the step that needs it. Material that applies to one variant only (a backend, a provider, a language) gets
a file of its own, so a run loads one variant. A reference longer than 300 lines starts with a list of
its contents.

Official source: docs-skills · Checked by: both (the validator checks the line count)

### S5. Explain why, and match the form to the failure

Give the reason behind an instruction: a model that knows why applies it to cases the text did not
foresee. Choose the form from the failure you are preventing:

- wrong shape of output: a positive recipe, or one example;
- a step that gets skipped: a required slot in the output the step fills;
- a discipline the agent dodges under pressure: a prohibition with its reason, plus the excuses agents
  give for breaking it, each answered.

Prohibitions are for the last case only. No capitals for emphasis.

Checked by: reviewer

### S6. One good example

One excellent example teaches more than several average ones. Take it from a different domain than the
test cases, so the skill is not tuned to its own tests.

Checked by: reviewer

### S7. Repeated, deterministic work goes in a script

When a run keeps doing the same mechanical work, bundle a script. Call it through its interpreter, with a
path relative to the skill directory (`python3 scripts/check.py`, `bash scripts/sync.sh`): installers do
not always keep the executable bit. A helper that test runs keep rewriting is a script waiting to be
bundled.

The limit: no script for what one sentence of the skill lets the model do with the harness's own tools,
such as copying a result to the clipboard, opening a file or calling a CLI the user has. Such a script
costs code, tests and one case per platform, and it fixes a single way of doing what the model would
fit to the user's request, the context and its memory. Script what must come out the same on every run,
or what the baseline run (T1) shows the model getting wrong; state the rest in a sentence.

Checked by: both (the validator warns on a bundled script run without an interpreter; the reviewer judges
whether a script earns its place)

### S8. No skill for what a tool can enforce

What a validator, a linter or a hook can enforce belongs there, not in a skill. Conventions of a single
project belong in that project's instruction file, not in a skill.

Checked by: reviewer

### S9. Describe choices, not flags

Do not copy a tool's options into the skill: they drift with each release. Say which choice to make and
let the agent read the tool's own help for the exact syntax.

Checked by: reviewer

### S10. Diagrams only for decisions that are not obvious

Use a flowchart only where the agent would otherwise choose wrongly, and keep code out of it.

Checked by: reviewer

### S11. Least surprise

A skill does nothing its description would not lead a user to expect: no undeclared network calls, no
writes outside its stated scope, no data sent to a third party without saying so.

Checked by: reviewer

### S12. Frontmatter keys fit the channel

Portable keys work in every harness: `name`, `description`, `license`, `compatibility`, `metadata`,
`allowed-tools`. Claude Code adds its own keys (listed in `../official-references.md`); they are fine in a
plugin-only skill. A skill also distributed through the `skills` CLI may carry them only if it still works
in a harness that ignores them. Any other key is a mistake.

Official source: docs-skills, agentskills-spec · Checked by: validator
