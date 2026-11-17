# Scenario: Bootstrap from the author's own texts

## Setup
Fixture created. Working directory: `$F/plain`.

## Invocation
"Here are three emails I wrote to clients myself, no AI involved. Learn my style from them." followed by three short client emails that all open with "Short version:" and close with "Talk soon," and the author's first name.

## Expected Behavior
- Accepts the texts as own texts, labels each one
- Records one observation per shared trait, with one source per email
- Keeps short excerpts as exemplars in the global store

## Acceptance Criteria
- [ ] Observations for the opener and for the closing, each with evidence 3 and source kind `own text`
- [ ] New files `exemplars/<topic>.en.<nn>.md`, each with `topic`, `language: en`, `audience: clients`, `source` and `words` in the frontmatter, at most 300 words, wording unchanged
- [ ] No exemplar in any project store; no rule file changes
- [ ] The exemplars for that topic and language stay at five or fewer
- [ ] One notice line naming the observations and the exemplars

## Edge Cases
- Texts to a relative → global store only, topic marked personal
- Unclear whether the texts were written with AI → one question before recording
