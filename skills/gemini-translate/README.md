---
summary: Translates text and Markdown files with Google Gemini into any language, in the register you choose, keeping code, links and placeholders intact.
---

# gemini-translate

`gemini-translate` translates text and Markdown files through the Google Gemini API into the language you name, in a formal, professional, technical or informal register. It detects the source language, keeps code, URLs and placeholders untouched, and aims for text that reads as if it had been written in the target language. It uses your own API key.

## Why

Translations written by a general-purpose agent often read like translations: borrowed syntax, literal idioms, a form of address that drifts. This skill hands the work to Gemini, which ranks among the strongest models in independent machine-translation evaluations. It sends a translator's brief with register profiles and per-language notes, then checks on its own that code, links, placeholders, headings and tables came through unchanged. Every call is billed to your key, so the skill runs only when you ask for a Gemini translation.

## Installation

```bash
npx skills add MrBogomips/skills --skill gemini-translate
```

It is the same skill as in the `skills` plugin, installed under the name `gemini-translate` instead of `skills:gemini-translate`.

## Usage

Set `GEMINI_API_KEY`, then ask your agent to translate with Gemini, naming the target language and, if you want, the register (`/skills:gemini-translate` in Claude Code with the plugin). The agent runs the bundled script from the skill's folder:

```bash
python3 scripts/gemini_translate.py --to it --register technical -i README.md -o README.it.md
```

Without `--register`, Gemini infers it and the script reports it. `--glossary` enforces your terminology, `--review` adds a revision pass at double the cost, and `--print-prompt` shows the request without making a call. All options are in [SKILL.md](SKILL.md).

## Inputs and outputs

- Input: `-t` text, `-i` file, or stdin. Output: the file given with `-o`, otherwise stdout.
- The detected source language and the register go to stderr.
- When code, URLs, placeholders, tags, headings or table rows differ from the source, nothing is written to `-o`: the translation goes to `<output>.unchecked` and the differences are listed.

## Requirements

- A Gemini API key in `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
- Python 3.9 or later, standard library only, and network access.
- The default model is `gemini-4-carbon`; pass `--model <id>` or set `GEMINI_TRANSLATE_MODEL` to use another.

## Limitations

- Every call is billed: long files are sent in chunks of about 24,000 characters, one call each, and `--review` doubles the count.
- Detailed language notes ship for Italian only; other languages get the general rules and register profiles. Add a file under `references/languages/` to extend them.
- The structure check can flag legitimate changes, such as a `$1` price written as `1 $`.
