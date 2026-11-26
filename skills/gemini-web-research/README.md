---
summary: Delegates web research to parallel Gemini workers through the agy CLI and returns an answer in which every fact was checked against the pages the workers read.
---

# gemini-web-research

`gemini-web-research` delegates substantial web research to parallel Gemini workers through the `agy` CLI. Each worker searches, reads pages, and backs every claim with a verbatim quote. A script checks each quote against the pages the worker actually read, and your agent writes the answer from the claims that pass.

## Why

When asked to do research, a model can cite a page it never opened or a quote that is not there. With this skill, a claim counts as a fact only when its quote is found on a page the worker read. Everything else is flagged as a lead or reported as unconfirmed, and the answer states plainly what remains open.

## Installation

```bash
npx skills add MrBogomips/skills --skill gemini-web-research
```

This installs the same skill included in the `skills` plugin, under the name `gemini-web-research` instead of `skills:gemini-web-research`.

## Usage

Ask your agent to research a topic with Gemini or `agy`, or invoke the skill directly. It does not run for ordinary research requests.

```text
/skills:gemini-web-research <what you want to know>
```

Your agent splits the request into questions (one per worker) and scales the research to match the difficulty. A round takes 3 to 6 minutes. You get a synthesis linking each fact to the page it came from, along with a plain statement of what remains unconfirmed.

## Requirements

- Model: Sonnet class or above, effort medium or above; a less capable model does not do this job well enough.
- The `agy` CLI (Google Antigravity), installed and logged in.
- Python 3.9 or later (standard library only).
- Network access.
- Workers use `gemini-3.8-flash-high` by default; set `GEMINI_RESEARCH_MODEL` to another ID from `agy models` to change it.

## Limitations

- The skill is not meant for quick searches or everyday research, and it runs only when you name Gemini or `agy`.
- If an MCP server configured in `agy` cannot connect, it blocks every worker. The skill reports the server and stops, so you can decide whether to repair `agy` or remove that server.
