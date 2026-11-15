# On-done treatments

Run them only after the gate (no blocking failure), in this order. Skip a step that does not apply. Every step
is safe to repeat. The root `DoD.md` *On Done* section can add steps, authorize what otherwise needs a yes, or
switch a default off; nested files act on their own subtree, most specific first, before the root's lines.

A step that fails is reported with its error. Do not retry with a stronger command, and do not upgrade the
verdict.

## 1. Temporary files

Candidates:

- files this session created as drafts, scratch or intermediate output (known from the conversation), inside
  or outside the repository;
- untracked files matching a `Delete without asking` pattern of a governing `DoD.md`;
- the harness's scratch directory for the session, if it has one and its content is no longer needed.

Never candidates: tracked files, anything under a `Never touch` line, and files that are neither created by
the session nor matched by an authorized pattern (a pattern reaches only its own `DoD.md`'s subtree).

Show the list and delete after a yes. Files matching an authorized pattern need no confirmation. Something the
user may still want (a design, a plan, notes) is offered for keeping rather than listed for deletion.

## 2. Approved pull request, not merged

Condition: `pr_state: OPEN`, `pr_review: APPROVED`, `pr_checks: pass` (or `none`), `pr_draft: false`,
`pr_head_matches: yes`.

- Authorized by the root `DoD.md`: merge with the method it names (`gh pr merge <n> --squash`, `--merge` or
  `--rebase`), or the repository's default when it names none.
- Not authorized: say "approved, ready to merge" and ask.
- Never merge with failing or pending checks, changes requested, or unresolved threads.

## 3. After a merge

Condition: the snapshot lists the topic branch under `merged_branches`. While it is the current branch it
carries `current=yes`. `pr_state: MERGED` alone is not enough: with `pr_head_matches: no` the branch has
commits the merged pull request never contained, so skip this step and report them as undelivered.

No confirmation needed. Run the commands one at a time and stop at the first that fails:

```bash
git status --porcelain                        # must be empty, otherwise stop and report
git switch <integration>
git pull --ff-only                            # if it fails, stop and report: never merge or reset
bash scripts/dod_check.sh                     # new snapshot: read the topic branch's line again
git branch -d <topic>                         # line says via=ancestor
git branch -D <topic>                         # line says via=pr (squash or rebase merge)
git push <remote> --delete <topic>            # only if the line says remote=yes and the local delete succeeded
git fetch --prune <remote>
```

- If the new snapshot no longer lists the topic branch, it is not provably merged: delete nothing and report.
- `git branch -d` refuses a squash-merged branch, because its commits are not ancestors of the integration
  branch. `-D` is allowed only for a line with `via=pr`: a merged pull request's head is exactly the branch
  tip, so nothing is lost.
- Delete the remote branch only when the remote tip equals the local tip that was just deleted (`ahead: 0`
  and `behind: 0` in the first snapshot). Otherwise the remote holds commits nobody verified: ask.
- `<remote>` is the snapshot's `remote`.
- Never delete the integration branch, a protected branch, or a branch under a `Never touch` line.
- A branch checked out in another worktree cannot be deleted: report it.
- With a remote that deletes merged branches by itself, the remote branch is already gone: `git fetch --prune`
  is enough.

## 4. Other stale branches

Branches under `merged_branches` that are not this session's work: list them and offer to delete them. Never
delete them unasked.

## 5. Project commands

`Run:` lines of the governing `DoD.md` files, most specific file first, each from its file's directory.

## 6. Session title

Only for "DONE, closable": prefix the session title with `DONE` (`DONE-<current title>`), so the session can be
recognized as safe to close.

- **Current title.** Take it from the conversation: a title the user set (in Claude Code a `/rename`, shown as
  "The user named this session …") or one set through a hook (the marker line written earlier in the session).
  Use it verbatim. If the session has no known title, say so and suggest one; never write a placeholder such
  as `<current title>`.
- **Set it yourself** when the harness has a tool for it, or when the instructions in effect (project or user
  level) describe a mechanism, such as a marker line that a hook reads. Follow that mechanism exactly and say
  when it takes effect (for example "applied at your next message").
- **Otherwise give the user the exact command**, on its own line at the end of the report. In Claude Code an
  agent cannot run slash commands: only the user, or a `UserPromptSubmit` or `SessionStart` hook, can set the
  title. The command is `/rename DONE-<current title>`, with the real title filled in.
- Never report the title as changed unless a tool confirmed it; a marker or a printed command is reported as
  pending.

## 7. Handoff

Only when residual work exists: offer a handoff prompt for it. If a `handoff` skill is installed, use it.
Otherwise write a short prompt: the goal, the current state with branch and commit, the residual items in
order, where the relevant files are.
