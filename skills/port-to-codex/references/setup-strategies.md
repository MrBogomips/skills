# Wiring the port: static or dynamic

The mode concerns only the generated files, `.agents/` and `.codex/`. `AGENTS.md`, the `CLAUDE.md` link and `.claude/CLAUDE.md` are sources: they are committed in every mode, and editing `AGENTS.md` needs no regeneration. When nothing in `.claude/` or `.mcp.json` converts, there is no generated file and nothing to wire: only the ignore check below applies.

**Ignore check, in every mode.** Before the port, run `git check-ignore -v AGENTS.md CLAUDE.md .claude/CLAUDE.md`. A match means a source is ignored, for example by the ignore block of an earlier dynamic run that still lists `/AGENTS.md`. Warn the user, naming the rule's file and line, and offer to remove the rule (or to add `!/AGENTS.md` at the end of the root `.gitignore`, which also overrides `info/exclude` and `core.excludesFile`). Change it only on approval.

## Static: generated on demand, committed

Static mode is a one-off generation whose output goes into the repository. The project gains no dependency: no script, no CI step, no vendored block, nothing that needs this skill or its tools to be installed. Setup scripts, CI and build files stay as they are, even when the project has them. Nothing keeps the files current between runs: regenerating them is a manual step.

1. **Check that git keeps the output.** Before the port, run `git check-ignore -v .agents/ .codex/ .codex/codex-port.manifest`.
   - No match: go on.
   - A match: warn the user, naming the rule's file and line, and offer to change `.gitignore` so the Codex files are committed for good. Remove the rule when it covers only these paths (for example the ignore block of an earlier dynamic run); otherwise add negations at the end of the root `.gitignore`: `!/.agents/`, `!/.codex/`. A negation in `.gitignore` also overrides `info/exclude` and `core.excludesFile`.
   - Change `.gitignore` only on approval. If the user declines, port anyway, and report that the files stay ignored and will not be committed.
2. **Port** with the block from this skill, never a copy in the project: `sh -c '. <skill dir>/templates/codex-port-block.sh; codex_port'`. Commit `.agents/skills/` and `.codex/`, including `.codex/codex-port.manifest`, which the next run reads, together with the source change.
3. **Record** that the files are generated on demand: re-run the port-to-codex skill in static mode after changing `.claude/` or `.mcp.json`, and commit the output with the source change. The record names no script and no check, because the project has none.
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

   Then `git rm --cached -r` whatever of them is tracked. `AGENTS.md` stays tracked: it is the shared instruction file. If an earlier run ignored or untracked it, remove that rule and add it back.
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
   - **(b) An instruction in `AGENTS.md`** (shared): "When `.agents/` or `.codex/` is missing, or older than its source, run the port-to-codex skill (or the block)." Nothing deterministic runs on CI or for a contributor whose agent lacks the skill; both tools read the instruction.
   - **(c) The same instruction in `CLAUDE.local.md`** (personal). Nothing shared changes except the ignore rules, so pair it with the local `info/exclude`.

## The vendored block (dynamic mode)

Static mode never vendors the block: it runs it from this skill. The calls below hold in both modes.

- Copy `templates/codex-port-block.sh` verbatim, markers included. On a re-run, replace the text between the markers and leave the rest of the file alone: a project that vendored an older block, which generated `AGENTS.md`, gets the new one this way.
- It needs `git`, `npx` (Node) and network access, but only when something in `.claude/` or `.mcp.json` converts. On CI, a dynamic setup therefore fetches rulesync on every job: this is the cost of running at latest.
- Calls: `codex_port` (check the instruction files, then generate), `--dry-run`, `--check` (no network; what it checks is in SKILL.md, step 7), `--force` (only for a same-name file you have read and folded). Call it as a plain command, never `codex_port || …`, which turns off its error checks.
- If the project has a test runner, offer a behavioural test of the vendored block against a stub `npx` placed first on `PATH`: the instruction checks, generation, removal of output whose source is gone, an older manifest that lists `AGENTS.md` (kept), the hand-written-file refusal, and the result checked before the checkout is touched.
- Worktrees: gitignored output is per checkout, so run the setup in every new worktree. Say so in the record.
