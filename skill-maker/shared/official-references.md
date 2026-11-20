# Official references

The rules this plugin checks come from the pages below. Read the page, not this summary, before
writing or changing a manifest or a frontmatter: the pages change, this file is a pointer with the
facts the scripts rely on. Last checked: 2026-11-20.

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
- Claude Code adds keys such as `model`, `effort`, `context`, `agent`, `argument-hint`,
  `disable-model-invocation`. Other harnesses may reject them.
- Keep `SKILL.md` under 500 lines and move detail to files it points to, one level deep.

**Agent frontmatter** (`agents/*.md`)

- `name` and `description` are required.
- A plugin agent ignores `hooks`, `mcpServers`, `permissionMode` and `initialPrompt`.

## Where this plugin is stricter

These are this plugin's own rules, not the official ones:

- `version` is required in `plugin.json` and must be a semantic version.
- `description` is required in `plugin.json`.
- Every plugin and every distributed skill has a `README.md` that follows the contract in
  `skills/skill-readme/references/contract.md`.
