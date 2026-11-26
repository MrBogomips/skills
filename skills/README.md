---
summary: Thirteen general-purpose skills for coding agents: session handoff, pause and close, plan stress-testing, shared AGENTS.md files, web research, translation, editorial review and images.
---

# skills

Thirteen small skills for daily work with coding agents. They let you pause and close a session, hand off a task to another session or a colleague, stress-test a plan, keep one short instruction file for every agent, and delegate web research, translation, editorial review and image generation to other tools. Each skill works on its own.

## Why

Working with agents brings the same chores to every project: passing a task on without losing context, verifying with evidence that it is finished, and keeping `AGENTS.md` short and shared across tools. Each skill handles one of them.

They follow the [Agent Skills](https://agentskills.io) format and do not depend on a single harness or the author's setup, so the same skill works in Claude Code, Codex, Cursor, OpenCode and other agents that support skills. Install the full set as a Claude Code plugin, or pick individual skills with the `skills` CLI.

## Included components

| Skill | What it does |
|---|---|
| [`handoff`](handoff/README.md) | Writes a prompt that lets another session or a colleague continue a task, with a patch or zip for files they cannot access. |
| [`done`](done/README.md) | Verifies with evidence whether the session's work meets its Definition of Done, then cleans up temporary files and merged branches. |
| [`pause`](pause/README.md) | Stops background work and writes a checkpoint so you can leave and resume later in the same session. |
| [`tldr`](tldr/README.md) | Summarizes a reply in a fixed format and optionally keeps the same footer on later long replies. |
| [`maieutic`](maieutic/README.md) | Interviews you about a plan or decision in short rounds of questions with recommended answers, and logs what was decided and discarded. |
| [`optimize-agents-md`](optimize-agents-md/README.md) | Slims down and restructures `AGENTS.md` and `CLAUDE.md` without changing what they tell agents. |
| [`gemini-web-research`](gemini-web-research/README.md) | Delegates web research to parallel Gemini workers and checks every claim against the pages they read. |
| [`image-gen`](image-gen/README.md) | Generates or edits images through the `codex` CLI (Codex login quota) or, on request, the Google Gemini API with your own key. |
| [`gemini-translate`](gemini-translate/README.md) | Translates text and files into any language and register with Google Gemini, keeping code and placeholders intact. |
| [`gemini-editorial-review`](gemini-editorial-review/README.md) | Revises text and files in their original language with Google Gemini (via agy or the API), removing signs of machine-written prose and applying your project's writing rules. |

## Installation

```text
/plugin marketplace add MrBogomips/claude-plugins
/plugin install skills@mrbogomips
```

The plugin installs all twelve skills, which you invoke as `/skills:<name>`.

**Standalone skills: yes.** Each skill also installs on its own in any agent supported by the [`skills`](https://github.com/vercel-labs/skills) CLI (requires Node.js 22.20 or later), without losing anything. It is installed under its own name, without the `skills:` prefix.

```bash
npx skills add MrBogomips/skills --skill <name>
```

## Quick start

```text
/skills:done --check
```

This returns a verdict on the session's work (`NOT DONE`, `DONE` or `DONE, closable`) and the cleanup that would follow, without making any changes.

## License

[MIT](../LICENSE)
