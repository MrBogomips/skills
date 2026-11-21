# Creating or revising a DoD.md (`done init [dir]`)

The format is in [dod-file.md](dod-file.md).

1. Read the project instructions, the CI configuration and the existing `DoD.md` files from `dir` up to the
   repository root (default `dir`: the root).
2. Draft the file from [default-dod.md](default-dod.md), made specific to the repository: its real test, lint
   and build commands, its integration branch, its pull request flow, the folders where drafts accumulate. For
   a nested directory, write only what differs from the levels above.
3. Keep it short: criteria someone can check, not aspirations. When several checks need more than one command
   each, offer a project script that the file names as a requirement's command (it must change nothing).
4. Show the draft, or the diff when the file exists, and ask whether it is committed (default: yes).
5. Write it only after the user confirms. Do not commit it unless asked.

The same flow runs when the user accepts the offer made after a run without any `DoD.md`: the draft starts
from the criteria that run used.
