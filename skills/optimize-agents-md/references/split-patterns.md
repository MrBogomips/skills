# Where a moved block goes

Pick the destination from what the block is tied to and which harnesses the project uses (the `signals` and
`layout` lines of the inventory). Why each choice saves context: `loading-and-limits.md`.

| Block is tied to | Claude Code only | Several harnesses |
|---|---|---|
| A folder (`web/`, `api/`) | nested `web/CLAUDE.md`, or `.claude/rules/web.md` with `paths: ["web/**"]` when the folder should stay free of agent files | nested `web/AGENTS.md` with `web/CLAUDE.md` → `AGENTS.md` symlink beside it, **plus** a root pointer |
| A file type across folders (`**/*.sql`) | `.claude/rules/<topic>.md` with `paths:` | a document behind a root pointer |
| A task (release, migrations, incident) that is a step-by-step procedure | an existing or new project skill | a skill in `.agents/skills/<name>/` with a `.claude/skills/<name>` symlink to it (no single folder is read by every agent), or a document behind a root pointer |
| A task that is reference material (conventions, tables) | a document behind a root pointer | a document behind a root pointer |

- **Nested files and new skills need the user's acceptance, one at a time.** They put agent files inside the
  source tree.
- **Never use `@import` to split.** It loads at start in Claude Code (no saving) and Codex ignores it.
- **A new skill** is a bigger step than a document: propose it only for a real procedure, and only when the project
  already uses skills or the user wants one.
- **Documents** go where the project records its working documents (look for a "Working documents" or similar
  section in the instruction file, or a `docs/` convention). If there is none, propose one location once, for
  example `docs/agents/<topic>.md`, and reuse it.

## Pointers

A pointer is one line in the root file, written as a condition the agent can match:

```markdown
- Before changing anything under `db/migrations/`, read `docs/agents/migrations.md`.
- Working in `web/`: its rules are in `web/AGENTS.md`.
- Releasing: use the `release` skill.
```

- Name the trigger (a path, a task), not the content ("see docs for more").
- Every nested `AGENTS.md` gets a root pointer when Codex or another non-Claude agent is in use: a Codex session
  launched at the root never reads it otherwise.
- Safety rules (`content-rules.md`) never move behind a pointer, even when their topic does: they leave the moved
  block and stay in the root file, once.

## Symlinks

- Edit the target of a symlink, never through it (several harnesses refuse, others replace the link with a file).
- A nested pair follows the root convention: real `AGENTS.md`, relative `CLAUDE.md` symlink (`ln -s AGENTS.md CLAUDE.md`).
