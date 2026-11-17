# voice-learn Test Scenarios

Layer 2 scenarios for the `personal-voice:voice-learn` skill. Each describes setup,
invocation, expected behavior and acceptance criteria.

## Setup

These scenarios reuse the voice-write fixture:

```bash
F="<scratch>/pv-fixture-N"                       # a fresh one per scenario
bash tests/scenarios/voice-write/fixture.sh create "$F"
bash tests/scenarios/voice-write/fixture.sh fingerprint "$F" > "<scratch>/before.txt"
```

The global store starts with two pending observations ("pertanto", evidence 1;
numbered lists, evidence 1) and `last_maintenance: 2026-09-01`. Scenarios that
need a git project without a project store create one:

```bash
mkdir -p "$F/newproj" && (cd "$F/newproj" && git init -q && printf '# Portal\n' > README.md \
    && git add -A && git -c user.name=f -c user.email=f@example.invalid commit -qm init)
```

## Running a scenario

Give a fresh agent this prompt, then the session transcript of the scenario:

> Read `<repo>/personal-voice/skills/voice-learn/SKILL.md` (and the voice-write skill when
> the scenario says so), and the files they point to when they tell you to, and
> follow them exactly, as if loaded into your context. Read
> `${user_config.store_dir}` as `$F/store` and `${CLAUDE_PLUGIN_ROOT}` as
> `<repo>/personal-voice`. Your working directory is `<the scenario's>`. Today
> is `<date>`. Write only inside `$F`. When you would ask the user something,
> write `ASK:` and the question, then use the answer the scenario gives.

Baseline runs (RED) replace the first two sentences with "My voice profile is
in `$F/store`; its format is in `<repo>/personal-voice/shared/store-format.md`".

Check the result with:

```bash
bash tests/scenarios/voice-write/fixture.sh fingerprint "$F" | diff "<scratch>/before.txt" -
```

## Scenarios

| File | What it tests |
|------|--------------|
| scenario-spoken-correction.md | A stated correction becomes an observation for the draft's language |
| scenario-edited-file.md | An edited file is compared with Claude's version |
| scenario-final-without-draft.md | No diff without the draft |
| scenario-proofreading.md | Proofreading the author's text records nothing |
| scenario-mixed-revision.md | Content and style in one revision: only style is recorded |
| scenario-own-texts.md | Bootstrap from the author's own texts, with exemplars |
| scenario-repeated-trait.md | A repeated trait adds evidence instead of a new observation |
| scenario-project-store-init.md | Project store initialization, with the default and with a decline |
| scenario-wrap-up.md | Wrap-up with pending work and with a missed revision |
| scenario-subdirectory.md | A session started in a subdirectory uses the store at the project root |
| scenario-exemplar-privacy.md | Exemplars never carry client or project names |
