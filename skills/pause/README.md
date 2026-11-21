---
summary: Pauses agentic work so that nothing runs or spends tokens while you are away, writes a checkpoint, and resumes the work later in the same session.
---

# pause

`pause` suspends work in progress so nothing is lost and nothing spends tokens while you are away, then resumes it in the same session. It stops background work, writes a short checkpoint, and gives you a `/compact` command to run before you leave if the context is large.

## Why

Leaving a session mid-task has two costs. Loops, scheduled wakeups, and background agents keep spending tokens while nobody is watching. After a long pause, the prompt cache also expires, so the first turn back re-reads the whole context at full price.

`pause` stops anything that would run unattended and records how to restart it. It also has you compact while the cache is still warm, so resuming is cheap. Your working tree stays untouched.

## Installation

```bash
npx skills add MrBogomips/skills --skill pause
```

This installs the same skill included in the `skills` plugin, under the name `pause` instead of `skills:pause`.

## Usage

```text
/skills:pause
```

You can also trigger it in plain language, such as "pause" or "I must go". The agent lists what it stopped, the checkpoint path, and a `/compact` command to run if the context is large. After that, it does no further work.

When you return, say "resume". The agent reads the checkpoint, reports what changed in the repository while you were away, restarts what it stopped, and continues from the next step.

## Inputs and outputs

The checkpoint is written to `pause-checkpoint.md` in the session scratchpad or the system temporary directory, never inside the repository.

## Requirements

`pause` works with any agent harness and uses git when the work is in a repository. The compact step requires a harness with a `/compact` command (Claude Code, Codex) and is skipped elsewhere.

## Limitations

- Work can resume only in the same session. To move it to another session or person, use `handoff`.
- An agent cannot run `/compact` itself; you run the command it gives you.
- When you resume, loops, crons, and other scheduled tasks are re-created only after you confirm.