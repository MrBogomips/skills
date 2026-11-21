# On-done treatments

Run them only after the gate, in this order; skip what does not apply. Each one is one line of the report's
*Actions*. A treatment that fails is reported with its error: never retry with a stronger command. The root
`DoD.md` *On Done* section can add treatments, authorize what otherwise needs a yes, or switch one off; nested
files act on their own subtree, before the root's lines.

Collect every yes the treatments need into **one** question at the end of the report; run the confirmed ones
after the answer and report them then.

## 1. Temporary files

Candidates: files the session created as drafts, scratch or intermediate output (inside or outside the
repository), and untracked files matching a `Delete without asking` pattern of a governing `DoD.md`. Never:
tracked files, anything under `Never touch`, files neither created by the session nor matched by a pattern.

Pattern matches and the session's own scratch go without asking. Other files need a yes. Something the user may
still want (a plan, a design, notes) is offered for keeping, not deleting.

## 2. Merge an approved pull request

Condition: `pr_state: OPEN`, `pr_review: APPROVED`, `pr_checks: pass` or `none`, `pr_draft: false`,
`pr_head_matches: yes`, `pr_unresolved_threads: 0`. Authorized by the root `DoD.md`: `gh pr merge <n>` with
the method it names. Otherwise it needs a yes.

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

`Run:` lines of the governing `DoD.md` files, most specific first, each from its file's directory.

## 6. Session title

Only for **DONE, closable**: prefix the current title with `DONE-`.

- The current title is the one the user set (`/rename`, "The user named this session …") or the one set by a
  marker earlier in the session, verbatim. Unknown: say so; never write a placeholder.
- Set it with the harness's tool, or the mechanism the instructions in effect describe (for example a marker
  line a hook reads): then it is `PENDING` until it applies, and the report says when.
- Otherwise print `/rename DONE-<real title>` as the last line: `PENDING`.

## 7. Handoff

Only when residual work exists: offer one in the final question (with the `handoff` skill when installed).
