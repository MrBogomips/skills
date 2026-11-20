---
summary: Checks on evidence whether a work session meets its Definition of Done, then tidies up temporary files, merged branches, the local integration branch and the session title.
---

# done

`done` decides whether the work of a session is finished and proves it: every criterion is checked with a command or a file, never from memory. When the verdict allows it, the skill tidies the workspace: temporary files, merged branches, the local integration branch, the session title.

## Why

An agent says "done" easily: the tests passed earlier, the pull request is still open, drafts are lying around. `done` gives you a verdict with its evidence (`NOT DONE` with what is missing, `DONE`, or `DONE, closable`) against criteria you own: `DoD.md` files in the repository, the project instructions, or a generic default.

Cleanup removes only what is provably disposable. Merging needs your yes unless your root `DoD.md` authorizes it; deleting anything not proven merged always does.

## Installation

```bash
npx skills add MrBogomips/skills --skill done
```

It is the same skill as in the `skills` plugin, installed under the name `done` instead of `skills:done`.

## Usage

```text
/skills:done [init [dir]] [--check] [free text]
```

- No argument: evaluate, then clean up as far as the verdict allows.
- `--check`: report the verdict and the cleanup that would run; change nothing.
- `init [dir]`: create or revise the `DoD.md` of a directory (default: the repository root), without evaluating.
- Free text amends this run only: "ignore the docs PR", "also delete the spike branch".

You can also ask in words: "are we done?", "finalize and cleanup".

```text
/skills:done --check
```

The reply starts with the verdict. With `NOT DONE` it lists only the failing criteria, each with its evidence and the next action.

## Inputs and outputs

`DoD.md` is optional. It has two sections: `## Requirements`, your checklist, and `## On Done`, the cleanup the file authorizes or switches off. The format is in [references/dod-file.md](references/dod-file.md).

The result is a short report in the conversation. `done` writes no file, except `DoD.md` with `init`, after you confirm.

## Requirements

An agent harness with a shell. git is used when the work is in a repository, and the GitHub CLI (`gh`) when it is installed. Without them the related checks are reported as not verifiable.

## Limitations

- It never commits, stashes, resets, force-pushes or rewrites history. Uncommitted work makes the verdict `NOT DONE`.
- It judges only the work of the current session. Other stale branches are reported apart and do not change the verdict.
- A criterion that cannot be checked (no `gh`, another forge, no network) does not fail the verdict, but rules out `DONE, closable`.
