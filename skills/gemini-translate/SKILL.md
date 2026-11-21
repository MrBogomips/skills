---
name: gemini-translate
description: >-
  Translates text or files through the Google Gemini API into a target language and register (formal,
  professional, technical, informal), detecting the source language and keeping Markdown, code and placeholders
  intact. Use only when the user asks to translate with Gemini or invokes this skill: every call is billed to
  their Gemini API key.
license: MIT
compatibility: >-
  Needs Python 3.9+ (standard library only), network access, and a Gemini API key in GEMINI_API_KEY or
  GOOGLE_API_KEY. Every call is billed to that key.
argument-hint: "<target-language> [formal|professional|technical|informal] <text-or-file>"
---

# Translation via the Gemini API

`scripts/gemini_translate.py` sends the text to Gemini with a translator's system instruction (from
`references/style-guide.md`, plus `references/languages/<code>.md` for the target when present) and returns the
translation. **Gemini translates, not you**: do not translate, polish or rewrite its output, and do not translate
the text yourself if the script fails.

**Every call costs money on the user's key.** One call per chunk of about 24,000 characters; `--review` doubles
it. Do not re-run "to compare".

## Run it

From the user's request, take the target language (required: ask if missing), the register if they name one, and
the input. Map the user's words to a register: formal/institutional/legal → `formal`, business/e-mail →
`professional`, docs/manual/README → `technical`, casual/marketing/UI → `informal`. Otherwise leave it out and
Gemini infers it.

```bash
python3 scripts/gemini_translate.py --to it -t "Deploy the service, then check the logs."
python3 scripts/gemini_translate.py --to de --register formal -i letter.md -o letter.de.md
```

The script path is relative to this skill's directory.

| Goal | Option |
|---|---|
| Target language (code, locale or name) | `--to it`, `--to pt-BR`, `--to Japanese` |
| Register | `--register formal\|professional\|technical\|informal` (default: inferred) |
| Text, file or stdin | `-t "..."`, `-i file.md`, or pipe it |
| Write to a file | `-o out.md` (default: stdout) |
| Enforce terminology | `--glossary terms.md` (any readable list of `source → target` terms) |
| Higher quality, double cost | `--review` (a second call revises each draft) |
| See the request, spend nothing | `--print-prompt` |
| Another model or thinking level | `--model <id>` (or env `GEMINI_TRANSLATE_MODEL`), `--thinking low\|medium\|high` |

- For a file, write to a new file next to it (`guide.md` → `guide.it.md`) unless the user names one; never
  overwrite the source.
- Use `--glossary` when the user gives terminology or the project has a glossary they point to.
- The default model is `gemini-4-carbon`. Model ids change: on an HTTP 400 about the model, list the models the
  key can use (`GET /v1beta/models`) and pass one with `--model`.

## Results

Stderr shows `source: <code> · register: <register>`, with `(inferred)` when Gemini chose it. Give the user the
translation (or the path) as it is, and mention the register when it was inferred.

| Exit | Meaning | What to do |
|---|---|---|
| 0 | Done | Relay the output. |
| 1 | Error (bad input, HTTP error, unexpected answer) | Report the one-line message. 401/403: key or project access; 402: the project's prepaid credit is used up, top it up in AI Studio; 429: quota, wait. |
| 2 | No API key | Ask the user to set `GEMINI_API_KEY`. |
| 3 | Source is already in the target language | Tell the user; nothing was written. |
| 4 | Code, URLs, placeholders, tags, headings or table rows differ from the source | The translation is in `<output>.unchecked` (or on stdout). Show the user the listed differences. Some are legitimate (a `$1` price that became `1 $`); if every item is, rename the file. Otherwise re-run with `--review`, once. |
