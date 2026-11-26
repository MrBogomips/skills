---
summary: Revises text and Markdown files with Google Gemini, through agy or the API, in their own language, removing the marks of machine-written prose and applying your writing rules.
---

# gemini-editorial-review

`gemini-editorial-review` revises text and Markdown files in their original language using Google Gemini 4 Neon through your local `agy` CLI or the Gemini API. It removes signs of machine-written prose, applies the writing rules in `AGENTS.md`, `CLAUDE.md`, and the style guides they cite, and returns the revised text with a summary of changes.

## Why

Text drafted by a coding agent carries the habits of its system prompt: stock openers and closers, bullet lists where an argument belongs, inflated adjectives, calques from English, and the same rhythm in every paragraph. Asking the same agent to polish its own draft repeats those habits.

This skill sends the review to a different model with language notes and an editor's brief for each type of text, aiming for prose a careful human writer would stand behind. The brief forbids inventing facts, and a check refuses to write the output file if code, URLs, or placeholders have changed. It runs only on request: `agy` uses your Antigravity quota, while the API bills your key.

## Installation

```bash
npx skills add MrBogomips/skills --skill gemini-editorial-review
```

This installs the same skill bundled in the `skills` plugin, registered as `gemini-editorial-review` instead of `skills:gemini-editorial-review`.

## Usage

Log in to `agy` or set `GEMINI_API_KEY`. Then ask your agent for an editorial review with Gemini, or run `/skills:gemini-editorial-review [technical|marketing|professional|essay|blog|creative] <text-or-file>` in Claude Code when using the plugin. The text profile is optional; Gemini infers it if omitted. Reviewing `guide.md` writes `guide.reviewed.md` alongside it and returns a summary of changes. The agent gathers your writing rules and runs the bundled script, as in this example:

```bash
python3 <skill-dir>/scripts/gemini_editorial_review.py --profile technical --rules docs/style-guide.md -i README.md -o README.reviewed.md
```

Pass `--via agy|api` to choose the backend for a single run, or `--print-prompt` to inspect the prompt without making a call. See [SKILL.md](SKILL.md) for all options.

## Inputs and outputs

- Input: text via `-t`, a file via `-i`, or stdin. Pass house rules with `--rules` (repeatable) and terms with `--glossary`.
- Output: the file specified with `-o`, or stdout if omitted. The source file is never overwritten.
- Stderr: the language, text profile, and summary of changes.
- Integrity check: if fenced code, inline code, absolute URLs, placeholders, HTML tags, or frontmatter differ from the source, the script exits with status 4 and lists the differences. With `-o`, the revision is written to `<output>.unchecked` instead; otherwise, it is still printed to stdout.

## Requirements

- Model: Sonnet class or above; a less capable model does not do this job well enough.
- Python 3.9 or later (standard library only).
- Either the `agy` CLI (installed and logged in) or a Gemini API key in `GEMINI_API_KEY` or `GOOGLE_API_KEY` for a project with credit or billing enabled.
- Default models: `gemini-4-neon-high` through agy and `gemini-4-neon` through the API. Override with `--model` or `GEMINI_EDITORIAL_MODEL`.

## Limitations

- Each document is processed in a single call (API calls retry once on a server error or timeout). Texts over 150,000 characters are rejected; split longer documents by chapter.
- Detailed language notes are included for Italian and English; other languages use the general rules.
- Gemini is instructed to preserve relative links, anchors, paths, and numbers, but the script does not verify them; headings and tables may also be reordered or merged.

## Configuration

Settings are stored in a user-level file and an optional project file (`.gemini-editorial-review.json` at the repository root), and are updated only through the script:

```bash
python3 <skill-dir>/scripts/gemini_editorial_review.py config set backend api
python3 <skill-dir>/scripts/gemini_editorial_review.py config
```

By default, `backend` is `auto`, which uses `agy` when installed and falls back to the API otherwise. You can also configure the timeout and a model for each backend. The `config` subcommand lists every setting and its source.