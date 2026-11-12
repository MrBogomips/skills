# Generic Definition of Done

Used when no `DoD.md` governs the work, and as the topmost level when the repository root has none. Done
criteria in the project instructions are merged in and win on conflict.

## Reading the snapshot

`scripts/dod_check.sh` prints `key: value` lines; list items are indented below their key.

| Key | Meaning |
|---|---|
| `git` | `no` outside a repository: only `root` and `dod_files` follow |
| `branch`, `head` | current branch or `(detached)`; `head: none` in a repository without commits |
| `remote` | the current branch's upstream remote, else `origin`, else the first remote; `none` without remotes |
| `fetch` | `ok`, `skipped` (no remote, or `--no-fetch`) or `failed`: after `failed`, remote facts may be stale |
| `integration_branch` | from `--base`, else the remote's default branch, else the first of `dev develop main master` |
| `upstream`, `ahead`, `behind` | tracking branch or `none`; commits not pushed, commits not pulled |
| `integration_behind` | commits the local integration branch lacks, or `unknown` |
| `modified`, `untracked` | counts, then the paths (ignored files are not listed; a path ending in `/` is an untracked nested repository) |
| `stashes`, `extra_worktrees` | counts; the script cannot tell which ones this session created |
| `forge`, `gh` | `github` or `unknown`; `ok`, `missing`, `unauthenticated` or `error` |
| `pr_number` … `pr_checks` | the latest pull request of the current branch: number or `none`, state, draft, review decision, checks (`pass`, `fail`, `pending`, `none`) |
| `pr_head_matches` | `yes` when that pull request's head is the current `HEAD`; `no` means it describes an earlier state of the branch |
| `merged_branches` | local branches that are safe to delete: `via=ancestor` (contained in the integration branch) or `via=pr` (a merged pull request has exactly this tip); `remote=yes` when the remote branch still exists; `current=yes` marks the current branch |
| `changed_paths` | the session's work: changes since the merge base with the integration branch, plus modified and untracked files; a rename shows both paths |
| `dod_files` | governing `DoD.md` files, most specific first, each followed by the changed paths it is nearest to; the root file is always listed when it exists |
| `no_dod_paths` | changed paths with no `DoD.md` above them, when other paths have one |
| `dod_name_conflict` | directories holding two spellings of the file name: report it and ask which one counts |

Long lists end with `... (+N more)`; raise the limit with `--max-list <n>`.

## Criteria

### Goals (always apply, whatever `DoD.md` says)

| Criterion | Evidence |
|---|---|
| Every goal asked for in the session is met, or dropped or deferred by the user | the file, commit or command output that shows it; the user's own words for a dropped goal |
| No question is waiting for the user | the conversation |
| Assumptions the agent made on its own are stated | list them in the report |
| No background task, subagent or long-running command is still active | the harness's task list, or `jobs` |

### Quality

| Criterion | Evidence |
|---|---|
| The project's verification passes on the final state | the repository's own test, lint and build commands, run on the current `HEAD` |
| Critical and high review findings are resolved | the review output, or the pull request's review threads |

### Delivery

| Criterion | Evidence |
|---|---|
| Working tree clean | `modified: 0` and `untracked: 0`, apart from temporary files (fixable) |
| Nothing unpushed | `upstream` set and `ahead: 0` |
| Pull request open or merged, when one is required | `pr_state` `OPEN` or `MERGED`, `pr_draft: false`, `pr_head_matches: yes` |
| CI green | `pr_checks: pass` (or `none` when the repository has no checks) |
| No changes requested, no unresolved review thread | `pr_review` is not `CHANGES_REQUESTED`; threads: query below |
| Version, changelog and docs updated where the repository requires it | the project instructions say what is required; check the diff |

Unresolved review threads (GitHub), with the owner, repository and number filled in:

```bash
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100){nodes{isResolved}}}}}' \
  -f o=<owner> -f r=<repo> -F n=<number> --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)] | length'
```

For a session that produced more than one branch, check each other branch's pull request with
`gh pr view <branch> --json number,state,isDraft,reviewDecision,statusCheckRollup`.

### Hygiene

| Criterion | Evidence | Fixable |
|---|---|---|
| No draft or temporary file left | `untracked`, plus what the session wrote outside the repository | yes |
| No debug leftovers in the session's diff | read `git diff <merge base>...HEAD` for debug prints, commented-out code, stray `TODO` | no |
| No stash or worktree the session created is left | `stashes`, `extra_worktrees`, and the conversation | no: ask |
| Merged topic branch deleted locally and remotely | `merged_branches` does not list it (a line with `current=yes` on a branch that has no work yet is not a failure) | yes |
| Local integration branch aligned | `integration_behind: 0` | yes |

## When a pull request is required

Only when the session's work sits on a topic branch of a repository that has a remote.

| Situation | Delivery | Can be closable |
|---|---|---|
| Topic branch, remote | pull request required; closable once it is `MERGED` with `pr_head_matches: yes` | yes, after the merge |
| Work committed and pushed on the integration branch | no pull request required | yes |
| No remote | "working tree clean, everything committed"; say that nothing was pushed | yes |
| `forge: unknown`, or `gh` not `ok` | pull request state is *not verifiable* | no |

## Outside git

Only the goal criteria and "no draft or temporary file left" apply. Temporary files are those the session
created, known from the conversation.
