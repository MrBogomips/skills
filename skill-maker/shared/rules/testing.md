# Rules for testing a skill

When skill-creator is installed, use it to run evals and tune descriptions (T2, T4). Without it, follow
the manual method each rule gives.

### T1. Baseline first

Before writing a skill, run its task on a fresh agent without the skill and write down how it fails, in
the agent's own words. Then write the least text that fixes those failures, run again, and close the
loopholes the new run shows. Required for a skill that enforces a discipline (rules an agent tends to
dodge: approvals, checks before claiming done). Recommended for the others.

Manual method: one subagent with the task alone, one with the task and the skill; record both outputs
side by side.

Checked by: reviewer

### T2. Compare with a baseline

Judge a skill by comparing runs with it against runs without it: no skill for a new skill, the previous
version for a change. A skill that does not beat its baseline is not finished.

Official source: skill-creator · Checked by: reviewer

### T3. Assertions that discriminate

Write checks that can be judged objectively, and drop those that pass with and without the skill: they
measure nothing. Script the checks a script can make.

Official source: skill-creator · Checked by: reviewer

### T4. Trigger tests

Test the description with realistic requests that should trigger the skill and near misses that should
not. Use substantive tasks: a one-step request is answered directly whatever the description says. Run
each request several times and keep some back to check that tuning did not overfit.

Manual method: a list of about ten requests of each kind, run in fresh sessions, with the result noted
for each.

Official source: skill-creator · Checked by: reviewer

### T5. Pressure for discipline skills

Test a discipline skill under combined pressures (time, effort already spent, an authority asking to skip
the rule, fatigue) and record the excuses the agent gives, word for word. Each excuse gets an answer in
the skill.

Checked by: reviewer

### T6. Small wording tests

To compare two wordings, run each at least five times as single requests against a control with no
guidance, and read every output that a check flags.

Checked by: reviewer

### T7. Test material stays outside the skill

Tests, scenarios, eval workspaces and notes on how the skill was made never live inside the skill
directory. Installers ship that directory, and an agent may read those files as instructions.

Checked by: validator (see P6)

### T8. Findings cite their evidence

Every finding about a skill cites `path:line`. A finding without a citation is dropped.

Checked by: reviewer
