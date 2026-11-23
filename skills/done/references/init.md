# Creating or revising the DoD.md (`done init`)

The `DoD.md` lives at the repository root and states what "done" means for the repository and what to do once
it is reached. Two sections with fixed headings, free Markdown inside:

```markdown
# Definition of Done

## Requirements

- [ ] Tests pass: `npm test`
- [ ] Pull request merged into `main`
- [ ] Changelog has an entry for user-visible changes
- [ ] When the user manual changed:
  - [ ] its screenshots in `docs/images/` show the current interface
  - [ ] The manual is rebuilt: `docs/build.sh`

## On Done

- Delete without asking: `drafts/**`, `*.tmp`
- Merge approved pull requests: yes, squash
- Never touch: branches `release/*`
- Run: `scripts/sync.sh`
```

How `Requirements` items are written (the checkboxes are never ticked in the file):

- **One condition per item**, short enough to be checked and reported on its own. Never chain conditions in
  one sentence with `;`, `and`, `:` or a trailing "The pull request says...": each becomes its own item.
- **A command that decides the item** goes last, after a colon: ``Tests pass: `npm test` ``. It runs from the
  repository root, must change nothing, and the item passes when it exits 0. One command per item.
- **Sub-items** group conditions that share a trigger or a scope ("When the manual changed:", "At a
  release:"). The parent states only that trigger or scope and has no command. One level of nesting at most.
- **A condition that applies only sometimes** starts with it ("For a plugin with a mod: ..."), or becomes a
  group when several items share it.
- Paths and file names go in backticks too.

The `On Done` lines with a defined meaning are in [on-done.md](on-done.md); a file with one section only
leaves the other to the defaults.

## Steps

1. Read the project instructions, the CI configuration and the existing `DoD.md`.
2. Draft the `Requirements` from [default-dod.md](default-dod.md), made specific to the repository: its real
   test, lint and build commands, its integration branch, its pull request flow. Draft `On Done` from the
   folders where drafts accumulate and the merge policy. Do not repeat the goals and hygiene conditions of
   `SKILL.md`: they always apply.
3. Keep it short: criteria someone can check, not aspirations. When revising, split every item that bundles
   several conditions and move each deciding command to the end of its item, keeping the meaning. When several
   checks need more than one command each, offer a project script that an item names as its command.
4. Show the draft, or the diff when the file exists.
5. Write it only after the user confirms. Do not commit it unless asked.

The same flow runs when the user accepts the offer made after a run with `dod_file: none`: the draft starts
from the criteria that run used.
