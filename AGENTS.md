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
- `tests/`: `validate.sh` (repository checks), `selftest.sh` (the validator's own tests) and `test-kaizen-stop-gate.sh` (the kaizen Stop hook), all run by `.github/workflows/validate.yml` on pushes and pull requests to `main`; `scenarios/` holds manual scenario checklists for the plugins.
- `skill-maker/shared/rules/`: the authoring rulebook every skill here follows. `skill-maker/shared/official-baseline.json` records the official sources it rests on; `.github/scripts/official_drift.py`, run monthly by `.github/workflows/official-drift.yml`, opens an `official-drift` issue when one changes (see [Official drift](#official-drift)).
- `DESIGN.md`: the value gate a skill or plugin must pass to be added, and how a skill declares its minimum model and effort.
- `DoD.md`: the Definition of Done that the `done` skill checks a session against.
- `README.md` keeps the public skill and plugin lists and install instructions; update it whenever a skill or plugin is added, renamed or removed.
- **Component READMEs**: every plugin and every distributed skill has a short `README.md` that follows the `skill-maker` contract (`skill-maker/skills/skill-readme/references/contract.md`): what it does and why, never a retelling of `SKILL.md`. The `skills` plugin's README is `skills/README.md`, because the root `README.md` is the repository page. Write or revise them with `/skill-maker:skill-readme`.

## Portability rules

A skill in `skills/` has to work in every harness the `skills` CLI targets, not only in Claude Code. Skills inside a plugin folder follow [Plugins](#plugins) instead.

- **Frontmatter** follows the Agent Skills spec (agentskills.io): `name`, `description`, and optionally `license`, `compatibility`, `metadata`, `allowed-tools`. Other harnesses ignore Claude Code-only keys, so a skill must still work without them.
- **`name` equals the directory name** (lowercase, hyphens). The `skills` CLI installs a skill under its frontmatter `name`, so a mismatch gives the skill different identities in the two channels. Neither tool reports it (see Verification).
- **`description`** says what the skill does and when to use it. Before a skill loads, the description is the only part an agent sees.
- **English**: every skill and plugin here is public (published through this repository, the marketplace or the `skills` CLI), so frontmatter, `SKILL.md`, references, agent files, README and examples are in English. Trigger phrases are English too; a term from another language is allowed only when English speakers commonly use it. There is no exception for skills whose subject is writing in several languages. The skill still talks to the user in their language. A custom skill (project- or user-scoped and never published) follows the language of the project's instruction file, then of the user's instructions, else English.
- **Authoring rules**: the general rules for skills, agents and plugins are in `skill-maker/shared/rules/`; check a skill against them with `/skill-maker:skill-check`.
- **Bundled files** are referenced by paths relative to the skill directory. Never use `${CLAUDE_PLUGIN_ROOT}` or files outside `skills/<name>/`: the `skills` CLI installs only the skill directory into each agent's skills folder.
- **No dependence on the author's setup**: no personal paths, no reliance on `~/.claude` rules or memory, and no assumption that particular MCP servers, plugins or CLIs are installed. Detect them at runtime or ask the user.
- **Bundled scripts** run on users' machines, so keep them macOS/BSD-compatible: no `grep -P`, no `head -n -1`, bash 3.2.

## Adding, changing, removing a skill

- **Value gate first**: a new skill or plugin, or a change of scope to one, must pass the value gate in [`DESIGN.md`](DESIGN.md). It adds what frontier models and harnesses do not already do well, as a method or process, never as a copy of a native capability. The gate also says how a skill declares its minimum model and effort.
- **Add**: run `npx skills init <name>` from inside `skills/` (it writes `<name>/SKILL.md`). The plugin picks it up with no manifest change.
- **Baseline first** (rule T1): before writing a skill, run its task on a fresh agent without it and record how it fails in `tests/scenarios/<skill>/baseline.md`. Required for a skill that enforces a discipline (approvals, checks before claiming done), recommended for the others.
- **Version**: every pull request that changes what a skill does bumps `version` in `.claude-plugin/plugin.json`, once per pull request: patch for a fix, minor for a new skill or a compatible extension, major when a skill is renamed or removed or its behavior changes incompatibly. Claude Code updates installed plugins only when the version changes.
- **Backends, not copies**: two skills that would differ only in how they reach a model or tool (an API, a local CLI) are one skill with backends and a setting, not copies: a skill cannot share files with another.
- **Rename or remove**: change the directory and the frontmatter `name` together. In Claude Code the invocation changes with it (`/skills:<old>` stops working); `skills` CLI installs keep the old name until removed.

## Plugins

A top-level plugin folder is for work that needs Claude Code plugin features: hooks, agents, `userConfig`, `${CLAUDE_PLUGIN_ROOT}`, files shared by several skills. Anything a single portable skill can do belongs in `skills/` instead.

- **Manifest**: `<plugin>/.claude-plugin/plugin.json`, with `name` equal to the folder name, a semver `version`, and no `skills` field. No `marketplace.json`.
- **Marketplace entry**: in `MrBogomips/claude-plugins`, with source `{"source": "git-subdir", "url": "https://github.com/MrBogomips/skills.git", "path": "<plugin>"}` and no `version`. Claude Code checks out only that folder, so a plugin may use nothing outside it.
- **Skill names**: the frontmatter `name` equals the directory, and names are specific enough to install at user scope (`voice-write`, not `write`). Skills hand off to each other as `<plugin>:<skill>`.
- **Standalone or plugin-only**: every plugin README has an **Installation** section that says whether its skills also work installed alone with `npx skills add MrBogomips/skills/<plugin>`, and what is lost that way. A skill that reads `${CLAUDE_PLUGIN_ROOT}`, `${user_config.*}` or files outside its own folder is plugin-only. Keep that statement, and the plugin table in `README.md`, in step with the code.
- **Version**: each plugin has its own `version` in its own `plugin.json`, bumped per pull request with the same patch/minor/major rule as above. The root `skills` version does not change for plugin work.
- **Tests**: a plugin's automated tests live in `tests/` and run in CI; its manual scenarios live in `tests/scenarios/<skill>/` (see `tests/scenarios/README.md`).

## Verification

After any change, run from the repo root (requires `jq`):

```bash
bash tests/validate.sh                             # every plugin.json and its skills/ agree (CI runs this)
bash tests/test-kaizen-stop-gate.sh                # the kaizen Stop hook (CI runs this; needs git)
python3 -m unittest discover -s tests -p 'test_*.py'  # unit tests of bundled scripts (CI runs this)
claude plugin validate . --strict                  # plugin.json schema of the root plugin
claude plugin validate ./kaizen --strict           # ... and of each plugin folder
claude plugin validate ./personal-voice --strict
claude plugin validate ./skill-maker --strict
python3 skill-maker/scripts/validate.py --no-claude --portable .  # root skills: rulebook lint and README contract
for p in kaizen personal-voice skill-maker; do python3 skill-maker/scripts/validate.py --no-claude $p; done  # each plugin folder
DISABLE_TELEMETRY=1 npx -y skills add ./ --list    # what the skills CLI discovers (Node >= 22.20): only skills/
DISABLE_TELEMETRY=1 npx -y skills add ./kaizen --list  # a plugin's skills, reached by its folder
```

`tests/validate.sh` exists because the other two commands don't report a skill directory with no `SKILL.md` or a frontmatter `name` that differs from its directory. It also enforces the frontmatter limits, each plugin's name (equal to its folder for plugin folders) and semver version, the absence of a `skills` field (which would stop the default scan of `skills/`) and of a `marketplace.json`.

When you change `tests/validate.sh`, add or adjust a case in `tests/selftest.sh` and run `bash tests/selftest.sh`; CI runs it before the validator. Both scripts must stay bash 3.2 compatible: run them with `/bin/bash` on macOS to check.

To try a plugin locally in Claude Code without installing it: `claude --plugin-dir .` (the skills appear as `/skills:<name>`), or `claude --plugin-dir ./<plugin>` for a plugin folder.

## Official drift

skill-maker's rulebook rests on official sources (the official plugins and documentation pages in `skill-maker/shared/official-baseline.json`). When the monthly workflow opens an `official-drift` issue:

1. Fetch each changed source into the session scratchpad: `gh api` on the compare link for a plugin, the `.md` page for a documentation page.
2. Dispatch the `rulebook-reviewer` agent in `drift` mode with the affected rule IDs listed in the issue and those files.
3. Apply the agreed rule changes, then record the new commits and hashes with `GITHUB_TOKEN=$(gh auth token) python3 .github/scripts/official_drift.py --refresh` (with a python.org build on macOS, also set `SSL_CERT_FILE=/etc/ssl/cert.pem`).
4. Bump skill-maker's version (patch, or minor when a rule changes meaning) and open one pull request that closes the issue.

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
