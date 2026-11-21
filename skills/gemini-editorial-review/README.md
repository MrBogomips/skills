---
summary: Revises text and Markdown files with Google Gemini in their own language, removing the marks of machine-written prose and applying your project's writing rules.
---

# gemini-editorial-review

`gemini-editorial-review` sends a text or a Markdown file to Google Gemini (Gemini 4 Neon by default) for an editorial review in its own language. It removes the marks of machine-written prose and applies the writing rules in your `AGENTS.md`, `CLAUDE.md` and the style guides they cite. You get the revised text and a short summary of what changed.

## Why

Text drafted by a coding agent carries the habits of its system prompt: stock openers and closers, bullet lists where an argument belongs, inflated adjectives, calques from English, the same rhythm in every paragraph. Asking the same agent to polish it repeats those habits. This skill hands the review to a different model, with an editor's brief for each kind of text and notes for each language, and aims for prose a careful human writer would sign. The brief forbids invented facts, and a check refuses to write the file when code, URLs or placeholders changed. Every call is billed to your key, so it runs only when you ask.

## Installation

```bash
npx skills add MrBogomips/skills --skill gemini-editorial-review
```

It is the same skill as in the `skills` plugin, installed under the name `gemini-editorial-review` instead of `skills:gemini-editorial-review`.

## Usage

Set `GEMINI_API_KEY`, then ask your agent for an editorial review with Gemini, or type `/skills:gemini-editorial-review [technical|marketing|professional|essay|blog|creative] <text-or-file>` in Claude Code with the plugin. The kind of text is optional: Gemini infers it. For `guide.md`, you get `guide.reviewed.md` next to it, plus the summary of changes. Behind the request, the agent collects your writing rules and runs the bundled script, for example:

```bash
python3 <skill-dir>/scripts/gemini_editorial_review.py --profile technical --rules docs/style-guide.md -i README.md -o README.reviewed.md
```

`--print-prompt` shows the request without making a call. All options are in [SKILL.md](SKILL.md).

## Inputs and outputs

- Input: `-t` text, `-i` file, or stdin; house rules with `--rules` (repeatable) and terms with `--glossary`.
- Output: the file given with `-o`, otherwise stdout. The source file is never overwritten.
- The language, the kind of text and the summary of changes go to stderr.
- When fenced code, inline code, absolute URLs, placeholders, HTML tags or the frontmatter differ from the source, the script exits with status 4 and lists the differences: with `-o`, the revision goes to `<output>.unchecked` instead; without it, it is printed anyway.

## Requirements

- A Gemini API key in `GEMINI_API_KEY` or `GOOGLE_API_KEY`, on a project with credit or billing enabled.
- Python 3.9 or later, standard library only, and network access.
- The default model is `gemini-4-neon`; `--model gemini-4-argon` or `GEMINI_EDITORIAL_MODEL` selects another.

## Limitations

- One billed call per document (retried once on a server error or timeout), and texts over 150,000 characters are refused: split long documents by chapter.
- Detailed language notes ship for Italian and English; other languages get the general rules.
- Relative links, anchors, paths and numbers are asked of Gemini but not checked; headings and tables may be reordered or merged.
