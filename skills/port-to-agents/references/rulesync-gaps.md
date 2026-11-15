# What rulesync carries to Codex, and what it does not

The table describes rulesync's `convert --from claudecode --to codexcli` at project scope, as observed with 43.8.0. Re-check it against the version in use: `npx --yes rulesync@latest docs reference/supported-tools`.

| Claude Code | Codex | Notes |
|---|---|---|
| `CLAUDE.md` | not converted | `AGENTS.md` is the shared file, written by hand; `CLAUDE.md` is a symlink to it and `.claude/CLAUDE.md` holds Claude Code's own lines (`instruction-layer.md`). The block never passes rulesync's `rules` feature, which would overwrite `AGENTS.md` with a copy of `CLAUDE.md`. |
| `.claude/rules/` | not ported | Codex reads no path-scoped rules. Move what every agent needs into `AGENTS.md` (`instruction-layer.md` §5). |
| `.claude/skills/<n>/` | `.agents/skills/<n>/` | `SKILL.md` and its supporting files. |
| `disable-model-invocation: true` | dropped by rulesync | The block adds `.agents/skills/<n>/agents/openai.yaml` with `policy: allow_implicit_invocation: false`. Codex then runs the skill only when invoked as `$<n>` (Codex docs, Build skills). |
| `.claude/agents/<n>.md` | `.codex/agents/<n>.toml` | Keeps `name`, `description` and `developer_instructions`. Drops `model`, `effort`, `tools` and `skills`, so a read-only Claude agent can edit files in Codex. |
| `.claude/commands/` | not ported | Codex has no project commands. |
| `.mcp.json` | `.codex/config.toml` | Only when the file exists (the block's feature detection). |
| hooks and permissions in `.claude/settings.json` | `.codex/hooks.json`, `.codex/config.toml`, `.codex/rules/` | Only when present. Without them, rulesync still writes an approval policy (`approval_policy`, `approvals_reviewer = "auto_review"`) that nobody asked for. That is why the block passes only the features the sources have. |
| `CLAUDE.local.md`, `settings.local.json` | not ported | Personal (`instruction-layer.md` §6). |

## Effects to tell the user about

- **Trust.** Codex loads the project's `.codex/` only when the user has trusted the project, so the agents and the config wait for the trust prompt. Skills in `.agents/skills/` are found from the working directory up to the repository root.
- **Commands.** A project command can become a skill: `.claude/skills/<n>/SKILL.md` with `disable-model-invocation: true` stays `/n` in Claude Code and becomes `$n` in Codex. Offer this per command, and only for commands that no skill already covers. Never offer it for commands a framework generates. Without an answer, leave the command as it is and list it as not carried.
- **The "not carried" list for the record.** List the commands, the agents' model, effort, tools and preloaded skills, the `.claude/rules/` left out of `AGENTS.md`, any imports that were turned into pointers, instructions above the git root, and the trust prompt.
