---
name: gemini-editorial-review
description: >-
  Revises a text or file with Google Gemini (Gemini 4 Neon or above), through the local agy CLI or the Gemini
  API, in the language it is written in: removes the marks of machine-written prose, fixes structure, register
  and calques, and applies the editorial rules found in AGENTS.md, CLAUDE.md and the files they cite. Use only
  when the user asks for an editorial review with Gemini or agy, invokes this skill, or asks to configure it.
license: MIT
compatibility: >-
  Needs Python 3.9+ (standard library only) and either the agy CLI (Google Antigravity) logged in, or network
  access and a Gemini API key in GEMINI_API_KEY or GOOGLE_API_KEY (billed to that key).
argument-hint: "[technical|marketing|professional|essay|blog|creative] <text-or-file> | config"
metadata:
  minimum-model: Sonnet class or above
---

# Editorial review with Gemini

Needs a model of Sonnet class or above. On a less capable model, tell the user before going on.

`scripts/gemini_editorial_review.py` sends the text to Gemini with an editor's instruction (from
`references/editorial-guide.md`, plus `references/languages/<code>.md` for the text's language when present) and
returns the revised text in the same language, with a short summary of the changes. **Gemini revises, not you**:
the point is a second model that does not share your writing habits. Do not polish or rewrite its output, and do
not revise the text yourself if the script fails.

Two backends reach the same model with the same instruction:

- `agy`: one turn of the local Antigravity CLI, on the user's agy login and quota, with no tools.
- `api`: the Gemini API with `GEMINI_API_KEY`; every call is billed to that key.

The `backend` setting picks one; `auto`, the default, uses agy when it is installed and the API otherwise. One
call per document either way: do not re-run "to compare".

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

Launch it directly: do not check first whether agy or the key works, the script reports it. A long document can
take several minutes: run it in the background if your harness can.

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
| Backend for this run | `--via agy\|api` (default: the `backend` setting) |
| Kind of text | `--profile technical\|marketing\|professional\|essay\|blog\|creative` (default: inferred) |
| Readers | `--audience "CTOs of small firms"` |
| House rules | `--rules file.md` (repeatable, later files win) |
| Terms to keep | `--glossary terms.md` |
| Language notes | `--lang it` (default: detected; notes ship for `it` and `en`) |
| See what would be sent, spend nothing | `--print-prompt` |
| Another model | `--model <id>` or env `GEMINI_EDITORIAL_MODEL`; `--thinking low\|medium\|high` (api only) |

- Default models: `gemini-4-neon-high` with agy (ids from `agy models`; the suffix is the reasoning level),
  `gemini-4-neon` with the API. Argon is the alternative. A model below Neon, older than Gemini 4 or not a
  Gemini runs with a warning: use one only if the user asks.
- Texts over 150,000 characters are refused: split the document by chapter or section and review each part.

## 3. Settings

The user asks to configure the skill ("use the API by default", "in this project use Argon"): change the
settings only with the script, never by editing the files.

```bash
python3 scripts/gemini_editorial_review.py config                          # values, where each comes from, file paths
python3 scripts/gemini_editorial_review.py config set backend api           # user default
python3 scripts/gemini_editorial_review.py config set agy_model gemini-4-argon-high --project
python3 scripts/gemini_editorial_review.py config unset backend --project
```

Keys: `backend` (`auto|agy|api`), `agy_model`, `api_model`, `api_thinking`, `timeout` (seconds). Precedence:
default < user file < project file (`.gemini-editorial-review.json` at the repository root) <
`GEMINI_EDITORIAL_BACKEND` / `GEMINI_EDITORIAL_MODEL` < flags. Show the user the output of `config` after a
change. A project file is part of the repository: say so, and let the user decide whether to commit it.

## 4. Results

Stderr shows `backend: <backend> · model: <id>`, then `language: <code> · profile: <profile>`, with `(inferred)`
when Gemini chose it, then the summary of changes as `- ` lines.

- **Default**: give the user the revised text (or the path) as it is, then the summary lines and the house-rule
  sources used.
- **Clean mode** (the user asks for the final file only, or "no notes"): give only the text or the path.

| Exit | Meaning | What to do |
|---|---|---|
| 0 | Done | Relay the output as above. |
| 1 | Error (bad input or setting, too long, HTTP error, failed agy turn, unexpected answer) | Report the one-line message. API: 401/403 key or project access; 402 prepaid credit used up (top up in AI Studio); 429 quota, wait. agy: the trace and log path is in the message. |
| 2 | Backend unavailable: no API key, agy not installed, or agy could not start a turn | Report it. Offer the other backend with `--via` only if the user agrees: the API bills their key. Repairing agy (for example an MCP server that never connects) is the user's decision. |
| 4 | Code blocks, inline code, URLs, placeholders, tags or the frontmatter differ from the source | The revision is in `<output>.unchecked` (or on stdout). Show the user the listed differences; if every item is legitimate, rename the file. Do not re-run without the user's consent. |
