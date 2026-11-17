# AGENTS.md

The rules for every coding agent working in this repository.

## What this repository is

A collection of small, general-purpose agent skills, shared through two channels built from the same files:

- **Any harness**, via the [`skills` CLI](https://github.com/vercel-labs/skills): `npx skills add MrBogomips/skills` (pick skills with `--skill <name>`, agents with `-a <agent>`, user scope with `-g`).
- **Claude Code plugin**: the whole repository is one plugin, `skills`, with every skill in it. It is listed in the `mrbogomips` marketplace, which lives in its own repository and also lists the author's other plugins: `/plugin marketplace add MrBogomips/claude-plugins`, then `/plugin install skills@mrbogomips`. Skills are invoked as `/skills:<name>`. Users who want a single skill use the `skills` CLI instead.

There is no build step. The repository is Markdown skills plus one JSON plugin manifest.

## Layout

- `skills/<name>/SKILL.md`: one directory per skill. Supporting files (`references/`, `scripts/`, `assets/`) go inside that directory.
- `.claude-plugin/plugin.json`: the manifest of the `skills` plugin, with `name`, `version`, `description`, `author` and `keywords`. It has **no `skills` field**, so Claude Code loads every `skills/<name>/SKILL.md`. There is no `marketplace.json` here: the marketplace entry (source `github`, `category`, `tags`) lives in `MrBogomips/claude-plugins` and carries no `version`, so the version is read from `plugin.json`.
- `tests/`: `validate.sh` (repository checks) and `selftest.sh` (the validator's own tests), both run by `.github/workflows/validate.yml` on pushes and pull requests to `main`.
- `DoD.md`: the Definition of Done that the `done` skill checks a session against.
- `README.md` keeps the public skill list and install instructions; update it whenever a skill is added, renamed or removed.

## Portability rules

A skill has to work in every harness the `skills` CLI targets, not only in Claude Code.

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

## The AGENTS.md skills must agree

`init-agents-md` (create), `optimize-agents-md` (slim and restructure) and `port-to-agents` (port a Claude Code setup to Codex) work on the same files and must stay coherent. When you change one, check the other two in the same pull request:

- **Instruction layer**: all three target one real `AGENTS.md`, `CLAUDE.md` as a relative symlink to it, and Claude Code-only lines in `.claude/CLAUDE.md`. None proposes an `@AGENTS.md` import or a generated copy.
- **Loading facts**: how each harness loads instruction files and skills is written in `skills/port-to-agents/references/instruction-files.md` and `skills/optimize-agents-md/references/loading-and-limits.md`. A skill can't read another skill's files, so each keeps its own copy: update both copies together, with the date and versions checked.
- **Scope and names**: each skill hands off to the others by their current names and never does their work.

## Verification

After any change, run from the repo root (requires `jq`):

```bash
bash tests/validate.sh                             # plugin.json and skills/ agree (CI runs this)
python3 -m unittest discover -s tests -p 'test_*.py'  # unit tests of bundled scripts (CI runs this)
CODEX_PORT_SH=dash python3 -m unittest discover -s tests -p 'test_codex_port_block.py'  # the POSIX block under dash too
claude plugin validate . --strict                  # plugin.json schema
DISABLE_TELEMETRY=1 npx -y skills add ./ --list    # what the skills CLI discovers (Node >= 22.20)
```

`tests/validate.sh` exists because the other two commands don't report a skill directory with no `SKILL.md` or a frontmatter `name` that differs from its directory. It also enforces the frontmatter limits, the plugin name and semver version, the absence of a `skills` field (which would stop the default scan of `skills/`) and of a `marketplace.json`.

When you change `tests/validate.sh`, add or adjust a case in `tests/selftest.sh` and run `bash tests/selftest.sh`; CI runs it before the validator. Both scripts must stay bash 3.2 compatible: run them with `/bin/bash` on macOS to check.

To try the plugin locally in Claude Code without installing it: `claude --plugin-dir .` (the skills appear as `/skills:<name>`).

## Working documents

- **Authoritative**: `skills/` and `.claude-plugin/plugin.json`.
- **AI working material** (brainstorms, draft skills, plans) stays in the session scratchpad; nothing is written to the repo for it. Tool defaults such as `docs/superpowers/...` follow this rule too.

## Codex interop

- `AGENTS.md` is the shared instruction file: edit it here. `CLAUDE.md` is a relative symlink to it, so Claude Code reads the same rules. On Windows, `core.symlinks` must be on before cloning.
- There is no `.claude/` or `.mcp.json` to convert, so nothing is generated for Codex and nothing needs regenerating.

## Git / PR Working Policy
- Worktree usage: disabled
- Worktree location: n/a (topic branch in main checkout)
- Base branch: main
- Recorded on: 2026-11-10
