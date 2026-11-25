---
name: voice-learn
description: Records the author's tone and lexicon as pending observations in their personal voice profile. Use when the author revises a document or message Claude wrote for them (text for people, not code) - pastes the version they actually sent, edits such a file, or states corrections such as "I never write X", "too formal", "I would never write that" - when the author shares texts they wrote without AI so Claude can learn their style, when asked to learn from a text for the voice profile, or when the author ends a work session in which the personal-voice plugin was used.
allowed-tools: Bash(git rev-parse:*)
---

# Learn the author's voice

Turn the author's revisions, and texts they wrote without AI, into pending
observations about their tone and lexicon. Record without interrupting their
work; never change a rule.

## Hard rules

1. **No draft, no diff.** Learn from a revision only when both versions are
   available: the draft in this session, or both versions given by the author.
   Never reconstruct or guess a draft.
2. **Only the author's changes are preferences.** Changes Claude made (a
   proofread, a rewrite, a translation) never become observations.
3. **Style only.** Record tone, lexicon, punctuation, structure and removed LLM
   habits. Never record corrected facts, figures, dates, names or scope.
4. **Record, never rule.** Write only to `observations.md`, to `exemplars/`
   for own texts, and, after the author confirms, the project-store
   initialization (`project-store-init.md`). Never edit `core.md`, language, topic,
   glossary or content-type files: promotion is the voice-maintain skill's job, with
   the author's approval.
5. **Personal stays global.** Nothing from a personal text ever enters a
   project store.

## Stores

- **Global store**: `${user_config.store_dir}`
- **Project store**: `.personal-voice/` at the project root: the directory
  `git rev-parse --show-toplevel` prints, or the working directory outside git.
  Never create a store in a subdirectory of the repository.
- **Format and routing**: `${CLAUDE_PLUGIN_ROOT}/shared/store-format.md`.
  Read it before your first recording in the session.
- **Project-store setup**: `${CLAUDE_PLUGIN_ROOT}/shared/project-store-init.md`.
  Read it only when a project store has to be created.

If the global store path above is empty or still contains the text
`user_config.store_dir`, tell the author to set **Voice store directory** in
`/config` and write nothing.

Use the Glob, Read, Write and Edit tools on store files, not shell commands:
the allow rules the plugin documents cover those tools, so recording raises
no permission prompt. The one command this skill runs is `git rev-parse`
(the project root, and the exclude file at project-store setup), which it
pre-approves.

## Workflow

1. **Identify the source.**
   - A revision of text Claude wrote: a pasted final version, a file the author
     edited, or corrections stated in the conversation → `references/revision.md`
   - Texts the author wrote without AI → `references/own-texts.md`
   - The end of the work session → `references/wrap-up.md`
   - Invoked with no source in sight → ask the author which text to learn from.
2. **Extract traits.** One trait per observation: a single, specific habit
   the author showed, stated in English, with the verbatim excerpts.
3. **Route** each trait with the Routing section of the store format.
4. **Record** as `references/recording.md` describes: merge with pending
   observations and existing rules, write, then show the one-line notice and,
   when a threshold is reached, the one-line maintenance suggestion.
5. **Carry on** with whatever else the author asked in the same message.

Do not ask before recording, and do not discuss the observations unless the
author asks.

## Red flags

| Thought | Reality |
|---|---|
| "I remember roughly what my draft said" | Not in the session, not available. Ask for it. |
| "My proofreading fixes show what they like" | They show what Claude likes. Record nothing. |
| "The new date is part of how they write" | It is content. Skip it. |
| "This matches a rule, so I'll bump the rule" | Record a reinforcing observation; maintenance updates the rule. |
| "I'll ask whether to record this" | Record without asking; the notice is enough. |
| "It's a family message, but we're in the client's repo" | Personal goes global. Always. |
