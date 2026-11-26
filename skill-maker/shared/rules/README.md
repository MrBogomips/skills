# Authoring rulebook

The rules skill-maker checks skills, agents and plugins against. Each rule has a stable ID that findings
cite, a reason, and a line that says who checks it: the validator (`scripts/validate.py`), the
`rulebook-reviewer` agent, or both.

| File | IDs | Covers |
|---|---|---|
| [value.md](value.md) | V1–V6 | Whether a skill should exist: value over native features, thinness, retirement, minimum model |
| [skill-md.md](skill-md.md) | S1–S12 | `SKILL.md`, descriptions, language, wording, scripts, frontmatter |
| [testing.md](testing.md) | T1–T8 | Testing a skill before and after writing it |
| [structure.md](structure.md) | P1–P6 | Names, paths, placeholders, manifests, files that must not ship |
| [claude-code.md](claude-code.md) | C1–C8 | Agents, hooks and commands (Claude Code only) |

## Precedence

1. The rules of the repository or project the skill lives in (its `AGENTS.md` or `CLAUDE.md`).
2. Official guidance: the documentation pages and the official tools listed in
   [`../official-references.md`](../official-references.md).
3. This rulebook, which settles what the first two leave open.

A rule marked `Official source: <key>` rests on official guidance. The key names an entry of
[`../official-baseline.json`](../official-baseline.json). When that source changes, the rule is
re-checked (see the repository's `AGENTS.md`, section Official drift).

## Public and custom skills

A skill is **public** when it is distributed through a public repository, a marketplace or the `skills`
CLI. It is **custom** when it is scoped to a project or a user and never published. Rule S3 sets the
language of each.
