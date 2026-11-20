# skill-readme Test Scenarios

Manual scenarios for the `skill-readme` skill of the `skill-maker` plugin and its `readme-reviewer`
agent. The scripts have automated tests (`tests/test_skill_maker_*.py`); these scenarios cover what
needs a live session: reading sources, drafting, the fact review.

## Setup

```bash
cd <repo> && claude --plugin-dir ./skill-maker
git status --short > "<scratch>/before.txt"       # the runs must leave the repository untouched
```

Targets used below: `personal-voice/` (a plugin in a subfolder, with a README that predates the
contract) and, in a checkout of `MrBogomips/eng-artifacts`, `skills/erd/` (a skill with a README, a
`summary:` and custom sections).

After each scenario:

```bash
git status --short | diff "<scratch>/before.txt" -     # must print nothing
```
