---
summary: Checks on evidence whether a work session meets its Definition of Done, then tidies up temporary files, merged branches, the local integration branch and the session title.
---

# done

`done` verifies whether a work session is finished by checking every criterion against a command or a file rather than memory. When the verdict allows, it cleans up temporary files, merged branches, the local integration branch, and the session title.

## Why

Agents are quick to call work done even when tests passed earlier, a pull request is still open, or drafts are lying around. `done` returns a verdict backed by evidence (`NOT DONE` with what is missing, `DONE`, or `DONE, closable`) evaluated against criteria you control: the repository's `DoD.md`, project instructions, or a generic default.

Cleanup removes only what is provably disposable. Merging requires your approval unless your root `DoD.md` authorizes it; deleting anything not proven merged always requires approval.

## Installation

```bash
npx skills add MrBogomips/skills --skill done
```

This installs the same skill from the `skills` plugin, under the name `done` instead of `skills:done`.

## Usage

```text
/skills:done [init] [--check] [free text]
```

| Argument | Behavior |
| --- | --- |
| None | Evaluate the session, then run the cleanup the verdict allows. |
| `--check` | Report the verdict and planned cleanup without making changes. |
| `init` | Create or revise the `DoD.md` at the repository root without evaluating. |
| Free text | Amend this run only: "ignore the docs PR" or "also delete the spike branch". |

You can also invoke it in plain language, such as "are we done?" or "finalize and cleanup".

Example:

```text
/skills:done --check
```

The response follows a fixed format: the verdict, each condition with its status mark (passed, failed, not verifiable, or not applicable) and evidence, each cleanup action with its outcome (`OK`, `FAILED`, `SKIPPED`, `DECLINED`, `PENDING`), and at most one question covering any remaining confirmations.

## Inputs and outputs

`DoD.md` is optional, lives at the repository root and contains two sections: `## Requirements` holds your checklist (one condition per item, with sub-items grouped under a shared trigger such as "At a release:"), and `## On Done` lists the cleanup actions the file authorizes or disables. See [references/init.md](references/init.md) for the format.

The output is a short report in the conversation. `done` writes no files unless you run `init`, which writes `DoD.md` only after you confirm.

## Requirements

A model of Sonnet class or above; a less capable model does not do this job well enough. An agent harness with a shell is required. `done` uses git when the work is in a repository, and the GitHub CLI (`gh`) when installed. Without them, the related checks are reported as not verifiable.

## Limitations

- `done` never commits, stashes, resets, force-pushes, or rewrites history. Uncommitted work results in a `NOT DONE` verdict.
- It evaluates only the work of the current session. Other stale branches are reported separately and do not affect the verdict.
- A criterion that cannot be verified (no `gh`, another forge, or no network) does not fail the verdict but rules out `DONE, closable`.