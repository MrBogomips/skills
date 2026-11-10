# CLAUDE.md

Guidance for working in this repository.

## What this repository is

A collection of small, general-purpose agent skills, shared through two channels built from the same files:

- **Any harness**, via the [`skills` CLI](https://github.com/vercel-labs/skills): `npx skills add MrBogomips/skills` (pick skills with `--skill <name>`, agents with `-a <agent>`, user scope with `-g`).
- **Claude Code plugin marketplace**: `/plugin marketplace add MrBogomips/skills`, then `/plugin install <skill>@mrbogomips-skills`.

There is no build step. The repository is Markdown skills plus one JSON manifest.

## Layout

- `skills/<name>/SKILL.md`: one directory per skill. Supporting files (`references/`, `scripts/`, `assets/`) go inside that directory.
- `.claude-plugin/marketplace.json`: the Claude Code marketplace, named `mrbogomips-skills`. It has **one plugin per skill**. Each entry has `"name": "<skill>"`, `"source": "./"`, `"strict": false` and `"skills": ["./skills/<skill>"]`, plus `description`, `version`, `category` and `tags`. Because of `strict: false`, the entry is the whole plugin definition, so there is no `plugin.json`.

The `skills` CLI discovers skills in `skills/` and also reads the skill paths declared in `marketplace.json`. When a skill is found both ways, it is listed once.

- `tests/`: `validate.sh` (repository checks) and `selftest.sh` (the validator's own tests), both run by `.github/workflows/validate.yml` on pushes and pull requests to `main`.
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

- **Add**: run `npx skills init <name>` from inside `skills/` (it writes `<name>/SKILL.md`). Then add the skill's plugin entry to `marketplace.json`.
- **Change**: bump the skill's `version` in its `marketplace.json` entry. Claude Code uses the version to decide whether an installed plugin needs updating.
- **Rename or remove**: change the directory, the frontmatter `name` and the manifest entry together. Existing installs keep the old name.

## Verification

After any change, run from the repo root (requires `jq`):

```bash
bash tests/validate.sh                             # marketplace.json and skills/ agree (CI runs this)
claude plugin validate . --strict                  # marketplace.json schema; fails while there are no plugins
DISABLE_TELEMETRY=1 npx -y skills add ./ --list    # what the skills CLI discovers (Node >= 22.20)
```

`tests/validate.sh` exists because the other two commands don't report a manifest path with no `SKILL.md`, a frontmatter `name` that differs from its directory, or a skill missing from the manifest. It also enforces the one-plugin-per-skill entry shape and the frontmatter limits.

When you change `tests/validate.sh`, add or adjust a case in `tests/selftest.sh` and run `bash tests/selftest.sh`; CI runs it before the validator. Both scripts must stay bash 3.2 compatible: run them with `/bin/bash` on macOS to check.

To try the marketplace locally in Claude Code: `/plugin marketplace add ./`, then `/plugin install <skill>@mrbogomips-skills`.

## Working documents

- **Authoritative**: `skills/` and `.claude-plugin/marketplace.json`.
- **AI working material** (brainstorms, draft skills, plans) stays in the session scratchpad; nothing is written to the repo for it. Tool defaults such as `docs/superpowers/...` follow this rule too.

## Git / PR Working Policy
- Worktree usage: disabled
- Worktree location: n/a (topic branch in main checkout)
- Base branch: main
- Recorded on: 2026-11-10
