---
summary: Records how you write, from your revisions of Claude's drafts and from texts you wrote yourself, as observations that wait for your review in your voice profile.
---

# voice-learn

`voice-learn` records how you write. It compares Claude's drafts against the versions you actually used, notes direct corrections such as "I never write 'inoltre'", and reads texts you wrote without AI. Each habit becomes an observation waiting for your review in your voice profile. It records without asking and never changes a rule.

## Why

The edits you make to a draft show your voice better than any description, yet they are lost as soon as you send the text. `voice-learn` preserves them without interrupting your work, reporting what it recorded in a single line.

- It records only style (tone, word choice, punctuation, structure, and LLM habits you remove), never corrected facts, figures, dates, names, or scope.
- Only your edits count. Changes Claude makes to your text, such as proofreading or rewriting it, never become your preferences.
- Nothing learned from a personal text enters a project store.

## Use cases

### Start the profile from texts you wrote

**Context:** Your profile is empty, and you have emails you wrote without AI.

**Action:** Paste them and write: "Here are three emails I wrote to clients myself, no AI involved. Learn my style from them."

**Result:** One observation for each habit the emails share, citing all three as evidence, plus short excerpts saved under `exemplars/` in your global store.

### Correct a word once

**Context:** Claude's note to your colleagues includes "altresì", a word you never use.

**Action:** Reply: "Non scrivere 'altresì', non lo uso mai."

**Result:** The corrected text, followed by a single line naming the new observation and its target profile file.

### Learn from a file you edited

**Context:** Claude wrote `q3-summary.md` for your team, and you revised it in your editor.

**Action:** Tell Claude: "I edited q3-summary.md, have a look."

**Result:** Observations capturing your style changes, such as the closing you chose, without modifying the file itself.

## Usage

Claude loads `personal-voice:voice-learn` automatically when you revise text it wrote during the session: paste the version you sent, edit the file and let Claude know, or state a correction directly. You can also share texts you wrote without AI (pasted or as files) and ask Claude to learn your style from them. The skill takes no arguments.

After recording, you see a single line:

```text
Voice profile: recorded 2 observations — global › languages/it.md (new), project › glossary.md (+1 evidence).
```

When enough observations are pending, a second line suggests running [`voice-maintain`](../voice-maintain/README.md). When you close the session, `voice-learn` records any revision it missed and prints a recap of at most two lines.

The first time a project-specific term comes up, the skill offers to create a project store and explains what keeping it personal or versioning it entails.

## Inputs and outputs

- **Needs:** For a revision, both the draft and your version (with the draft from this session, or both versions provided by you). For your own texts, material you wrote without AI.
- **Leaves:** Observations in `observations.md` (in the global store or in the project's `.personal-voice/`), excerpts of your own texts under `exemplars/` in the global store, and a new `.personal-voice/` folder created only after you confirm.

These files are described in [the store format](../../shared/store-format.md).

## Requirements

The `personal-voice` plugin with `store_dir` configured. Until `store_dir` is set, `voice-learn` explains how to configure it and writes nothing.

## Limitations

- `voice-learn` learns only within a Claude Code session. Revisions you make afterward, such as edits to an email you already sent, are not captured unless you provide both versions.
- Without the original draft, `voice-learn` makes no comparison and records nothing from that text.
- A text that started as an AI draft counts as a revision, not as text you wrote yourself.
- Any edit that could be either style or content is skipped.
- Exemplars never include client or project names. If a text has no passage free of them, `voice-learn` records observations but saves no exemplar.