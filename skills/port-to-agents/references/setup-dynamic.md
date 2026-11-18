# Dynamic mode: the Codex files are gitignored

1. Ignore the outputs.
   - Shared: add this to `.gitignore`:
     ```
     # Codex interop: generated from .claude/ and .mcp.json (codex-port, rulesync); never edited
     /.agents/
     /.codex/
     ```
   - Local only: put the same lines in `$(git rev-parse --git-common-dir)/info/exclude`.
   - **With shared skills** ([setup-strategies.md](setup-strategies.md)), ignoring `/.agents/` whole would hide the owner's committed files. Ignore only what codex-port writes, and re-include the owner's files: one negation per owner, by its prefix when its skills share one, so the skills it adds later stay tracked, and its own record files in `.agents/skills/`. For OpenSpec 2:
     ```
     # Codex interop: generated from .claude/ and .mcp.json (codex-port, rulesync); never edited.
     # OpenSpec's shared skills, linked from .claude/skills/, are committed.
     /.agents/*
     !/.agents/skills/
     /.agents/skills/*
     !/.agents/skills/openspec-*/
     !/.agents/skills/.openspec-target
     /.codex/
     ```
     Git cannot re-include a file whose parent folder is excluded: keep the `/.agents/*` and `!/.agents/skills/` pair, never `/.agents/`. Check with `git check-ignore -v --no-index .agents/skills/<shared>/SKILL.md` (no match) and the same on a generated skill (a match), then `git ls-files .agents/skills` lists every shared skill.

   Then `git rm --cached -r` whatever codex-port wrote and is tracked: the files its manifest lists, except those under a shared skill's folder (an older manifest can list them, from before their owner took them over), and never a whole `.agents/` that also holds shared skills, which would untrack them and leave the links dangling in every clone. Afterwards `git ls-files .agents/skills` must still list every shared skill; `git add` any that dropped out. `AGENTS.md` stays tracked: it is the shared instruction file. If an earlier run ignored or untracked it, remove that rule and add it back.

   **A tool adopted after an earlier run** may have found codex-port's copies of its skills already in `.agents/skills/` and kept them as the user's: OpenSpec 2 records `keep <skill>` in `.openspec-target`, links to the old copy and never refreshes it (an old `generatedBy` in its frontmatter shows it). Remove those copies and run the tool's update again, so it writes its own; then commit them. The block leaves them alone either way, because the link marks them shared.
2. Find the setup strategy, in this order:

| Look for | Wire the port as |
|---|---|
| a shell setup script: `setup.sh`, `bin/setup`, `scripts/setup*`, `script/bootstrap` | the block inside the script, with one `codex_port` call after the dependencies install |
| `Makefile` / `justfile` / `Taskfile.yml` / `mise.toml` with a setup or bootstrap task | the block vendored as `scripts/codex-port.sh` (block plus `codex_port "$@"`), and one line in the task |
| `package.json` `prepare` / `postinstall` / `setup` | the same vendored file, called from `setup` (not from `postinstall`: that runs on every install, including in consumers) |
| `.devcontainer/devcontainer.json` `postCreateCommand` | the call added to that command |
| CI that installs dependencies itself (workflow steps, composite actions) | that step calls the project's setup entry point instead, so local and CI setup stay one path. With no entry point yet, this is not a strategy of its own: go on to the next part, then wire CI to the script it creates |

3. If there is none, recommend in this order, and let the user choose:
   - **(a) A deterministic `setup.sh`** (`templates/setup.sh`). Recommended when the project has CI, more than one contributor, or worktrees. Fill in its dependency command from the lockfile: `bun.lock` → `bun install`, frozen `--frozen-lockfile`; `package-lock.json` → `npm install`, frozen `npm ci`; `pnpm-lock.yaml` → `pnpm install`, frozen `--frozen-lockfile`; `yarn.lock` → `yarn install`, frozen `--immutable`; `uv.lock` → `uv sync`, frozen `--locked`; nothing → leave it out. Wire CI to call `./setup.sh --ci`.
   - **(b) An instruction in `AGENTS.md`** (shared): "When `.agents/` or `.codex/` is missing, or older than its source, run the port-to-agents skill (or the block)." Nothing deterministic runs on CI or for a contributor whose agent lacks the skill; both tools read the instruction.
   - **(c) The same instruction in `CLAUDE.local.md`** (personal). Nothing shared changes except the ignore rules, so pair it with the local `info/exclude`.
