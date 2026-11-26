# Design principles

What earns a place in this repository. The authoring rules (how a skill is written) live in
`skill-maker/shared/rules/`; this file decides whether a skill should exist at all.

## The value gate

A skill or plugin is worth adding only when it carries value that frontier models and the harnesses do not
already deliver, and are unlikely to deliver soon. Frontier models get better with every release, and
harnesses keep adding built-in features and official skills. A skill that copies a capability they already
have competes with something that improves on its own; it costs context and maintenance and is quietly
overtaken.

A skill therefore distils a **method, a process or a discipline**: a sequence of checks, a decision
procedure, an approval protocol, an integration of tools the user owns. It never restates a capability the
model or the harness already has.

### The five tests

A new skill, or a change of scope to an existing one, passes all five or does not go in:

1. **Not native.** Neither the model, asked in one plain request, nor the harness (built-in features,
   settings, official skills and plugins) already does it well. Evidence: the baseline run (rule T1)
   shows a concrete failure that repeats, and the official documentation shows no equivalent feature.
2. **Durable value.** The value lies in a method, a process, a discipline or an integration, not in a
   capability gap that models are closing (knowing current facts, writing better, judging risk). Ask:
   if the next model were twice as good, would this skill still be needed?
3. **On top of native, not beside it.** Where the harness has a mechanism (permission rules, hooks,
   memory, plan mode, settings), the skill reads, configures or drives it. It does not build a parallel
   one.
4. **Thin.** The skill holds only what the baseline lacks. Whatever the model does unaided is cut. A
   difference that fits in one line of a prompt does not need a skill.
5. **Revisited.** The gate is run again at every official drift and at major harness releases. A skill
   that the native features have absorbed becomes a candidate for retirement.

### Outcome

The gate ends in one of three outcomes:

- **Go**: the skill is written, holding only the difference the baseline showed.
- **Reshape**: the scope or the goal changes, and the gate runs again on the new shape.
- **Drop**: the skill is not written.

For **go** and **reshape**, the outcome and the reason are recorded at the top of
`tests/scenarios/<skill>/baseline.md`.

## Minimum model and effort

When a weaker model would not perform the skill well enough, the skill declares the least capable model
that does, and the effort level when it matters:

- in the frontmatter, under the portable `metadata` key: `minimum-model` and, if needed, `minimum-effort`,
  as free text that names a capability class rather than a dated model ID (for example `Sonnet class or
  above`, `high`);
- in the README, in one line;
- in `SKILL.md`, as a first step: if the running model is below the minimum, say so to the user before
  going on.

Do not use Claude Code's `model` frontmatter key for this: it switches the model on every invocation
instead of declaring a minimum, and other harnesses ignore it.

