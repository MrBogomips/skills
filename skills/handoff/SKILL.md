---
name: handoff
description: >-
  Prepares a handoff prompt that lets another agent session or a colleague pick up a piece of work. Use when the
  user asks to hand off, hand over, pass on or transfer the current task, or one topic of it, to another session,
  a remote or cloud agent, another machine or a colleague, or asks for a handoff prompt, file or zip
  ("passaggio di consegne").
license: MIT
compatibility: >-
  Any agent harness with a shell. Uses git when the work is in a repository, and the system clipboard and a zip
  tool when they are available.
---

# Handoff

A handoff is a prompt that lets the recipient, another agent session or a colleague, continue the work without
asking anything. It carries only what matters for the chosen topic and points to material the recipient can
reach. Material they cannot reach travels as a patch or in a zip.

## Invocation

```text
handoff [--file] [--zip | --no-zip] [--patch | --no-patch] [free text]
```

- **Free text** narrows the topic and may name the recipient: "only the parser fix, for Marco". Without it, the
  topic is the current task.
- Phrases with the same meaning count as flags: "save it to a file" is `--file`, "make a zip" is `--zip`.
- If flags conflict (`--zip` with `--no-zip`, `--patch` with `--no-patch`), ask which one applies.

## Steps

1. **Topic.** Collect from the conversation what the recipient needs for the topic. Check every fact against the
   files and git before writing it down; where they disagree, the files win.
2. **Recipient.** Classify it from the free text with the table in *Recipients*. If the text does not say and
   step 3 finds material at risk, ask one question offering the three kinds; otherwise the recipient is *unknown*.
3. **Inventory.** List every file the prompt will cite and mark it *reachable* (in a commit that is on a remote
   branch, unchanged since) or *at risk* (uncommitted, untracked, in local-only commits, outside the repository,
   or in a project without git). Commands are in [references/packaging.md](references/packaging.md).
4. **Mode.** Pick it from the table in *Modes*.
5. **Unpushed commits.** If the recipient is not on the same machine and local-only commits hold topic changes,
   offer to push them once the push scan in [references/sensitive-data.md](references/sensitive-data.md) finds
   nothing in their diff. Push only on an explicit yes; pushed commits become reachable. Uncommitted and untracked
   topic files still travel in the patch. Never commit, stash, reset or otherwise change the user's repository.
6. **Confidentiality.** Run the check in [references/sensitive-data.md](references/sensitive-data.md) on
   everything that leaves the machine. Skip it only for a same-machine prompt with no zip.
7. **Write the prompt** following [references/prompt-template.md](references/prompt-template.md).
8. **Deliver** it as *Output* says.
9. **Report** in a few lines: the recipient assumed, what was produced and where, what was left out or
   anonymized, any push. Do not print the prompt; offer to show it.

## Recipients

| Kind | Typical wording | Paths in the prompt |
|---|---|---|
| Same machine | "another session", "here on my Mac" | absolute |
| Elsewhere, receives files | a colleague, another PC, a remote or disconnected system | repo-relative, with remote URL, branch and commit |
| Remote session, text only | a cloud agent that clones the repository, a chat that only takes pasted text | repo-relative, with remote URL, branch and commit |
| Unknown | nothing said, nothing at risk | repository root with `~` for the home directory, then repo-relative paths, with remote URL, branch and commit |

## Modes

| Recipient | Nothing at risk | Something at risk |
|---|---|---|
| Same machine | prompt | prompt |
| Elsewhere, receives files | prompt | zip with `--patch` |
| Remote session, text only | prompt | prompt with the diff inline (`--no-zip --patch`) |
| Unknown | prompt | ask the recipient kind (step 2) |

- `--zip` always makes a zip, and its default becomes `--no-patch`. `--no-zip` never makes one.
- `--patch` ships changes to repository files as a diff against the last pushed commit: `changes.patch` in a
  zip, a `diff` code block in a prompt. With `--no-patch` a zip holds full copies of the current files, and a
  prompt only names the at-risk files, warning that the recipient does not have them.
- Files outside the repository go into a zip as copies. A prompt for anyone but the same machine describes them
  in words and never by local path.
- With no pushed base (nothing ever pushed, no remote, no git) nothing can be patched: a zip holds full copies.
- What goes into a zip, file by file, and the no-base case: [references/packaging.md](references/packaging.md).

## Output

| Case | Result |
|---|---|
| Prompt (default) | copied to the clipboard; no file is written |
| Prompt with `--file` | `<slug>-handoff.md` in the current directory, instead of the clipboard |
| Zip | `<slug>-handoff.zip` in the current directory, with `HANDOFF.md` inside; the clipboard gets one line telling the recipient to extract it and follow `HANDOFF.md` |
| No working clipboard tool | as with `--file`, and the report says so |

- `<slug>` is a few lowercase ASCII words naming the topic, joined by hyphens: `bug22-date-format`.
- Never overwrite. If the name exists, insert `-2`, `-3`… before `-handoff`: `bug22-date-format-2-handoff.md`.
- Never commit the output. If it lands inside a repository and `git check-ignore` does not match it, the report
  says it is untracked.
- Clipboard and zip commands for each system: [references/packaging.md](references/packaging.md).

## Common mistakes

| Mistake | Instead |
|---|---|
| A section listing the session's other topics | the topic only, plus the one line for unrelated changes the recipient will see ([references/prompt-template.md](references/prompt-template.md)) |
| Loose patch files in a folder | one `changes.patch` inside `<slug>-handoff.zip` |
| A prompt in English when the conversation is in another language | the language of the conversation |
| A file and a clipboard copy, or a file in some other folder | exactly one output from the *Output* table |
| "Include or exclude?" for a sensitive file | one question listing each finding with its type and default |
| Leaving a sensitive file out without asking | list it in that question; the user decides how it travels |
| Local absolute paths in a prompt for a colleague | repo-relative paths with branch and commit |
