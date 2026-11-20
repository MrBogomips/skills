# AGENTS.md

The rules for every coding agent working in this repository.

## What this repository is

A collection of small, general-purpose agent skills, shared through two channels built from the same files:

- **Any harness**, via the [`skills` CLI](https://github.com/vercel-labs/skills): `npx skills add MrBogomips/skills` (pick skills with `--skill <name>`, agents with `-a <agent>`, user scope with `-g`).
- **Claude Code plugin**: the skills in `skills/` make up one plugin, `skills`, with the repository root as its folder. It is listed in the `mrbogomips` marketplace, which lives in its own repository and also lists the author's other plugins: `/plugin marketplace add MrBogomips/claude-plugins`, then `/plugin install skills@mrbogomips`. Skills are invoked as `/skills:<name>`. Users who want a single skill use the `skills` CLI instead.

The repository also hosts **Claude Code plugins** that need more than a skill (hooks, agents, plugin settings): one top-level folder each, listed as separate plugins in the same marketplace. See [Plugins](#plugins).

There is no build step. The repository is Markdown skills plus one JSON manifest per plugin.

## Layout

- `skills/<name>/SKILL.md`: one directory per skill. Supporting files (`references/`, `scripts/`, `assets/`) go inside that directory.
- `.claude-plugin/plugin.json`: the manifest of the `skills` plugin, with `name`, `version`, `description`, `author` and `keywords`. It has **no `skills` field**, so Claude Code loads every `skills/<name>/SKILL.md`. There is no `marketplace.json` here: the marketplace entry (source `github`, `category`, `tags`) lives in `MrBogomips/claude-plugins` and carries no `version`, so the version is read from `plugin.json`.
- `<plugin>/` (today `kaizen/`, `personal-voice/` and `skill-maker/`): a Claude Code plugin with its own `.claude-plugin/plugin.json`, `skills/`, and optionally `agents/`, `hooks/` and shared files. The root plugin loads only the root `skills/`, and the `skills` CLI lists only the root `skills/` for `npx skills add MrBogomips/skills`, so plugin skills stay out of both.
- `tests/`: `validate.sh` (repository checks), `selftest.sh` (the validator's own tests) and `test-kaizen-stop-gate.sh` (the kaizen Stop hook), all run by `.github/workflows/validate.yml` on pushes and pull requests to `main`; `scenarios/` holds manual scenario checklists for the plugins and for `spawn-session`.
- `DoD.md`: the Definition of Done that the `done` skill checks a session against.
- `README.md` keeps the public skill and plugin lists and install instructions; update it whenever a skill or plugin is added, renamed or removed.
- **Component READMEs**: every plugin and every distributed skill has a short `README.md` that follows the `skill-maker` contract (`skill-maker/skills/skill-readme/references/contract.md`): what it does and why, never a retelling of `SKILL.md`. The `skills` plugin's README is `skills/README.md`, because the root `README.md` is the repository page. Write or revise them with `/skill-maker:skill-readme`.

## Portability rules

A skill in `skills/` has to work in every harness the `skills` CLI targets, not only in Claude Code. Skills inside a plugin folder follow [Plugins](#plugins) instead.

- **Frontmatter** follows the Agent Skills spec (agentskills.io): `name`, `description`, and optionally `license`, `compatibility`, `metadata`, `allowed-tools`. Other harnesses ignore Claude Code-only keys, so a skill must still work without them.
- **`name` equals the directory name** (lowercase, hyphens). The `skills` CLI installs a skill under its frontmatter `name`, so a mismatch gives the skill different identities in the two channels. Neither tool reports it (see Verification).
- **`description`** says what the skill does and when to use it. Before a skill loads, the description is the only part an agent sees.
- **Bundled files** are referenced by paths relative to the skill directory. Never use `${CLAUDE_PLUGIN_ROOT}` or files outside `skills/<name>/`: the `skills` CLI installs only the skill directory into each agent's skills folder.
- **No dependence on the author's setup**: no personal paths, no reliance on `~/.claude` rules or memory, and no assumption that particular MCP servers, plugins or CLIs are installed. Detect them at runtime or ask the user.
- **Bundled scripts** run on users' machines, so keep them macOS/BSD-compatible: no `grep -P`, no `head -n -1`, bash 3.2.

## Adding, changing, removing a skill

- **Add**: run `npx skills init <name>` from inside `skills/` (it writes `<name>/SKILL.md`). The plugin picks it up with no manifest change.
- **Version**: every pull request that changes what a skill does bumps `version` in `.claude-plugin/plugin.json`, once per pull request: patch for a fix, minor for a new skill or a compatible extension, major when a skill is renamed or removed or its behavior changes incompatibly. Claude Code updates installed plugins only when the version changes.
- **Rename or remove**: change the directory and the frontmatter `name` together. In Claude Code the invocation changes with it (`/skills:<old>` stops working); `skills` CLI installs keep the old name until removed.

## Plugins

A top-level plugin folder is for work that needs Claude Code plugin features: hooks, agents, `userConfig`, `${CLAUDE_PLUGIN_ROOT}`, files shared by several skills. Anything a single portable skill can do belongs in `skills/` instead.

- **Manifest**: `<plugin>/.claude-plugin/plugin.json`, with `name` equal to the folder name, a semver `version`, and no `skills` field. No `marketplace.json`.
- **Marketplace entry**: in `MrBogomips/claude-plugins`, with source `{"source": "git-subdir", "url": "https://github.com/MrBogomips/skills.git", "path": "<plugin>"}` and no `version`. Claude Code checks out only that folder, so a plugin may use nothing outside it.
- **Skill names**: the frontmatter `name` equals the directory, and names are specific enough to install at user scope (`voice-write`, not `write`). Skills hand off to each other as `<plugin>:<skill>`.
- **Standalone or plugin-only**: every plugin README has an **Installation** section that says whether its skills also work installed alone with `npx skills add MrBogomips/skills/<plugin>`, and what is lost that way. A skill that reads `${CLAUDE_PLUGIN_ROOT}`, `${user_config.*}` or files outside its own folder is plugin-only. Keep that statement, and the plugin table in `README.md`, in step with the code.
- **Version**: each plugin has its own `version` in its own `plugin.json`, bumped per pull request with the same patch/minor/major rule as above. The root `skills` version does not change for plugin work.
- **Tests**: a plugin's automated tests live in `tests/` and run in CI; its manual scenarios live in `tests/scenarios/<skill>/` (see `tests/scenarios/README.md`).

## The AGENTS.md skills must agree

`init-agents-md` (create), `optimize-agents-md` (slim and restructure) and `port-to-agents` (port a Claude Code setup to Codex) work on the same files and must stay coherent. When you change one, check the other two in the same pull request:

- **Instruction layer**: all three target one real `AGENTS.md`, `CLAUDE.md` as a relative symlink to it, and Claude Code-only lines in `.claude/CLAUDE.md`. None proposes an `@AGENTS.md` import or a generated copy.
- **Loading facts**: how each harness loads instruction files and skills is written in `skills/port-to-agents/references/instruction-files.md` and `skills/optimize-agents-md/references/loading-and-limits.md`. A skill can't read another skill's files, so each keeps its own copy: update both copies together, with the date and versions checked.
- **Scope and names**: each skill hands off to the others by their current names and never does their work.

## Verification

After any change, run from the repo root (requires `jq`):

```bash
bash tests/validate.sh                             # every plugin.json and its skills/ agree (CI runs this)
bash tests/test-kaizen-stop-gate.sh                # the kaizen Stop hook (CI runs this; needs git)
python3 -m unittest discover -s tests -p 'test_*.py'  # unit tests of bundled scripts (CI runs this)
CODEX_PORT_SH=dash python3 -m unittest discover -s tests -p 'test_codex_port_block.py'  # the POSIX block under dash too
claude plugin validate . --strict                  # plugin.json schema of the root plugin
claude plugin validate ./kaizen --strict           # ... and of each plugin folder
claude plugin validate ./personal-voice --strict
claude plugin validate ./skill-maker --strict
for p in . kaizen personal-voice skill-maker; do python3 skill-maker/scripts/validate.py --no-claude $p; done  # every plugin and skill README follows the contract
DISABLE_TELEMETRY=1 npx -y skills add ./ --list    # what the skills CLI discovers (Node >= 22.20): only skills/
DISABLE_TELEMETRY=1 npx -y skills add ./kaizen --list  # a plugin's skills, reached by its folder
```

`tests/validate.sh` exists because the other two commands don't report a skill directory with no `SKILL.md` or a frontmatter `name` that differs from its directory. It also enforces the frontmatter limits, each plugin's name (equal to its folder for plugin folders) and semver version, the absence of a `skills` field (which would stop the default scan of `skills/`) and of a `marketplace.json`.

When you change `tests/validate.sh`, add or adjust a case in `tests/selftest.sh` and run `bash tests/selftest.sh`; CI runs it before the validator. Both scripts must stay bash 3.2 compatible: run them with `/bin/bash` on macOS to check.

To try a plugin locally in Claude Code without installing it: `claude --plugin-dir .` (the skills appear as `/skills:<name>`), or `claude --plugin-dir ./<plugin>` for a plugin folder.

## Working documents

- **Authoritative**: `skills/`, `.claude-plugin/plugin.json` and each plugin folder.
- **AI working material** (brainstorms, draft skills, plans) stays in the session scratchpad; nothing is written to the repo for it. Tool defaults such as `docs/superpowers/...` follow this rule too.

## Codex interop

- `AGENTS.md` is the shared instruction file: edit it here. `CLAUDE.md` is a relative symlink to it, so Claude Code reads the same rules. On Windows, `core.symlinks` must be on before cloning.
- There is no `.claude/` or `.mcp.json` to convert, so nothing is generated for Codex and nothing needs regenerating.

## Git / PR Working Policy
- Worktree usage: disabled
- Worktree location: n/a (topic branch in main checkout)
- Base branch: main
- Recorded on: 2026-11-10
