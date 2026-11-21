---
summary: Writes a handoff prompt that lets another agent session or a colleague continue a piece of work, with a patch or a zip for the material they cannot reach.
---

# handoff

`handoff` prepares a prompt that lets another agent session or a colleague continue your work without follow-up questions. It focuses on one topic, points to the files the recipient can reach, and delivers anything they cannot reach as a patch or in a zip.

## Why

When work moves to another session, machine, or person, context gets lost: what was decided, which files matter, and what was never pushed. A summary written from memory misses changes that exist only on your machine.

`handoff` verifies every fact against your files and git, then includes any material the recipient cannot reach with the prompt. Before anything sensitive leaves your machine, it asks your permission. It never commits or modifies your repository, and it pushes only when you confirm.

## Use cases

### Continue in a fresh session on the same machine

**Context:** Your session has grown long, and one topic needs a clean start.

**Action:** Ask for a handoff of just that topic for another session.

**Result:** The prompt is copied to your clipboard with absolute paths, ready to paste into the new session.

### Pass unpushed work to a colleague

**Context:** A colleague is taking over a fix, and part of it is uncommitted on your machine.

**Action:** Ask for a handoff and name the colleague.

**Result:** `<topic>-handoff.zip` in the current directory, containing `HANDOFF.md` and `changes.patch`.

### Brief a cloud agent that only takes text

**Context:** A remote agent clones the repository and receives only pasted text.

**Action:** Ask for a handoff for that agent.

**Result:** A single prompt containing repository-relative paths, the remote URL, branch, and commit, plus your unpushed changes as an inline diff.

## Installation

```bash
npx skills add MrBogomips/skills --skill handoff
```

This installs the same skill included in the `skills` plugin, under the name `handoff` instead of `skills:handoff`.

## Usage

```text
/skills:handoff [--file] [--zip | --no-zip] [--patch | --no-patch] [free text]
```

The optional free text narrows the topic and can name the recipient; if you omit it, the topic defaults to the current task. You can also state options in plain language: "save it to a file" acts like `--file`, and "make a zip" acts like `--zip`.

For example:

```text
/skills:handoff --file only the parser fix
```

This command writes the prompt to `<topic>-handoff.md` instead of copying it to the clipboard, and reports what was produced and what was left out.

## Inputs and outputs

- **Default:** Copies the prompt to the clipboard without writing any files.
- **`--file` (or no working clipboard tool):** Writes `<topic>-handoff.md` in the current directory, or in the location specified by your project's rules.
- **Zip:** Writes `<topic>-handoff.zip` in the current directory with `HANDOFF.md` inside, and copies a one-line instruction to the clipboard telling the recipient to extract the archive and follow `HANDOFF.md`.

`handoff` never overwrites existing files and never commits its output.

## Requirements

Requires an agent harness with a shell. When available, `handoff` also uses git, the system clipboard, and a zip tool.