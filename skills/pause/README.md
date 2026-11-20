---
summary: Pauses agentic work so that nothing runs or spends tokens while you are away, writes a checkpoint, and resumes the work later in the same session.
---

# pause

`pause` suspends work in progress so that nothing is lost and nothing spends tokens while you are away, then picks it up again in the same session. It stops background work, writes a short checkpoint and, when the context is large, gives you a `/compact` line to run before you leave.

## Why

Leaving a session in the middle of a task has two costs. Loops, scheduled wakeups and background agents keep spending tokens while nobody is watching. And after a long pause the prompt cache has expired, so the first turn re-reads the whole context at full price.

`pause` stops what would run unattended and notes how to restart it, and has you compact while the cache is still warm, so the resume is cheap. Your working tree stays exactly as it is.

## Installation

```bash
npx skills add MrBogomips/skills --skill pause
```

It is the same skill as in the `skills` plugin, installed under the name `pause` instead of `skills:pause`.

## Usage

```text
/skills:pause
```

Or say it in words: "pause", "I must go". The report lists what was stopped, the path of the checkpoint and, if the context is large, the `/compact` line to run. The agent then does no further work.

When you are back, say "resume". The agent reads the checkpoint, reports what changed in the repository meanwhile, restarts what it stopped and continues from the next step.

## Inputs and outputs

The checkpoint is `pause-checkpoint.md`, in the session scratchpad or in the system temporary directory, never inside the repository.

## Requirements

Any agent harness. git is used when the work is in a repository. The compact step needs a harness with a `/compact` command (Claude Code, Codex) and is skipped elsewhere.

## Limitations

- It resumes in the same session. To move the work to another session or person, use `handoff`.
- An agent cannot run `/compact` itself: you run the line it gives you.
- Loops, crons and other scheduled tasks are re-created at resume only after you confirm.
