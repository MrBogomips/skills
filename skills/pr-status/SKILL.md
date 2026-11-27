---
name: pr-status
description: >-
  Prints the live status of the pull requests in play, one line each with a status emoji, read from GitHub
  with gh at that moment. Runs only when the user invokes /pr-status or $pr-status, optionally with pull
  request references; never on a request made in other words.
license: MIT
compatibility: Needs the GitHub CLI (gh), authenticated, and Python 3.8+. GitHub only. Read-only.
disable-model-invocation: true
---

# PR status

A fixed status list for work that spans several pull requests. The state always comes from GitHub at the moment
of the invocation, never from what the conversation remembers. Read-only: never comment, label, approve, merge
or close.

## 1. Which pull requests

- Arguments win: `owner/repo#N`, a pull request URL, or `#N` for the current repository.
- With no arguments, take the pull requests in play in the conversation: those under review or being worked
  on, and those opened or touched in this session. Leave out ones mentioned only in passing.
- With neither, ask which pull requests; do not guess.

## 2. Read them

Run the script once with every reference, from the user's project directory and not from this skill's
directory: `python3 <this skill's directory>/scripts/pr_status.py <ref> ...`. A bare `#N` is read in the
repository of the current directory; for pull requests taken from the conversation always pass `owner/repo#N`.

It prints a JSON array, one entry per reference, with a `state`, its `emoji` and the facts behind it. Exit
status 3 means gh is not installed: tell the user to install it and run `gh auth login`, and stop. Status 1
means some entries are errors: print them with the others.

## 3. Print the list

Output only this block, with every word in the user's language, "merged" and the title included:

```
---
Pull requests
- ✅ design: #78 merged · https://github.com/acme/design/pull/78
- ❌ app: #421 open, sbom check failed (not required) · https://github.com/acme/app/pull/421
- ⛔ app: #430 draft, conflict with the base, build check failed · https://github.com/acme/app/pull/430
- 🆕 prototype: #29 open, not reviewed yet · https://github.com/acme/prototype/pull/29
```

- One line per pull request: the entry's `emoji`, the repository, `#number`, the status in words, ` · `, the
  full URL as plain text. Never put the URL inside a Markdown link, and never change the emoji.
- The repository is its name without the owner (`cli` for `cli/cli`), with the owner only when two
  repositories in the list share a name. Group the lines by repository in order of first appearance, and
  sort each group by number.
- When the project's instructions define a title, short names or an order for its repositories, those win.
- Write the status words from the facts, the state first, the rest after it, separated by commas:

| `state` | Words |
|---|---|
| `merged` | merged |
| `closed` | closed without merging |
| `blocked` | open (or draft), then each cause: conflict with the base (`conflict`), changes requested (`changes_requested`) |
| `ci_failed` | open (or draft), then the `failed_checks` by name; add "not required" when `failed_checks_not_required` |
| `draft` | draft |
| `unreviewed` | open, not reviewed yet; add "automated review only" when `bot_reviews` is not 0 |
| `in_progress` | open, then what is under way: checks running (`pending_checks`), in review, approved and waiting to merge (`approved`) |
| `error` | a line of its own shape, after all the others: `- ⚠️ <ref>: <error>`, the error text as it is, no URL |

- On an open pull request add the other facts that are true: failed checks behind a block, "merge state not
  computed yet" (`merge_state_unknown`), and "stacked on `<base>`" when `base_is_default` is false and `base`
  is not the integration branch the project's instructions name for that repository.
