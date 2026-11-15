# Wiring the port: static or dynamic

The mode concerns only the generated files, `.agents/` and `.codex/`. `AGENTS.md`, the `CLAUDE.md` link and `.claude/CLAUDE.md` are sources: they are committed in every mode, and editing `AGENTS.md` needs no regeneration. When nothing in `.claude/` or `.mcp.json` converts, there is no generated file and nothing to wire: only the ignore check below applies.

**Shared skills.** A skill in `.claude/skills/` can be a symbolic link to a folder in `.agents/skills/`: a tool that writes its skills once for every agent links them there for Claude Code (OpenSpec 2 does so for its `openspec-*` skills, and keeps its own record, `.openspec-target`, in the same folder). `.agents/skills/` then holds two kinds of files: the owner's, committed and kept current by the owner's own command, and codex-port's output. The block recognises such a skill by the shape of the link, whatever tool made it: it ports none, counts none, and never removes or overwrites their files, even when an older manifest lists them. Git must keep the owner's files in every mode, or each link dangles in a fresh clone and on CI: `--check` fails while git ignores one or while a link dangles, and a run warns of both. A link to a folder anywhere else is an ordinary skill and is ported.

**Ignore check, in every mode.** Before the port, run `git check-ignore -v AGENTS.md CLAUDE.md .claude/CLAUDE.md`. A match means a source is ignored, for example by the ignore block of an earlier dynamic run that still lists `/AGENTS.md`. Warn the user, naming the rule's file and line, and offer to remove the rule (or to add `!/AGENTS.md` at the end of the root `.gitignore`, which also overrides `info/exclude` and `core.excludesFile`). Change it only on approval.

## Static: generated on demand, committed

Static mode is a one-off generation whose output goes into the repository. The project gains no dependency: no script, no CI step, no vendored block, nothing that needs this skill or its tools to be installed. Setup scripts, CI and build files stay as they are, even when the project has them. Nothing keeps the files current between runs: regenerating them is a manual step.

1. **Check that git keeps the output.** Before the port, run `git check-ignore -v .agents/ .codex/ .codex/codex-port.manifest`.
   - No match: go on.
   - A match: warn the user, naming the rule's file and line, and offer to change `.gitignore` so the Codex files are committed for good. Remove the rule when it covers only these paths (for example the ignore block of an earlier dynamic run); otherwise add negations at the end of the root `.gitignore`: `!/.agents/`, `!/.codex/`. A negation in `.gitignore` also overrides `info/exclude` and `core.excludesFile`.
   - Change `.gitignore` only on approval. If the user declines, port anyway, and report that the files stay ignored and will not be committed.
2. **Port** with the block from this skill, never a copy in the project: `sh -c '. <skill dir>/templates/codex-port-block.sh; codex_port'`. Commit `.agents/skills/` and `.codex/`, including `.codex/codex-port.manifest`, which the next run reads, together with the source change. Shared skills (above) are committed already, by their owner; the manifest never lists them.
3. **Record** that the files are generated on demand: re-run the port-to-agents skill in static mode after changing `.claude/` or `.mcp.json`, and commit the output with the source change. The record names no script and no check, because the project has none.
4. **Switching from dynamic:** the checks above find the old ignore block. Offer, separately, to remove the setup wiring the earlier run added (the vendored block and its `codex_port` call); otherwise every setup would regenerate the committed files.

## Dynamic: the Codex files are gitignored

1. Ignore the outputs.
   - Shared: add this to `.gitignore`:
     ```
     # Codex interop: generated from .claude/ and .mcp.json (codex-port, rulesync); never edited
     /.agents/
     /.codex/
     ```
   - Local only: put the same lines in `$(git rev-parse --git-common-dir)/info/exclude`.
   - **With shared skills** (above), ignoring `/.agents/` whole would hide the owner's committed files. Ignore only what codex-port writes, and re-include the owner's files: one negation per owner, by its prefix when its skills share one, so the skills it adds later stay tracked, and its own record files in `.agents/skills/`. For OpenSpec 2:
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

## The vendored block (dynamic mode)

Static mode never vendors the block: it runs it from this skill. The calls below hold in both modes.

- Copy `templates/codex-port-block.sh` verbatim, markers included. On a re-run, replace the text between the markers and leave the rest of the file alone: a project that vendored an older block, which generated `AGENTS.md`, gets the new one this way.
- It needs `git`, `npx` (Node) and network access, but only when something in `.claude/` or `.mcp.json` converts. On CI, a dynamic setup therefore fetches rulesync on every job: this is the cost of running at latest.
- Calls: `codex_port` (check the instruction files, then generate), `--dry-run`, `--check` (no network; what it checks is in SKILL.md, step 7), `--force` (only for a same-name file you have read and folded). Call it as a plain command, never `codex_port || …`, which turns off its error checks.
- If the project has a test runner, offer a behavioural test of the vendored block against a stub `npx` placed first on `PATH`: the instruction checks, generation, removal of output whose source is gone, an older manifest that lists `AGENTS.md` (kept), the hand-written-file refusal, the result checked before the checkout is touched, and, when the project has shared skills, that the stub never sees one and their files survive a manifest that lists them.
- Worktrees: gitignored output is per checkout, so run the setup in every new worktree. Say so in the record.
