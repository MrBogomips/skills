# DoD.md

A `DoD.md` states what "done" means for its directory and everything below it, and what to do once it is
reached. Two sections with fixed headings, free Markdown inside:

```markdown
# Definition of Done

## Requirements

- [ ] Tests pass: `npm test`
- [ ] Pull request merged into `main`
- [ ] Changelog has an entry for user-visible changes
- [ ] When the user manual changed:
  - [ ] its screenshots in `docs/images/` show the current interface
  - [ ] `docs/manual.pdf` is rebuilt with `docs/build.sh`

## On Done

- Delete without asking: `drafts/**`, `*.tmp`
- Merge approved pull requests: yes, squash
- Never touch: branches `release/*`
- Run: `scripts/sync.sh`
```

**Requirements**: an item with a command in backticks passes when the command exits 0, run from the file's
directory; an item without one is judged on evidence. The checkboxes are never ticked in the file. A section
titled `## Definition of Done` (older files) is read as *Requirements*.

How items are written:

- **One condition per item**, short enough to be checked and reported on its own. Never chain conditions in
  one sentence with `;`, `and`, `:` or a trailing "The pull request says...": each becomes its own item.
- **Sub-items** group conditions that share a trigger or a scope ("When the manual changed:", "At a
  release:"). The parent states only that trigger or scope and has no command; it passes when every sub-item
  passes, and when its trigger does not hold the whole group is not applicable. One level of nesting at most.
- **A condition that applies only sometimes** starts with it ("For a plugin with a mod: ..."), or becomes a
  group when several items share it.
- Commands, paths and file names go in backticks.

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
