---
summary: Writes a handoff prompt that lets another agent session or a colleague continue a piece of work, with a patch or a zip for the material they cannot reach.
---

# handoff

`handoff` prepares a prompt that lets another agent session or a colleague continue your work without asking you anything. The prompt covers one topic and points to the files the recipient can reach. What they cannot reach travels as a patch or in a zip.

## Why

When work moves to another session, machine or person, the context is what gets lost: what was decided, which files matter, what was never pushed. A summary written from memory misses the changes that exist only on your machine.

`handoff` checks every fact against the files and git, finds the material the recipient cannot reach and ships it with the prompt, and asks you before anything sensitive leaves the machine. It never commits or otherwise changes your repository, and it pushes only when you say yes.

## Use cases

### Continue in a fresh session on the same machine

**Context:** Your session has grown long and one topic of it deserves a clean start.

**Action:** Ask for a handoff of that topic only, for another session.

**Result:** The prompt is on your clipboard, with absolute paths, ready to paste into the new session.

### Pass unpushed work to a colleague

**Context:** A colleague takes over a fix, and part of it is uncommitted on your machine.

**Action:** Ask for the handoff and name the colleague.

**Result:** A `<topic>-handoff.zip` in the current directory, with `HANDOFF.md` and a `changes.patch` inside.

### Brief a cloud agent that only takes text

**Context:** A remote agent clones the repository and receives nothing but pasted text.

**Action:** Ask for the handoff for that agent.

**Result:** One prompt with repo-relative paths, the remote URL, branch and commit, and your unpushed changes as an inline diff.

## Installation

```bash
npx skills add MrBogomips/skills --skill handoff
```

It is the same skill as in the `skills` plugin, installed under the name `handoff` instead of `skills:handoff`.

## Usage

```text
/skills:handoff [--file] [--zip | --no-zip] [--patch | --no-patch] [free text]
```

The free text narrows the topic and may name the recipient. Without it, the topic is the current task. You can also ask in words: "save it to a file" counts as `--file`, "make a zip" as `--zip`.

```text
/skills:handoff --file only the parser fix
```

This writes the prompt to a `<topic>-handoff.md` file instead of the clipboard, and reports what was produced and what was left out.

## Inputs and outputs

- **Default:** the prompt goes to the clipboard; no file is written.
- **`--file`**, or no working clipboard tool: `<topic>-handoff.md` in the current directory, or where the project's rules place such files.
- **Zip:** `<topic>-handoff.zip` in the current directory, with `HANDOFF.md` inside. The clipboard gets one line that tells the recipient to extract it and follow `HANDOFF.md`.

An existing file is never overwritten, and the output is never committed.

## Requirements

An agent harness with a shell. git, the system clipboard and a zip tool are used when they are available.
