# Learning from a revision

A revision is the author's change to human-facing text Claude wrote. It comes
in three forms:

| Form | The draft | The final |
|---|---|---|
| Pasted final version | Claude's text earlier in this session | The pasted text |
| Edited file | The content Claude last wrote to the file in this session | The file as it is on disk now: read it in full, even when a change notice shows only some lines |
| Spoken correction | The passage of Claude's text the correction is about | The correction itself ("don't write 'inoltre'", "too formal", "I'd say 'a presto'") |

## 1. Check that the draft is available

Find the draft in this session. If it is not there, and the author has not
given both versions:

- Do not compare and do not record anything from this text.
- Say that learning from a revision needs the draft, and ask for it.
- If the author says they wrote the final text themselves, without starting
  from an AI draft, offer to learn from it as their own text
  (`own-texts.md`). A final they edited from an AI draft is not own text.

## 2. Establish who wrote each version

Only changes the author made are preferences.

- Claude drafted, the author revised → the author's changes are preferences.
- The author wrote, Claude edited (proofreading, rewording, translating) →
  Claude's changes are not preferences. Record nothing from them.
- The author rejects one of Claude's edits to their text ("no, keep my 'e
  poi'") → that rejection is a spoken correction and is a preference.

## 3. Separate style from content

Compare the two versions change by change.

| Record (style) | Skip (content) |
|---|---|
| Word choice among synonyms, jargon, borrowed expressions | Corrected facts, figures, dates, times, names |
| Register, address form (tu/Lei, du/Sie), greetings and closings | Added or removed information |
| Sentence length, rhythm, punctuation habits | Changed scope, commitments or recipients |
| Structure: order of paragraphs, lists vs prose, headings | Reordering required by the content |
| Removed LLM habits: stock openers and closers, hedges, rule-of-three lists, summaries | Typo and grammar fixes |

When one change mixes both ("martedì 14" → "mercoledì 15" inside a rewritten
sentence), record only the style part. When you cannot tell whether a change
is style or content, skip it.

## 4. State each trait

- One habit per observation, in English, at the level the change supports:
  "Close with a short direct offer of help instead of a stock formula", not
  "prefers informal writing".
- Quote the before and after excerpts verbatim.
- Take language, topic and audience from the draft's request and context,
  and tag the source with the project when the session is in one.
- A habit repeated several times in one text is one trait with one source.
- Skip traits the model shows anyway, such as "writes clearly".

Then go back to the workflow in `SKILL.md`: route and record.
