# Rules for the value of a skill

Whether a skill should exist at all. A skill competes with frontier models and harnesses that improve on
their own: one that copies a capability they already have costs context and maintenance and is quietly
overtaken. A skill therefore distils a method, a process, a discipline or an integration of tools the
user owns, never a capability the model or the harness already has.

A repository may keep its own value gate (for example a `DESIGN.md`); where it does, it wins (see the
precedence in [README.md](README.md)).

### V1. Not native

Neither the model, asked in one plain request, nor the harness (built-in features, settings, official
skills and plugins) already does the job well. Evidence: the baseline run of rule T1 shows a failure that
repeats, and the official documentation shows no equivalent feature. A skill whose baseline does not fail
is not written; an existing one is a retire candidate.

Checked by: reviewer

### V2. Durable value

The value lies in a method, a process, a discipline or an integration, not in a capability gap that
models are closing (knowing current facts, writing better, judging risk). Ask: if the next model were
twice as good, would the skill still be needed?

Checked by: reviewer

### V3. On top of native, not beside it

Where the harness has a mechanism (permission rules, hooks, memory, plan mode, settings, built-in
commands), the skill reads, configures or drives it. It does not build a parallel one.

Checked by: reviewer

### V4. Thin

The skill holds only what the baseline lacks; whatever the model does unaided is cut. A difference that
a request of five to seven meaningful words already conveys needs no skill.

A longer request is the exception: a **shortcut skill** stands for the ten or twenty words a user would
otherwise type every time (a report format, a structure of questions, labels, limits). It is invoked by
the human, by name or by a few exact trigger words that its description names (or, in Claude Code, with
`disable-model-invocation: true`), and its body holds only that standard behaviour.

Checked by: reviewer

### V5. Revisited

The value is judged again at every change of the official sources (see
[`../official-baseline.json`](../official-baseline.json)) and at major harness releases. A skill that
native features have absorbed, or that is never used for what it costs in context, is a retire
candidate. In Claude Code, `/skill-doctor` (v2.1.252 or later) reports what each skill costs in context
and how often it is used: read it before a retire verdict when it is available. `/doctor prompt-audit`
(v2.1.283 or later) flags skills and instruction files written for older models or pointing to files and
commands that no longer exist.

Official source: docs-skills, docs-memory · Checked by: reviewer

### V6. Minimum model and effort are declared

When a weaker model would not perform the skill well enough, the skill declares the least capable model
that does, and the effort when it matters: `minimum-model` and `minimum-effort` under the portable
`metadata` key, as a capability class rather than a dated model ID (`Sonnet class or above`, `high`);
one line in the README; and a first step in `SKILL.md` that tells the user when the running model is
below the minimum. Claude Code's `model` key does not declare a minimum: it switches the model on every
invocation, and other harnesses ignore it.

Checked by: reviewer
