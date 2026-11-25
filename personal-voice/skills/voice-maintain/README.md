---
summary: Reviews your voice profile when you ask, proposes which observations become rules and what to merge, settle or remove, and changes only the items you name.
---

# voice-maintain

`voice-maintain` reviews your voice profile when you ask and lists numbered proposals backed by
evidence: observations ready to become rules, overlapping or contradictory rules, and rules that
are stale or add nothing. It changes only the items you name, and it can also switch a project's
voice store between personal and versioned.

## Why

A profile left to grow on its own would turn one-off fixes into rules, keep conflicting rules, and
lengthen with every session. `voice-maintain` is the only place where rules change, and every
update is up to you.

- An observation is proposed as a rule once it appears in two independent texts; a single
  occurrence is proposed only if you ask explicitly.
- Nothing changes until you name the items. A reply like "ok" does not count as approval.
- Personal material never moves into a project store, no matter what you approve.

## Use cases

### Turn a repeated fix into a rule

**Context:** You removed "therefore" from two different texts, and the pending observation stores both as evidence.

**Action:** Say "review my voice profile", then reply with that item's number.

**Result:** The rule is added to `languages/en.md` in your global store, and the observation is removed from `observations.md`.

### Share a project glossary with your team

**Context:** The project's `.personal-voice/` folder is personal, so Git ignores it.

**Action:** Say "I'd like to share the project glossary with the team", review what versioning entails, and confirm.

**Result:** `git status` shows `.personal-voice/` as untracked and ready for you to commit; nothing is committed automatically.

## Usage

`personal-voice:voice-maintain` takes no arguments and runs only when you ask ("review my voice
profile") or accept a suggestion from [`voice-learn`](../voice-learn/README.md). It returns a
numbered list such as:

```text
1. PROMOTE → global › languages/en.md › Avoid
   [en] Avoid "therefore"; drop it or restructure the sentence. (evidence: 2)
   Evidence: 2026-09-18 meeting follow-up to the team · "Therefore, we postpone…" → "We postpone…"
             2026-09-25 retrospective reminder to the team · "I never use 'therefore'"
```

Reply with the items to apply (for example, `1, 3 remove, 2 keep A`), or `all` to apply every item
that requires no decision. For a promotion, you can also write `1 edit: <new text>` or
`1 scope: project`. Items you do not name remain unchanged.

## Inputs and outputs

`voice-maintain` reads the global store and the current project's `.personal-voice/` folder. For
the items you name, it writes rules to the profile files and removes the observations they came
from. Switching a project store between personal and versioned edits the repository's
`.git/info/exclude`, never `.gitignore`. See [the store format](../../shared/store-format.md) for
details on the files.

## Requirements

The `personal-voice` plugin with its `store_dir` setting configured. If `store_dir` is not set,
`voice-maintain` explains how to configure it and stops.

## Limitations

- `voice-maintain` never runs on its own.
- It operates only on the current project's store. To scope a rule to another project, run it in
  that project.
- It does not commit changes. After switching a store to versioned, commit the files yourself;
  files already committed remain in Git history when you switch back to personal.