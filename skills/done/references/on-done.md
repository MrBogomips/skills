# On-done treatments

Run them only after the gate, in this order; skip what does not apply. Each one is one line of the report's
*Actions*. A treatment that fails is reported with its error: never retry with a stronger command.

The `On Done` section of the `DoD.md` changes them. Lines with a defined meaning; other sentences are
instructions, within the skill's safety rules:

| Line | Effect |
|---|---|
| `Delete without asking: <patterns>` | matching untracked files are deleted without a yes |
| `Merge approved pull requests: yes[, <method>]` | an approved, ready pull request is merged without a yes |
| `Never touch: <things>` | no treatment touches the named branches, files or directories |
| `Run: <command>` | runs after the default treatments, from the repository root |
| `Do not <default treatment>` | switches it off, e.g. "Do not delete remote branches" |

Collect every yes the treatments need into **one** question at the end of the report; run the confirmed ones
after the answer and report them then.

## 1. Temporary files

Candidates: files the session created as drafts, scratch or intermediate output (inside or outside the
repository), and untracked files matching a `Delete without asking` pattern. Never:
tracked files, anything under `Never touch`, files neither created by the session nor matched by a pattern.

Pattern matches and the session's own scratch go without asking. Other files need a yes. Something the user may
still want (a plan, a design, notes) is offered for keeping, not deleting.

## 2. Merge an approved pull request

Condition: `pr_ready: yes` and `pr_review: APPROVED`. Authorized by the `DoD.md`: `gh pr merge <n>` with the
method it names. Otherwise it needs a yes.

## 3. Close the merged branch

Condition: the topic branch is listed under `merged_branches`. One call, no confirmation:

```bash
bash <skill-dir>/scripts/dod_check.sh --finish <topic>
```

It switches to the integration branch, pulls with `--ff-only`, deletes the branch locally (`-d`, or `-D` only
when a merged pull request has its exact tip) and on the remote (only when the remote tip is the one just
deleted), prunes, then prints a fresh snapshot. Report its `finish_step` lines. A `FAILED` or a remote branch
`SKIPPED` because its tip moved needs the user: never resolve it with a stronger command.

Never for a branch under `Never touch`.

## 4. Other merged branches

Branches under `merged_branches` that are not this session's: list them in the final question.

## 5. Project commands

The `Run:` lines and the other instructions of `On Done`, in file order, from the repository root.

## 6. Session title

Only for **DONE, closable**: prefix the current title with `DONE-`.

- The current title is the one the user set (`/rename`, "The user named this session …") or the one set by a
  marker earlier in the session, verbatim. Unknown: say so; never write a placeholder.
- Set it with the harness's tool, or the mechanism the instructions in effect describe (for example a marker
  line a hook reads): then it is `PENDING` until it applies, and the report says when.
- Otherwise print `/rename DONE-<real title>` as the last line: `PENDING`.

## 7. Handoff

Only when residual work exists: offer one in the final question (with the `handoff` skill when installed).
