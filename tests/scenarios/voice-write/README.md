# voice-write Test Scenarios

Layer 2 scenarios for the `personal-voice:voice-write` skill. Each describes setup,
invocation, expected behavior and acceptance criteria.

## Setup

```bash
F="<scratch>/pv-fixture-N"                       # any new, non-existent dir
bash tests/scenarios/voice-write/fixture.sh create "$F"
bash tests/scenarios/voice-write/fixture.sh fingerprint "$F" > "<scratch>/before.txt"
```

The fixture builds three places, all with invented content:

| Path | What it is |
|---|---|
| `$F/store` | Global store: tone, `it` and `en` language files, topics `software-engineering`, `cycling`, `family` (personal), two exemplars, two pending observations |
| `$F/project` | Git project whose `.personal-voice/` glossary prefers "rilascio" where the topic file prefers "deploy" |
| `$F/plain` | Directory with no project store, outside git |

`create-empty DIR` builds an empty store instead.

## Running a scenario

**Following the skill** (checks behavior). Give a fresh agent this prompt:

> Read `<repo>/personal-voice/skills/voice-write/SKILL.md` and follow it exactly, as
> if it had been loaded into your context. Read `${user_config.store_dir}` as
> `$F/store` and `${CLAUDE_PLUGIN_ROOT}` as `<repo>/personal-voice`. Your working
> directory is `<working dir of the scenario>`. Do not write or modify any file.
> When you would invoke another skill, write `INVOKE: <skill> — <why>` instead.

then the user message of the scenario. Baseline runs (RED) replace the first
sentence with "My writing-voice profile is stored in `$F/store`".

**Live** (checks triggering). `trigger.sh` runs a headless session with the
plugin loaded from the repository and prints the skills the model invoked:

```bash
bash tests/scenarios/voice-write/trigger.sh "<scratch>/w1" "Draft an email to our client ..."
```

With `--marketplace` (or `PV_TRIGGER_MARKETPLACE=1`) it loads every plugin of the repository, so
collisions with the document skills of other plugins are measured (scenario-triggering.md).
Keep those runs few: each one is a full headless session.

After each run, the store must be unchanged: the voice-write skill never writes.

```bash
bash tests/scenarios/voice-write/fixture.sh fingerprint "$F" | diff "<scratch>/before.txt" -
```

## Scenarios

| File | What it tests |
|------|--------------|
| scenario-email-draft.md | An email draft applies the profile, with audience and exemplar rules |
| scenario-commit-message.md | A commit message does not apply the profile |
| scenario-uncertain-topic.md | An uncertain topic produces one short question |
| scenario-project-glossary.md | The project glossary overrides a topic term |
| scenario-revision-starts-learning.md | A revision after a draft starts learning |
| scenario-session-end.md | A session-end phrase starts the wrap-up |
| scenario-triggering.md | The description triggers for human-facing text in several languages, and not for excluded text |
