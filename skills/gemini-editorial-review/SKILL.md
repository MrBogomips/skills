---
name: gemini-editorial-review
description: >-
  Revises a text or file through the Google Gemini API (Gemini 4 Neon or above) in the language it is written
  in, removing the marks of machine-written prose, fixing structure, register and calques, and applying the
  editorial rules found in AGENTS.md, CLAUDE.md and the files they cite. Use only when the user asks for an
  editorial review with Gemini or invokes this skill: every call is billed to their Gemini API key.
license: MIT
compatibility: >-
  Needs Python 3.9+ (standard library only), network access, and a Gemini API key in GEMINI_API_KEY or
  GOOGLE_API_KEY. Every call is billed to that key.
argument-hint: "[technical|marketing|professional|essay|blog|creative] <text-or-file>"
---

# Editorial review via the Gemini API

`scripts/gemini_editorial_review.py` sends the text to Gemini with an editor's system instruction (from
`references/editorial-guide.md`, plus `references/languages/<code>.md` for the text's language when present) and
returns the revised text in the same language, with a short summary of the changes. **Gemini revises, not you**:
the point is a second model that does not share your writing habits. Do not polish or rewrite its output, and do
not revise the text yourself if the script fails.

**Every call costs money on the user's key**: one call per document. Do not re-run "to compare".

## 1. Before the call

1. **Profile and audience.** Map the text to a profile: docs, README, manual → `technical`; landing or product
   page, pitch → `marketing`; e-mail, report, memo, proposal → `professional`; essay, article, non-fiction
   chapter → `essay`; personal post or project diary → `blog`; fiction, dialogue, screenplay → `creative`. If it
   is clear, pass `--profile`; otherwise leave it out and Gemini infers it. Pass `--audience` when the user or
   the context says who reads the text. Ask the user only when the purpose or the readers are genuinely
   ambiguous and would change the result: Gemini cannot ask.
2. **House rules from the context.** Gemini does not see your instructions, so collect the editorial rules that
   apply to this text:
   - Read the project's `AGENTS.md` / `CLAUDE.md` (the root one and any nested one on the path to the file) and
     the user-level instructions you have loaded.
   - Keep only rules about writing: style, tone, register, terminology, language and spelling, document
     formats, forbidden words or content (for example "no AI attribution"). Ignore rules about code, tools,
     tests or version control.
   - When those files **cite** a style guide, glossary or writing-rules file (by path or link), pass that file as
     it is with `--rules <path>` (`--glossary <path>` for a pure term list). Read it first to confirm it is
     about writing.
   - Copy rules written inline, verbatim, into one file in your temporary or scratch directory and pass it with
     `--rules`. Pass the most general rules first and the most specific last: later files win on conflicts.
   - Tell the user which sources you passed. If there are none, say so and go on.
3. **Output path.** For a file, write to a new file next to it (`guide.md` → `guide.reviewed.md`) unless the
   user names one. The script refuses to overwrite the source.

## 2. Run it

```bash
python3 scripts/gemini_editorial_review.py -i draft.md -o draft.reviewed.md
python3 scripts/gemini_editorial_review.py --profile technical --rules /tmp/house-rules.md \
  --rules docs/style-guide.md -i README.md -o README.reviewed.md
```

The script path is relative to this skill's directory. Several files: one call per file, one file at a time.

| Goal | Option |
|---|---|
| Text, file or stdin | `-t "..."`, `-i file.md`, or pipe it |
| Write to a file | `-o out.md` (default: stdout) |
| Kind of text | `--profile technical\|marketing\|professional\|essay\|blog\|creative` (default: inferred) |
| Readers | `--audience "CTOs of small firms"` |
| House rules | `--rules file.md` (repeatable, later files win) |
| Terms to keep | `--glossary terms.md` |
| Language notes | `--lang it` (default: detected; notes ship for `it` and `en`) |
| See the request, spend nothing | `--print-prompt` |
| Another model or thinking level | `--model gemini-4-argon` (or env `GEMINI_EDITORIAL_MODEL`), `--thinking low\|medium\|high` (default `high`) |

- The default model is `gemini-4-neon`; `gemini-4-argon` is the alternative. A Gemini 4 model below Neon runs
  with a warning: use one only if the user asks. Model ids change: on an HTTP 400 about the model, list the
  models the key can use (`GET /v1beta/models`) and pass one with `--model`.
- Texts over 150,000 characters are refused: split the document by chapter or section and review each part.

## 3. Results

Stderr shows `language: <code> · profile: <profile>`, with `(inferred)` when Gemini chose it, then the summary
of changes as `- ` lines.

- **Default**: give the user the revised text (or the path) as it is, then the summary lines and the house-rule
  sources used.
- **Clean mode** (the user asks for the final file only, or "no notes"): give only the text or the path.

| Exit | Meaning | What to do |
|---|---|---|
| 0 | Done | Relay the output as above. |
| 1 | Error (bad input, too long, HTTP error, unexpected answer) | Report the one-line message. 401/403: key or project access; 402: the project's prepaid credit is used up, the user must top it up in AI Studio; 429: quota, wait. |
| 2 | No API key | Ask the user to set `GEMINI_API_KEY`. |
| 4 | Code blocks, inline code, URLs, placeholders, tags or the frontmatter differ from the source | The revision is in `<output>.unchecked` (or on stdout). Show the user the listed differences; if every item is legitimate, rename the file. Do not re-run without the user's consent. |
