# Official references

The rules this plugin checks come from the pages below. Read the page, not this summary, before
writing or changing a manifest or a frontmatter: the pages change, this file is a pointer with the
facts the scripts rely on. Last checked: 2026-11-25.

| Topic | Page |
|---|---|
| Plugin manifest, component folders, `${CLAUDE_PLUGIN_ROOT}` | https://code.claude.com/docs/en/plugins-reference |
| Marketplace manifest, plugin entries, sources | https://code.claude.com/docs/en/plugin-marketplaces |
| `SKILL.md` frontmatter and substitutions in Claude Code | https://code.claude.com/docs/en/skills |
| Agent files and plugin agents | https://code.claude.com/docs/en/sub-agents |
| Portable skill format (any harness) | https://agentskills.io/specification |

## Facts the scripts rely on

**Plugin manifest** (`.claude-plugin/plugin.json`)

- Only `name` is required: lowercase words joined by hyphens.
- Components are found at the plugin root: `skills/`, `agents/`, `commands/`, `hooks/hooks.json`.
- A `skills` field adds folders to the default `skills/` scan. `agents` and `commands` fields replace
  their default folder. A `hooks` field merges with `hooks/hooks.json`.
- Agents are scanned recursively; an agent in a subfolder is invoked as `plugin:folder:agent`.

**Marketplace manifest** (`.claude-plugin/marketplace.json`)

- Top level: `name`, `owner`, `plugins`. Each entry needs `name` and `source`.
- The entry `name` should equal the `name` in the plugin's `plugin.json`.
- A plugin in a subfolder of another repository uses the `git-subdir` source with `url` and `path`.

**Skill frontmatter** (`SKILL.md`)

- Portable keys: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
- `name`: 1 to 64 characters, lowercase letters, digits and single hyphens, equal to the folder name.
- `description`: 1 to 1024 characters. It is the only text an agent sees before the skill loads.
- Claude Code adds these keys: `when_to_use`, `argument-hint`, `arguments`,
  `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`,
  `agent`, `background`, `hooks`, `paths`, `shell`. Other harnesses may ignore or reject them.
- Keep `SKILL.md` under 500 lines and move detail to files it points to, one level deep.

**Agent frontmatter** (`agents/*.md`)

- `name` and `description` are required.
- A plugin agent ignores `hooks`, `mcpServers`, `permissionMode` and `initialPrompt`.

## Official tools

Skills and plugins published by Anthropic, or built into Claude Code, are the official tier. Their
guidance wins over any other source, except where the rules of the repository or project in use say
otherwise. Where one of them already does a job, skill-maker hands off to it and covers only what it
leaves out. The skills built into Claude Code are covered through the documentation pages above.

### Recommended tools

skill-maker works without these, but strongly recommends them. Its reports list each missing one on
every run, with what is lost and how to install it.

| Tool | skill-maker hands off | Lost without it | Install |
|---|---|---|---|
| skill-creator | drafting a skill, evals against a baseline, description tuning, benchmarks | automated evals and trigger tuning: the manual methods of rules T1–T4 take their place | `/plugin install skill-creator@claude-plugins-official` |
| plugin-dev | writing agents, hooks, commands, plugin settings; plugin validation | guided authoring of Claude Code components: rules C1–C8 and the official pages take its place | `/plugin install plugin-dev@claude-plugins-official` |
| claude-md-management | audits of instruction files | nothing in skill-maker; instruction files are out of its scope | `/plugin install claude-md-management@claude-plugins-official` |
| claude-code-setup | recommendations of hooks, agents and skills for a codebase | nothing in skill-maker | `/plugin install claude-code-setup@claude-plugins-official` |
| hookify | turning repeated mistakes into hook rules | the C6 promotion of a skipped rule to a hook is done by hand | `/plugin install hookify@claude-plugins-official` |

Which rules rest on which source, and the version each was last checked against, is recorded in
`official-baseline.json`. A monthly check in the source repository opens an issue when one changes.

## Where this plugin is stricter

These are this plugin's own rules, not the official ones:

- `version` is required in `plugin.json` and must be a semantic version.
- `description` is required in `plugin.json`.
- Every plugin and every distributed skill has a `README.md` that follows the contract in
  `skills/skill-readme/references/contract.md`.
