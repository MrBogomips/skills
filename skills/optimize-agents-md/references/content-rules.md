# Classifying each block

Read the instruction files one block at a time (a section, or a run of related bullets) and give each block one
verdict. A line stays only if it saves an agent exploration time or prevents a mistake.

| Verdict | When | Proposal |
|---|---|---|
| **keep** | Needed on most tasks, or a safety rule (below), at any size | stays in the root file, tightened if wordy |
| **move** | Needed only for some paths or some tasks **and**, without its safety rules, at least the split threshold (default 20 lines) | `split-patterns.md` decides where |
| **keep (short)** | Needed only for some paths or tasks, but under the threshold | stays in the root file: a pointer would cost almost as much |
| **delete: history** | Changelog, dates, "we used to", "moved from X to Y", "fixed in PR #n", migration stories | delete; see below |
| **delete: generic** | Advice any competent agent follows anyway ("write clean code", "use meaningful names") | delete |
| **delete: derivable** | Restates what the code, config or README already says plainly (file trees, dependency lists) | delete, unless agents keep getting it wrong |
| **stale** | A path that does not exist, or a command the project does not declare | one grouped question: fix or delete |
| **overlap** | Repeats a project skill | see "Skills" below |
| **conflict** | Contradicts a project skill, another instruction file, another line of the same file, or the code | ask the user which one is right |

## Safety rules

A safety rule prevents harm that is hard to undo or that leaks: lost data, leaked secrets or personal data,
broken production, rewritten shared history, irreversible or outward actions (publishing, releasing, deleting).
"Never push to `main`", "never commit `.env`", "never edit a merged migration" are safety rules. "Never use
`moment`", "no class components" are style rules, however strongly worded: they move with their block.

A safety rule is a standalone prohibition that holds even when nobody is running the procedure it sits in.
"Never release on Fridays" is one; "run the migration on staging first" is a step of the release procedure and
moves with it.

A safety rule stays in the root file at any size, and only there: when its block moves, the rule is taken out of
the block, not copied. The threshold counts the block's content lines, without its heading and without its safety
rules.

## Stale references

Check by reading, never by running a command with side effects: paths with a listing, commands against the
package manifest scripts, Makefile targets, workflow files. A reference that may live outside the repository (a
user-level slash command, a CI workflow in another repository, a team calendar) is a question, not a deletion.
When many references are stale (a skeleton project), ask once whether they are plans or mistakes.

## History is not rationale

- **History** tells what happened: delete it from instruction files. Explain once, in the report, why: git already
  keeps it (`git log`, `git blame`, commit messages, pull requests), the agent pays for it on every run, and an
  agent reading "we moved from Redux to Zustand" learns nothing it can't see in the code. Decisions that must
  outlive the code belong in ADRs or a `CHANGELOG.md`, which agents read on demand.
- **Rationale** tells why a rule exists, in one line ("Python 3.11 is pinned because the deploy image ships
  3.11"). Keep it: without it an agent "fixes" the rule.
- A history line that still implies a rule ("we dropped GraphQL") becomes the rule ("REST only, no GraphQL") and
  the story goes.
- **No git** in the project: don't delete history. Propose moving it to a `CHANGELOG.md` or a `docs/` file and
  say why.

## Skills

Project skills are the ones agents of this project use: `.claude/skills/*/SKILL.md`, `.agents/skills/*/SKILL.md`.
A top-level `skills/` folder may instead be the product the repository ships (a skills library): read the README
and ask if unsure; skills that are the product are subject matter, not instructions.

Overlap and conflict with a skill are decided here, whatever the block's size: the threshold does not apply.

- **Overlap** (same content, no contradiction): the skill is the home for a procedure, because it loads only when
  needed and its description already advertises it. Propose deleting the copy from the instruction file, but only
  when every harness in use can see the skill (`loading-and-limits.md`, "Who sees which skills"); keep at most a
  one-line pointer when the skill would not obviously trigger. A skill only some harnesses see keeps the text, or
  a pointer to the skill file that any agent can read.
- **Conflict** (they disagree, e.g. tag `vX.Y.Z` vs `release-X.Y.Z`): never pick a side silently. Ask the user
  which is right and where the merged content lives (the skill, the instruction file, or both with the skill as
  source). Lines that exist only in the instruction file are not conflicts: propose moving them into the skill, and show
the skill's resulting diff (reordering inside the skill is fine; say so).
- A skill generated or managed by a framework or tool (its header says so, or the framework's docs do) is never
  edited by hand: integrate into the instruction file or the framework's own source, and say so.

## Never touch

- Content written to an instruction file by a tool between markers (`<!-- BEGIN … -->`, `# >>> … >>>`): leave it.
- Files the user said are out of scope; the user-level files (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`) unless
  the user asked to include them.
