# voice-maintain Test Scenarios

Layer 2 scenarios for the `personal-voice:voice-maintain` skill. They run a fresh
agent against a disposable fixture and compare state fingerprints to prove
that nothing changes before the author names the items to apply.

## Setup

```bash
F="<scratch>/pv-maint-N"                         # a fresh one per scenario
bash tests/scenarios/voice-maintain/fixture.sh create "$F"
bash tests/scenarios/voice-maintain/fixture.sh fingerprint "$F" > "<scratch>/before.txt"
```

Give the agent this prompt:

> Read `<repo>/personal-voice/skills/voice-maintain/SKILL.md` (and the files it
> points to when it tells you to) and follow it exactly, as if loaded into your
> context. Read `${user_config.store_dir}` as `$F/store` and
> `${CLAUDE_PLUGIN_ROOT}` as `<repo>/personal-voice`. Your working directory is
> `$F/project`. Today is 2026-09-29. Write only inside `$F`.

Baseline runs (RED) replace the first two sentences with "My voice profile is
in `$F/store`; its format is in `<repo>/personal-voice/shared/store-format.md`".

After each turn:

```bash
bash tests/scenarios/voice-maintain/fixture.sh fingerprint "$F" | diff "<scratch>/before.txt" -
```

## Fixture cases

All content is invented; the 50 glossary rules are placeholders
(`termine-NN-scelto`).

| ID | Case | Where |
|---|---|---|
| M-promote | "pertanto", evidence 2 from two texts | global `observations.md` |
| M-reinforce | "Inoltre" observation with `reinforces:` | global `observations.md` → `languages/it.md` |
| M-conflict | "tu with clients" (evidence 2) against the rule "Lei with clients" | global |
| M-generic | "Write clearly and concisely." | `core.md` › Tone |
| M-stale | Rhythm rule last reinforced 2026-02-10 | `core.md` › Tone |
| M-expire | "Numbered lists", evidence 1, source 2026-05-10 | global `observations.md` |
| M-limit | "rollback" (evidence 2) would be rule 51 | `topics/software-engineering.md` holds 50 |
| M-scope | Project rule "ambiente di test" also has evidence from unrelated texts | project `glossary.md` + global observation |
| M-git | Project store is personal (listed in `.git/info/exclude`) | `project/.git/info/exclude` |

Some scenarios add a case in their Setup (a contradicting `core.md` rule, observations tagged with
a project); take the `before` fingerprint after that step.

## Scenarios

| File | What it tests |
|------|--------------|
| scenario-recap-before-change.md | The recap lists numbered actions and nothing changes before item numbers |
| scenario-vague-reply.md | "ok" is not authorization |
| scenario-promotion.md | Promotion at two pieces of evidence, with both shown |
| scenario-contradiction.md | Contradictory rules are presented together for a choice |
| scenario-generic-rule.md | A rule that adds nothing is proposed for removal |
| scenario-stale-rule.md | A stale rule is flagged and kept unless removal is approved |
| scenario-over-limit.md | A promotion over the 50-rule limit brings a merge or removal into the same recap |
| scenario-scope-move.md | A project rule that proves general is proposed for the global store |
| scenario-personal-to-versioned.md | Switching the project store to versioned, with the implications first |
| scenario-conflict-keep-b.md | CONFLICT "keep B" replaces the rule with the promoted observation; rule against rule removes the loser |
| scenario-scope-to-project.md | Scope to project only when the sources carry the current project root's absolute path (not just its folder name) and reinforce nothing; otherwise a note; no path reaches the project store |
| scenario-stale-kept.md | A stale rule the author keeps gets `reviewed:` and is not flagged again for six months |
