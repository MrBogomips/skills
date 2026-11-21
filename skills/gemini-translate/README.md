---
summary: Translates text and Markdown files with Google Gemini into any language, in the register you choose, keeping code, links and placeholders intact.
---

# gemini-translate

`gemini-translate` translates text and Markdown files through the Google Gemini API into the language you specify, in a formal, professional, technical, or informal register. It detects the source language, leaves code, URLs, and placeholders untouched, and aims for text that reads as if written in the target language. It uses your own API key.

## Why

Translations from a general-purpose agent often read like translations, with borrowed syntax, literal idioms, and a drifting form of address. This skill delegates the work to Gemini, which ranks among the strongest models in independent machine-translation evaluations. It sends a translator's brief with register profiles and per-language notes, then automatically checks that code, links, placeholders, headings, and tables come through unchanged. Because every call is billed to your key, the skill runs only when you ask for a Gemini translation.

## Installation

```bash
npx skills add MrBogomips/skills --skill gemini-translate
```

This installs the same skill included in the `skills` plugin, under the name `gemini-translate` instead of `skills:gemini-translate`.

## Usage

Set `GEMINI_API_KEY`, then ask your agent to translate with Gemini, specifying the target language and an optional register (`/skills:gemini-translate` in Claude Code with the plugin). The agent runs the bundled script from the skill's folder:

```bash
python3 scripts/gemini_translate.py --to it --register technical -i README.md -o README.it.md
```

If you omit `--register`, Gemini infers the register and the script reports it. Other options:

- `--glossary`: enforces your terminology.
- `--review`: adds a revision pass at double the cost.
- `--print-prompt`: shows the request without making a call.

See [SKILL.md](SKILL.md) for all options.

## Inputs and outputs

- Input comes from `-t` (text), `-i` (file), or stdin.
- Output is written to the file specified with `-o`, or to stdout if `-o` is omitted.
- The detected source language and register go to stderr.
- If code, URLs, placeholders, tags, headings, or table rows differ from the source, nothing is written to `-o`. Instead, the translation is saved to `<output>.unchecked` and the differences are listed.

## Requirements

- A Gemini API key set in `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
- Python 3.9 or later (standard library only) and network access.
- The default model is `gemini-4-carbon`; pass `--model <id>` or set `GEMINI_TRANSLATE_MODEL` to use another.

## Limitations

- Every call is billed: long files are split into chunks of about 24,000 characters (one call per chunk), and `--review` doubles the call count.
- Detailed language notes are included for Italian only; other languages use the general rules and register profiles. Add a file under `references/languages/` to cover another language.
- The structure check can flag legitimate changes, such as a `$1` price written as `1 $`.