---
summary: Records how you write, from your revisions of Claude's drafts and from texts you wrote yourself, as observations that wait for your review in your voice profile.
---

# voice-learn

`voice-learn` notes how you write. It compares Claude's drafts with the versions you actually used,
takes corrections such as "I never write 'inoltre'", and reads texts you wrote without AI. Each
habit becomes an observation that waits for your review in your voice profile: it records without
asking and never changes a rule.

## Why

The changes you make to a draft show your voice better than any description, and they are lost as
soon as you send the text. `voice-learn` keeps them without interrupting your work: one line tells
you what it recorded.

- It records only style: tone, words, punctuation, structure, and LLM habits you remove. Never
  corrected facts, figures, dates, names or scope.
- Only your changes count. Claude's own edits of your text, such as a proofread or a rewrite, never
  become your preferences.
- Nothing learned from a personal text enters a project store.

## Use cases

### Start the profile from texts you wrote

**Context:** Your profile is empty and you have emails you wrote without AI.

**Action:** Paste them with "Here are three emails I wrote to clients myself, no AI involved. Learn my style from them."

**Result:** One observation for each habit the emails share, with all three as evidence, and short excerpts kept under `exemplars/` in your global store.

### Correct a word once

**Context:** Claude's note to your colleagues says "altresì", a word you never use.

**Action:** Reply "Non scrivere 'altresì', non lo uso mai."

**Result:** The corrected text, and one line naming the new observation and the profile file it is meant for.

### Learn from a file you edited

**Context:** Claude wrote `q3-summary.md` for your team and you changed it in your editor.

**Action:** Say "I edited q3-summary.md, have a look."

**Result:** Observations for your style changes, such as the closing you chose; the file itself is not modified.

## Usage

Claude loads `personal-voice:voice-learn` on its own when you revise text it wrote for you in the
session: paste the version you sent, edit the file and say so, or state the correction. You can also
give it texts you wrote without AI, pasted or as files, and ask it to learn your style from them.
It takes no arguments.

After recording you see one line:

```text
Voice profile: recorded 2 observations — global › languages/it.md (new), project › glossary.md (+1 evidence).
```

When enough observations are pending, a second line suggests running
[`voice-maintain`](../voice-maintain/README.md). When you close the session, it records any revision
it missed and gives a recap of at most two lines.

The first time a project term comes up in a project, it offers to create the project store and
explains what keeping it personal or versioning it implies.

## Inputs and outputs

- **Needs:** for a revision, both the draft and your version: the draft from this session, or both
  versions given by you. For your own texts, that you wrote them without AI.
- **Leaves:** observations in `observations.md`, in the global store or in the project's
  `.personal-voice/`; excerpts of your own texts in `exemplars/` of the global store; a new `.personal-voice/` folder, only after you
  confirm.

The files are described in [the store format](../../shared/store-format.md).

## Requirements

The `personal-voice` plugin, with its `store_dir` setting. Until `store_dir` is set, it tells you
how to set it and writes nothing.

## Limitations

- It learns only within a Claude Code session. Revisions you make after the session, such as edits
  to an email you already sent, are not captured unless you provide both versions.
- Without the draft it compares nothing and records nothing from that text.
- A text that started from an AI draft is a revision, not a text of your own.
- A change that could be style or content is skipped.
- Exemplars carry no client or project names: a text with no passage free of them gives observations
  but no exemplar.
