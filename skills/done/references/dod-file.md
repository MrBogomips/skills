# DoD.md

A `DoD.md` states what "done" means for the directory it sits in and everything below it, and what to do once
it is reached.

## Format

Two sections with fixed headings; the content is free Markdown.

```markdown
# Definition of Done

## Definition of Done

- [ ] Tests pass: `npm test`
- [ ] Lint is clean: `npm run lint`
- [ ] Pull request merged into `main`
- [ ] Changelog has an entry for user-visible changes

## On Done

- Delete without asking: `drafts/**`, `*.tmp`
- Merge approved pull requests: yes, squash
- Never touch: branches `release/*`
- Run: `scripts/dod_ondone.sh`
```

**Definition of Done** is a checklist. An item with a command in backticks is satisfied when the command exits
with status 0. An item without a command is judged with evidence, like the generic criteria. The checkboxes
are never ticked in the file: the result goes in the report.

**On Done** lists treatments and authorizations, in plain sentences. The ones with a defined meaning:

| Line | Effect |
|---|---|
| `Delete without asking: <patterns>` | untracked files matching the patterns, inside this file's subtree, are deleted without confirmation |
| `Merge approved pull requests: yes[, <method>]` | an approved pull request with passing checks is merged without asking (root file only) |
| `Never touch: <things>` | the named branches, files or directories are left alone by every treatment |
| `Run: <command>` | the command runs after the default treatments, from this file's directory |
| `Do not <default treatment>` | switches that default off, for example "Do not delete remote branches" |

Other sentences are instructions to follow at that point, within the safety rules of the skill.

A file with only one of the two sections is valid: the missing section falls back to the level above, or to the
defaults, and the report says so.

## Several files

- Location: the repository root and any directory that needs its own rules.
- Paths, patterns and commands are relative to the file's directory. Commands run from there.
- Chain for a path: the `DoD.md` of its directory, then of each ancestor, up to the repository root. Outside
  git, only the working directory's file. Never above the root, never across a submodule boundary.
- Nearest first, then upward; the levels add up. On conflict the more specific file wins for its subtree.
- To drop an inherited rule, a nested file says so: `Does not apply here: changelog entry`.
- Pull request, merge, branch and session-title lines count only in the topmost file.
- The name is `DoD.md`. Other letter cases (`DOD.md`, `dod.md`) are honored when found. Two spellings in one
  directory is an error to report, not to resolve silently.

Example: with `DoD.md`, `packages/api/DoD.md` and `docs/DoD.md`, a session that changed
`packages/api/src/x.ts` and `README.md` loads the first two. `x.ts` must satisfy `packages/api/DoD.md` and
then the root file; `README.md` only the root file; `docs/DoD.md` is not loaded.

## Creating or revising one (`done init [dir]`)

1. Read the project instructions, the CI configuration and the existing `DoD.md` files above `dir`.
2. Draft the file from the generic DoD, made specific to the repository: its real test, lint and build
   commands, its integration branch, its pull request flow, the folders where drafts accumulate. For a nested
   directory, write only what differs from the levels above.
3. Keep it short: criteria someone can check, not aspirations. Leave out anything the levels above already say.
4. Show the draft. If the file exists, show the change as a diff.
5. Ask whether the file is committed (default: yes, so the team shares it).
6. Write it only after the user confirms. Do not commit it unless asked.

The same flow runs when the user accepts the offer made after a run without any `DoD.md`: the draft starts
from the criteria that run actually used.

## Project scripts

A `DoD.md` may delegate checks or treatments to scripts in the repository. They run only when a `DoD.md` names
them; a script that merely exists is never executed.

- Suggested names: `scripts/dod_check.sh` (exit status 0 means the criteria it covers are satisfied; it prints
  what failed) and `scripts/dod_ondone.sh`. If the repository keeps its scripts elsewhere, follow that.
- Offer to create one during `init` only when several criteria need more than one command each. Write it
  after the user confirms, and reference it from the file, as a checklist item that carries the script as its
  command.
- A check script must not change anything. An on-done script must be safe to run twice.
