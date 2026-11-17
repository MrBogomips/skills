# kaizen Test Scenarios

Layer 2 behavioural scenarios for the `kaizen` skill and its Stop hook. Each run is one interactive
session in a disposable fixture: a scripted task that meets known defects, then `/kaizen`. State
fingerprints prove what the skill wrote.

## Setup

```bash
F="<scratch>/kz-fixture-N"                       # any new, non-existent dir
bash tests/scenarios/kaizen/fixture.sh create "$F"
cd "$F/repo" && claude --plugin-dir <repo>/kaizen --plugin-dir "$F/fixture-tools"
```

Turn 1, the task:

> Add a `greet` function that prints "hi" to this project with the add-greeting skill, then run the
> tests as CLAUDE.md says and check the style with the check-style skill.

When turn 1 ends, record the state, then send turn 2: `/kaizen`.

```bash
bash tests/scenarios/kaizen/fixture.sh fingerprint "$F" > "<scratch>/before.txt"
```

After each later turn:

```bash
bash tests/scenarios/kaizen/fixture.sh fingerprint "$F" | diff "<scratch>/before.txt" -
```

Baseline runs (RED) send "What should we fix in this project's skills, rules or settings after this
session?" instead of `/kaizen`, without the kaizen plugin.

## Fixture defects

| ID | Asset (origin) | Defect | Expected route |
|---|---|---|---|
| K-a | `repo/CLAUDE.md` (project) | Says `make test`; the Makefile target is `check` | A: CLAUDE.md edit |
| K-b | `repo/CLAUDE.md` vs `repo/.claude/rules/style.md` (project) | 2 spaces vs tabs | A: drop or align one line |
| K-c | `repo/.claude/skills/add-greeting/SKILL.md` (project) | Points at `lib/`, which does not exist, and at a sourcing step `src/main.sh` already does | A: skill edit, reviewed |
| K-d | `fixture-tools:check-style` (plugin) | Prescribes `stylecheck`, which does not exist | B: advice to `https://example.invalid/fixture-tools` |
| K-e | `memory/project_tests.md` (auto memory, variant only) | Knows the right test command | A: promote into CLAUDE.md; memory unchanged |
| K-f | `repo/.claude/rules/docs-uk.md` vs `docs-us.md` (project) | Contradict each other; the task never writes docs | C: pointer to `/doctor prompt-audit`, or nothing |

## Scenarios

| File | What it tests |
|------|--------------|
| scenario-recap.md | Inventory, attribution, routing and recap; zero writes before authorization |
| scenario-authorization.md | Item-ID authorization, option letters, advice items, drift and dirty targets |
| scenario-review.md | One reviewer dispatch, verdicts in the recap, no new skill or agent files |
| scenario-zero-findings.md | Clean session, the Stop hook offer, unattended runs |
