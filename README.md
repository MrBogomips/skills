# skills

Simple, general-purpose agent skills that I found useful in daily work and want to share.

Each skill is a folder with a `SKILL.md` that follows the [Agent Skills](https://agentskills.io) format, so it works with any coding agent that supports skills.

## Install

### Any agent, with the `skills` CLI

[`skills`](https://github.com/vercel-labs/skills) (Node.js 22.20 or later) installs into Claude Code, Codex, Cursor, OpenCode and many more:

```bash
npx skills add MrBogomips/skills                       # choose skills and agents interactively
npx skills add MrBogomips/skills --list                # list the available skills
npx skills add MrBogomips/skills --skill <name> -g     # one skill, for all your projects
```

### Claude Code, as a plugin marketplace

```text
/plugin marketplace add MrBogomips/skills
/plugin install <skill>@mrbogomips-skills
```

Each skill is its own plugin, so you install only the ones you want.

## Skills

| Skill | What it does |
|---|---|
| [`handoff`](skills/handoff/SKILL.md) | Prepares a handoff prompt so another agent session or a colleague can pick up the work. The prompt goes to the clipboard by default (`--file` writes `<topic>-handoff.md`). When the recipient could not reach some of the material, it becomes `<topic>-handoff.zip` with a patch and the missing files. Sensitive data is confirmed with you before anything leaves the machine. |

## Repository layout

- `skills/<name>/SKILL.md`: one directory per skill, with any supporting files next to it.
- `.claude-plugin/marketplace.json`: the Claude Code marketplace, one plugin entry per skill.
- `tests/validate.sh`: checks that the marketplace and `skills/` describe the same skills; CI runs it on every push and pull request.

## License

[MIT](LICENSE)
