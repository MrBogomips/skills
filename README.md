# skills

Simple, general-purpose agent skills that I found useful in daily work and want to share.

Each skill is a folder with a `SKILL.md` that follows the [Agent Skills](https://agentskills.io) format, so it works with any coding agent that supports skills.

## Skills and plugins

The repository holds two kinds of things:

- **Standalone skills**, in `skills/`. Each one works on its own, in any agent: install the ones you want with the `skills` CLI, or all of them at once as the Claude Code plugin `skills`.
- **Claude Code plugins**, one top-level folder each (`kaizen/`, `personal-voice/`, `skill-maker/`). A plugin can bring more than skills (hooks, agents, settings), and you install it as a whole. Its README says whether its skills can also be installed one by one with the `skills` CLI, and what you lose that way.

All the plugins come from the `mrbogomips` marketplace, which lists the author's plugins from several repositories.

## Install

### Any agent, with the `skills` CLI

[`skills`](https://github.com/vercel-labs/skills) (Node.js 22.20 or later) installs into Claude Code, Codex, Cursor, OpenCode and many more:

```bash
npx skills add MrBogomips/skills                       # choose skills and agents interactively
npx skills add MrBogomips/skills --list                # list the available skills
npx skills add MrBogomips/skills --skill <name> -g     # one skill, for all your projects
```

These commands cover the standalone skills in `skills/`. A plugin's skills, where its README says they work alone, are reached through the plugin folder: `npx skills add MrBogomips/skills/<plugin>`.

### Claude Code, as a plugin

All the standalone skills come as one plugin, `skills`, from the `mrbogomips` marketplace:

```text
/plugin marketplace add MrBogomips/claude-plugins
/plugin install skills@mrbogomips
```

The plugin installs every skill, and you invoke them as `/skills:<name>` (for example `/skills:done`). To install only some skills, use the `skills` CLI above, which works in Claude Code too.

## Skills

| Skill | What it does |
|---|---|
| [`handoff`](skills/handoff/SKILL.md) | Prepares a handoff prompt so another agent session or a colleague can pick up the work. The prompt goes to the clipboard by default (`--file` writes `<topic>-handoff.md`). When the recipient could not reach some of the material, it becomes `<topic>-handoff.zip` with a patch and the missing files. Sensitive data is confirmed with you before anything leaves the machine. |
| [`spawn-session`](skills/spawn-session/SKILL.md) | From a master session in a workspace hub (a folder holding several git repositories), starts a child session in each repository a piece of work touches, so each child loads that repository's own instructions, skills and agents. Each child gets a handoff prompt and a channel back to the master, and you can talk to it directly. Works in the Claude desktop app, in Herdr, in tmux, with Claude Code background sessions, or by handing you the commands; children open as separate tabs or as panes stacked beside the master, your choice, which can become the hub's default. Optional settings live in a `## Child sessions` section of the hub's `AGENTS.md`. |
| [`done`](skills/done/SKILL.md) | Checks on evidence whether a work session meets its Definition of Done, then tidies up: temporary files, merged branches (local and remote), the local integration branch, the session title. The Definition of Done comes from `DoD.md` files, which can be nested per directory, or from a generic default. If something blocks, you get a short list of what is missing. |
| [`pause`](skills/pause/SKILL.md) | Pauses agentic work safely so you can resume it hours later in the same session. It stops what would run or wake up while you are away (subagents, background commands, loops), writes a short checkpoint, and gives you a `/compact` line to run while the prompt cache is still warm, so the resume is cheap. Say "resume" to pick the work up again. |
| [`tldr`](skills/tldr/SKILL.md) | Summarizes a reply in a few bullets: decisions, open questions, next actions. Once invoked, it keeps a short TLDR footer on later long replies until you say "stop TLDR". |
| [`init-agents-md`](skills/init-agents-md/SKILL.md) | Creates a short, repository-specific `AGENTS.md` and makes `CLAUDE.md` a symlink to it, so every agent reads one instruction file. |
| [`port-to-agents`](skills/port-to-agents/SKILL.md) | Ports a project's Claude Code setup to Codex: one shared `AGENTS.md` with `CLAUDE.md` linked to it, and skills, agents, MCP and hooks converted with rulesync, either committed or regenerated on setup. |
| [`optimize-agents-md`](skills/optimize-agents-md/SKILL.md) | Slims down and restructures `CLAUDE.md` / `AGENTS.md` without changing what they tell agents. It drops repository history (git already keeps it), resolves overlaps and conflicts with the project's skills, keeps the root file under the size the tools recommend, and moves detail that only some tasks or folders need into nested or on-demand files that Claude Code, Codex and other agents can all load. Every change is a diff you approve. |
| [`gemini-web-research`](skills/gemini-web-research/SKILL.md) | Delegates web research to parallel Gemini jobs through the `agy` CLI. A script checks every claim's quote against the pages each job actually read. |
| [`codex-image-gen`](skills/codex-image-gen/SKILL.md) | Generates or edits images through the `codex` CLI's built-in image tool, on the Codex login's quota and with no API key. |
| [`google-image-gen`](skills/google-image-gen/SKILL.md) | Generates or edits images through the Google Gemini API with your own API key (`GEMINI_API_KEY`). |

## Plugins

| Plugin | What it does | Skills installable alone? |
|---|---|---|
| [`kaizen`](kaizen/README.md) | Session retrospective: links the errors, reworks and ambiguities of a session to the skills, rules, CLAUDE.md, memory, hooks and settings behind them, and applies only reviewed fixes you authorize. A Stop hook offers it when a session had friction. | **Yes, with less**: `npx skills add MrBogomips/skills/kaizen` installs the `kaizen` skill; run it with `/kaizen`. There is no Stop hook offer, and the review runs through a general-purpose subagent. |
| [`personal-voice`](personal-voice/README.md) | Writes documents, emails and messages in your tone and lexicon (`voice-write`), learns from your revisions and your own texts (`voice-learn`), and maintains the profile with per-item approval (`voice-maintain`). | **No**: plugin only. The skills share the plugin's store format and its `store_dir` setting. |
| [`skill-maker`](skill-maker/README.md) | Opinionated tools for producing quality skills and plugins. `skill-readme` inventories, checks and drafts the public README of a plugin and of each skill it ships against one fixed section contract; a read-only agent checks every statement against the component's files, and a script validates the result. | **No**: plugin only. The skill runs the plugin's scripts and dispatches its reviewer agent. |

Install a plugin from the `mrbogomips` marketplace:

```text
/plugin marketplace add MrBogomips/claude-plugins
/plugin install <plugin>@mrbogomips
```

Its skills are invoked as `/<plugin>:<skill>`, for example `/personal-voice:voice-write`.

## Repository layout

- `skills/<name>/SKILL.md`: one directory per skill, with any supporting files next to it.
- `.claude-plugin/plugin.json`: the manifest of the Claude Code plugin `skills`, which loads every skill in `skills/`.
- `<plugin>/`: a Claude Code plugin (`kaizen/`, `personal-voice/`, `skill-maker/`) with its own `.claude-plugin/plugin.json`, skills, and any hooks or agents.
- `tests/validate.sh`: checks every plugin manifest and every skill's frontmatter; CI runs it on every push and pull request, together with `tests/test-kaizen-stop-gate.sh`.
- `tests/scenarios/`: manual scenario checklists for the plugin skills.
- `tests/test_*.py`: unit tests for the scripts bundled with skills (`python3 -m unittest discover -s tests -p 'test_*.py'`).

## License

[MIT](LICENSE)
