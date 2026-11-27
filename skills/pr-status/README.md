---
summary: Prints the live status of several pull requests at once, one line each with a status emoji, read from GitHub when you ask.
---

# pr-status

`pr-status` prints one line for each pull request you are working on: a status emoji, the repository, the number, the status in words and the URL. It reads the state from GitHub at that moment and never starts on its own.

## Why

Work that spans several pull requests, often in several repositories, needs a status list you can read at a glance. An agent asked in a few words answers with a different table each time and reports what it remembers or what one field suggests: it shows raw merge states and leaves you to work out which pull request needs you. The rules are easy to get wrong: a bot's review is not a review, and a re-run check leaves its old failure behind. `pr-status` always reads GitHub again, applies the same rules through a tested script and prints the same list.

## Installation

```bash
npx skills add MrBogomips/skills --skill pr-status
```

This installs the same skill included in the `skills` plugin, under the name `pr-status` instead of `skills:pr-status`.

## Usage

Invoke `/pr-status` (`/skills:pr-status` with the plugin in Claude Code), with or without references:

```
/pr-status acme/design#78 acme/app#421 https://github.com/acme/app/pull/430
```

```
---
Pull requests
- ✅ design: #78 merged · https://github.com/acme/design/pull/78
- ❌ app: #421 open, sbom check failed (not required) · https://github.com/acme/app/pull/421
- ⛔ app: #430 open, changes requested · https://github.com/acme/app/pull/430
```

- With no references it lists the pull requests in play in the conversation, and asks when there are none.
- Each line carries one emoji, the first that applies: ✅ merged, 🗑️ closed without merging, ⛔ conflict or changes requested, ❌ a failed check, 📝 draft, 🆕 not reviewed by a person yet, 🔄 in progress.
- A title, short repository names and an order defined in your project's instructions are used as they are.
- A request in other words ("show me the PR status") does not start it.

## Requirements

- The GitHub CLI (`gh`), authenticated with access to the repositories.
- Python 3.8 or later.

## Limitations

- GitHub only (github.com, or the host `gh` is signed in to).
- Reads the first 100 reviews and checks of a pull request.
- Read-only: it never comments, labels, approves, merges or closes.
- GitHub does not say which checks are required: a failed check is reported as "not required" only when the pull request is still mergeable.
- In harnesses other than Claude Code nothing but the description stops the agent from starting it on its own.
