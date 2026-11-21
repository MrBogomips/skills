# DoD.md

A `DoD.md` states what "done" means for its directory and everything below it, and what to do once it is
reached. Two sections with fixed headings, free Markdown inside:

```markdown
# Definition of Done

## Requirements

- [ ] Tests pass: `npm test`
- [ ] Pull request merged into `main`
- [ ] Changelog has an entry for user-visible changes

## On Done

- Delete without asking: `drafts/**`, `*.tmp`
- Merge approved pull requests: yes, squash
- Never touch: branches `release/*`
- Run: `scripts/sync.sh`
```

**Requirements**: an item with a command in backticks passes when the command exits 0, run from the file's
directory; an item without one is judged on evidence. The checkboxes are never ticked in the file. A section
titled `## Definition of Done` (older files) is read as *Requirements*.

**On Done** lines with a defined meaning; other sentences are instructions, within the skill's safety rules:

| Line | Effect |
|---|---|
| `Delete without asking: <patterns>` | matching untracked files in this file's subtree are deleted without a yes |
| `Merge approved pull requests: yes[, <method>]` | root file only: an approved, green pull request is merged |
| `Never touch: <things>` | no treatment touches the named branches, files or directories |
| `Run: <command>` | runs after the default treatments, from this file's directory |
| `Do not <default treatment>` | switches it off, e.g. "Do not delete remote branches" |
| `Does not apply here: <criterion>` | a nested file drops an inherited criterion for its subtree |

A file with one section only: the other falls back to the level above or the defaults, and the report says so.

**Several files**: paths, patterns and commands are relative to the file's directory. Never above the
repository root or across a submodule. `DOD.md` and `dod.md` are honored too; two spellings in one directory
is reported (`dod_name_conflict`) and the user chooses.
