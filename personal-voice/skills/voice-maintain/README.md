---
summary: Reviews your voice profile when you ask, proposes which observations become rules and what to merge, settle or remove, and changes only the items you name.
---

# voice-maintain

`voice-maintain` reviews your voice profile when you ask. It lists numbered proposals with their
evidence: observations ready to become rules, rules that overlap or contradict each other, rules
that are stale or add nothing. It changes only the items you name. It also switches a project's
voice store between personal and versioned.

## Why

A profile that grew on its own would turn one-off fixes into rules, keep rules that contradict each
other and get longer with every session. `voice-maintain` is the one place where rules change, and
every change is yours.

- An observation is proposed as a rule once two independent texts show it; a single one only on
  your explicit request.
- Nothing changes until you name the items. A reply like "ok" is not an approval.
- Personal material never moves into a project store, whatever you approve.

## Use cases

### Turn a repeated fix into a rule

**Context:** You dropped "pertanto" in two different texts, and the observation waits with both as evidence.

**Action:** Ask "review my voice profile", then reply with the number of that item.

**Result:** `languages/it.md` in your global store holds the rule, and the observation is gone from `observations.md`.

### Share a project glossary with your team

**Context:** The project's `.personal-voice/` folder is personal: git ignores it.

**Action:** Say "I'd like to share the project glossary with the team", read what versioning implies, and confirm.

**Result:** `git status` shows `.personal-voice/` as untracked, ready for you to commit; nothing is committed for you.

## Usage

`personal-voice:voice-maintain` runs only when you ask ("review my voice profile") or accept the
suggestion from [`voice-learn`](../voice-learn/README.md). It takes no arguments. It answers with a
numbered list such as:

```text
1. PROMOTE → global › languages/it.md › Avoid
   [it] Avoid "pertanto"; drop it or restructure the sentence. (evidence: 2)
   Evidence: 2026-09-18 meeting follow-up to the team · "Pertanto, rinviamo…" → "Rinviamo…"
             2026-09-25 retrospective reminder to the team · "non uso mai 'pertanto'"
```

Reply with the items to apply, for example `1, 3 remove, 2 keep A`, or `all` for every item that
needs no decision. For a promotion you can also write `1 edit: <new text>` or `1 scope: project`.
Items you do not name stay as they are.

## Inputs and outputs

It reads the global store and the current project's `.personal-voice/`. On the items you name, it
writes rules to the profile files and removes the observations they came from. Switching a store between personal and versioned
edits the repository's `.git/info/exclude`, never `.gitignore`. The files are described in
[the store format](../../shared/store-format.md).

## Requirements

The `personal-voice` plugin, with its `store_dir` setting. Until `store_dir` is set, it tells you
how to set it and stops.

## Limitations

- It never starts on its own.
- It reaches only the current project's store: to scope a rule to another project, run it in that
  project.
- It does not commit. After a switch to versioned you commit the files yourself; files already
  committed stay in the git history when you switch back to personal.
