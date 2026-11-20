---
summary: Delegates web research to parallel Gemini workers through the agy CLI and returns an answer in which every fact was checked against the pages the workers read.
---

# gemini-web-research

`gemini-web-research` hands substantial web research to Gemini workers that run in parallel through the `agy` CLI. Each worker searches, reads pages and backs every claim with a verbatim quote. A script checks each quote against the pages the worker actually read, and your agent writes the answer from the claims that passed.

## Why

A model asked to research can cite a page it never opened, or a quote that is not there. Here a claim counts as a fact only when its quote was found in a page the worker read. The rest is flagged as a lead or reported as unconfirmed, and the answer says plainly what stayed open.

## Installation

```bash
npx skills add MrBogomips/skills --skill gemini-web-research
```

It is the same skill as in the `skills` plugin, installed under the name `gemini-web-research` instead of `skills:gemini-web-research`.

## Usage

Ask to research something with Gemini or with `agy`; the skill does not run for an ordinary research request.

```text
/skills:gemini-web-research <what you want to know>
```

Your agent splits the request into questions, one worker each, and sizes the research to its difficulty. A round takes 3 to 6 minutes. You get a synthesis in which each fact links to the page it came from, and a plain statement of what stayed unconfirmed.

## Requirements

- The `agy` CLI (Google Antigravity), installed and logged in.
- Python 3.9 or later (standard library only) and network access.
- The workers use the model `gemini-3.8-flash-high`; set `GEMINI_RESEARCH_MODEL` to another id from `agy models` to change it.

## Limitations

- It is not for a quick search or everyday research: it runs only when you name Gemini or `agy`.
- An MCP server configured in `agy` that never connects blocks every worker. The skill reports the server and stops: repairing `agy` or removing that server is your decision.
