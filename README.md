# skills

Simple, general-purpose agent skills that I found useful in daily work and want to share.

Each skill lives in a directory with a `SKILL.md` that follows the [Agent Skills](https://agentskills.io) format, so it works with any coding agent that supports skills.

## Skills and plugins

This repository contains two kinds of components:

- **Standalone skills**, in `skills/`. Each works on its own in any agent: install the ones you want with the `skills` CLI, or install all of them at once as the `skills` Claude Code plugin.
- **Claude Code plugins**, one top-level directory each (`kaizen/`, `personal-voice/`, `skill-maker/`). A plugin can bundle more than skills (hooks, agents, settings) and is installed as a whole. Each plugin's README states whether its skills can also be installed individually with the `skills` CLI and what is lost by doing so.

All plugins are available from the `mrbogomips` marketplace, which lists my plugins from several repositories.

## Install

### Any agent, with the `skills` CLI

The [`skills`](https://github.com/vercel-labs/skills) CLI (requires Node.js 22.20 or later) installs skills into Claude Code, Codex, Cursor, OpenCode, and many other agents:

```bash
npx skills add MrBogomips/skills                       # choose skills and agents interactively
npx skills add MrBogomips/skills --list                # list the available skills
npx skills add MrBogomips/skills --skill <name> -g     # one skill, for all your projects
```

These commands cover the standalone skills in `skills/`. When a plugin's README notes that its skills work alone, install them from the plugin directory: `npx skills add MrBogomips/skills/<plugin>`.

### Claude Code, as a plugin

All standalone skills are also bundled into a single `skills` plugin from the `mrbogomips` marketplace:

```text
/plugin marketplace add MrBogomips/claude-plugins
/plugin install skills@mrbogomips
```

The plugin installs every standalone skill; invoke them as `/skills:<name>` (for example, `/skills:done`). To install only specific skills, use the `skills` CLI above, which also supports Claude Code.

## Skills

| Skill | What it does |
|---|---|
| [`handoff`](skills/handoff/SKILL.md) | Prepares a handoff prompt so another agent session or a colleague can pick up the work. Copies the prompt to the clipboard by default (`--file` writes `<topic>-handoff.md`). When the recipient cannot access some of the material, it builds `<topic>-handoff.zip` with a patch and the missing files. Asks you to confirm sensitive data before anything leaves the machine. |
| [`done`](skills/done/SKILL.md) | Verifies with evidence whether a work session meets its Definition of Done, then cleans up temporary files, merged branches (local and remote), the local integration branch, and the session title. Reads the Definition of Done from `DoD.md` files (which can be nested per directory) or falls back to a generic default. If anything blocks completion, it returns a short list of what is missing. |
| [`pause`](skills/pause/SKILL.md) | Pauses agentic work safely so you can resume it hours later in the same session. Stops anything that would run or wake up while you are away (subagents, background commands, loops), writes a short checkpoint, and gives you a `/compact` command to run while the prompt cache is still warm so resuming stays cheap. Say "resume" to pick up where you left off. |
| [`tldr`](skills/tldr/SKILL.md) | Summarizes a reply in a few bullets: decisions, open questions, and next actions. Once invoked, it adds a short TLDR footer to subsequent long replies until you say "stop TLDR". |
| [`maieutic`](skills/maieutic/SKILL.md) | Interviews you about a plan, design, or decision in short rounds of up to five questions, each with a recommended answer, until every decision is settled. Looks up the facts it can find and asks you for decisions and for facts only you know. Keeps a log of what was decided and what was explicitly discarded, each with a short rationale. A hard mode plays devil's advocate and ends with a pre-mortem. |
| [`init-agents-md`](skills/init-agents-md/SKILL.md) | Creates a short, repository-specific `AGENTS.md` and makes `CLAUDE.md` a symlink to it, so every agent reads a single instruction file. |
| [`port-to-agents`](skills/port-to-agents/SKILL.md) | Ports a project's Claude Code setup to Codex: creates a shared `AGENTS.md` with `CLAUDE.md` linked to it, and converts skills, agents, MCP, and hooks with rulesync (either committed or regenerated on setup). |
| [`optimize-agents-md`](skills/optimize-agents-md/SKILL.md) | Slims down and restructures `CLAUDE.md` / `AGENTS.md` without changing what they tell agents. Drops repository history (git already tracks it), resolves overlaps and conflicts with the project's skills, keeps the root file under the size the tools recommend, and moves details needed only for specific tasks or directories into nested or on-demand files that Claude Code, Codex, and other agents can all load. Every change is a diff you approve. |
| [`gemini-web-research`](skills/gemini-web-research/SKILL.md) | Delegates web research to parallel Gemini jobs through the `agy` CLI. A script verifies the quote for every claim against the pages each job actually read. |
| [`codex-image-gen`](skills/codex-image-gen/SKILL.md) | Generates or edits images through the `codex` CLI's built-in image tool, using the Codex login quota with no API key. |
| [`google-image-gen`](skills/google-image-gen/SKILL.md) | Generates or edits images through the Google Gemini API with your own API key (`GEMINI_API_KEY`). |
| [`gemini-translate`](skills/gemini-translate/SKILL.md) | Translates text and Markdown files through the Google Gemini API into any language and register (formal, professional, technical, informal). Detects the source language and checks that code, links, and placeholders remain unchanged. Uses your own API key (`GEMINI_API_KEY`). |
| [`gemini-editorial-review`](skills/gemini-editorial-review/SKILL.md) | Revises text and Markdown files in their original language with Google Gemini (Gemini 4 Neon or above) through the local `agy` CLI or the Gemini API. Removes signs of machine-written prose, fixes structure, register, and calques, and applies the writing rules in `AGENTS.md`, `CLAUDE.md`, and the style guides they cite. Checks that code, links, placeholders, and frontmatter remain unchanged. Uses `agy` by default when installed; backend, models, and timeout are configured per user and per project. |

`spawn-session` was retired in 2.0.0. Its successor is the `session-hub` plugin ([MrBogomips/agent-orchestration](https://github.com/MrBogomips/agent-orchestration)): install it with `/plugin install session-hub@mrbogomips`, then use `/session-hub:spawn`. A hub that pins this repository in a lock file keeps the old skill until it updates the pin.

## Plugins

| Plugin | What it does | Skills installable alone? |
|---|---|---|
| [`kaizen`](kaizen/README.md) | Session retrospective: links a session's errors, rework, and ambiguities to the skills, rules, `CLAUDE.md`, memory, hooks, and settings behind them, and applies only reviewed fixes you authorize. A Stop hook offers it when a session has friction. | **Yes, with limitations**: `npx skills add MrBogomips/skills/kaizen` installs the `kaizen` skill; run it with `/kaizen`. There is no Stop hook offer, and the review runs through a general-purpose subagent. |
| [`personal-voice`](personal-voice/README.md) | Writes documents, emails, and messages in your tone and lexicon (`voice-write`), learns from your revisions and your own texts (`voice-learn`), and maintains the profile with per-item approval (`voice-maintain`). | **No**: plugin only. The skills share the plugin's store format and its `store_dir` setting. |
| [`skill-maker`](skill-maker/README.md) | Opinionated tools for producing quality skills and plugins. `skill-readme` inventories, checks, and drafts public READMEs for a plugin and each skill it ships against a fixed section contract; a read-only agent verifies every statement against the component's files, and a script validates the result. | **No**: plugin only. The skill runs the plugin's scripts and dispatches its reviewer agent. |

Install a plugin from the `mrbogomips` marketplace:

```text
/plugin marketplace add MrBogomips/claude-plugins
/plugin install <plugin>@mrbogomips
```

Invoke a plugin's skills as `/<plugin>:<skill>` (for example, `/personal-voice:voice-write`).

## Repository layout

- `skills/<name>/SKILL.md`: one directory per skill, with any supporting files alongside it.
- `.claude-plugin/plugin.json`: manifest for the `skills` Claude Code plugin, which loads every skill in `skills/`.
- `<plugin>/`: a Claude Code plugin (`kaizen/`, `personal-voice/`, `skill-maker/`) with its own `.claude-plugin/plugin.json`, skills, and any hooks or agents.
- `tests/validate.sh`: checks every plugin manifest and skill frontmatter; CI runs it on every push and pull request alongside `tests/test-kaizen-stop-gate.sh`.
- `tests/scenarios/`: manual scenario checklists for the plugin skills.
- `tests/test_*.py`: unit tests for the scripts bundled with skills (`python3 -m unittest discover -s tests -p 'test_*.py'`).

## License

[MIT](LICENSE)