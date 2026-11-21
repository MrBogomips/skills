---
summary: Eleven general-purpose skills for work with coding agents, from handing over, pausing and closing a session to shared AGENTS.md files, checked web research, translation and image generation.
---

# skills

Eleven small skills for daily work with coding agents. They hand a task over to another session or a colleague, pause and close a work session, keep one short instruction file for every agent, and delegate web research, translation and image generation to other tools. Each skill works on its own.

## Why

Work with agents has chores that every project repeats: passing a task on without losing context, deciding on evidence that it is finished, keeping `AGENTS.md` short and shared between tools. Each of these skills settles one of them.

They follow the [Agent Skills](https://agentskills.io) format and depend on nothing specific to one harness or to the author's setup, so the same skill works in Claude Code, Codex, Cursor, OpenCode and other agents that support skills. Install all of them as one Claude Code plugin, or only the ones you want with the `skills` CLI.

## Included components

| Skill | What it does |
|---|---|
| [`handoff`](handoff/README.md) | Writes a prompt that lets another session or a colleague continue a task, with a patch or a zip for the files they cannot reach. |
| [`done`](done/README.md) | Checks on evidence whether the session's work meets its Definition of Done, then cleans up temporary files and merged branches. |
| [`pause`](pause/README.md) | Stops background work and writes a checkpoint, so you can leave and resume later in the same session. |
| [`tldr`](tldr/README.md) | Summarizes a reply in a few bullets and can keep a short footer on later long replies. |
| [`init-agents-md`](init-agents-md/README.md) | Creates a short `AGENTS.md` for a repository and makes `CLAUDE.md` a symlink to it. |
| [`optimize-agents-md`](optimize-agents-md/README.md) | Slims down and restructures `AGENTS.md` and `CLAUDE.md` without changing what they tell agents. |
| [`port-to-agents`](port-to-agents/README.md) | Ports a project's Claude Code setup to Codex around one shared `AGENTS.md`. |
| [`gemini-web-research`](gemini-web-research/README.md) | Delegates web research to parallel Gemini workers and checks every claim against the pages they read. |
| [`codex-image-gen`](codex-image-gen/README.md) | Generates or edits images through the `codex` CLI, on the Codex login's quota. |
| [`google-image-gen`](google-image-gen/README.md) | Generates or edits images through the Google Gemini API with your own API key. |
| [`gemini-translate`](gemini-translate/README.md) | Translates text and files with Google Gemini into any language and register, keeping code and placeholders intact. |

## Installation

```text
/plugin marketplace add MrBogomips/claude-plugins
/plugin install skills@mrbogomips
```

The plugin installs every skill, and you invoke them as `/skills:<name>`.

**Standalone skills: yes.** Each skill also installs alone, in any agent the [`skills`](https://github.com/vercel-labs/skills) CLI supports (Node.js 22.20 or later), and nothing is lost that way. The skill is then installed under its own name, without the `skills:` prefix.

```bash
npx skills add MrBogomips/skills --skill <name>
```

## Quick start

```text
/skills:done --check
```

You get a verdict on the session's work (`NOT DONE`, `DONE` or `DONE, closable`) and the cleanup that would follow. Nothing is changed.

## License

[MIT](../LICENSE)
