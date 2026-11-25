---
name: pause
description: >-
  Pauses agentic work safely and cheaply so it can be resumed hours later in the same session, then resumes it:
  stops unattended background work, writes a checkpoint, suggests compacting. Use when the user has to stop for a
  while with work in progress ("pause", "suspend", "I must go/leave/commute") or comes back to it ("resume",
  "continue from the pause"). Not for moving work to another session or person (that is a handoff) or closing a
  session.
license: MIT
compatibility: >-
  Any agent harness. Uses git when the work is in a repository; the compact step needs a harness with a
  /compact command (Claude Code, Codex) and is skipped elsewhere.
---

# Pause

Suspend the work so that nothing is lost and nothing costs tokens while the user is away, then pick it up again
in the same session. Two modes: **pause** (default) and **resume** ("resume", "continue from the
pause").

Never commit, stash, reset or otherwise change the user's repository: the working tree stays as it is.

## Pause

1. **Stop starting new work.** Finish the current atomic step (an edit, a test run) so nothing is left
   half-written. Do not begin the next one.
2. **Quiesce background work.** List everything still running or scheduled from this session and handle each:
   - *Running subagents, workflows, background commands*: wait for those about to finish; stop the others and
     note how to restart them (command, prompt, run id). In Claude Code a stopped workflow can be resumed from
     its run id, and agents that completed are not re-run.
   - *Anything that wakes up on its own*: loops, scheduled wakeups, crons, monitors, polling. Stop each one and
     note how to re-create it, since it would spend tokens while nobody is watching. Ask before stopping one the
     user set up outside this task.
3. **Write the checkpoint** `pause-checkpoint.md` in the session scratchpad, or in the system temporary
   directory when the harness has no scratchpad, never inside the repository. Keep it short:
   - paused at (date and time), goal of the work;
   - done, in progress, next steps in order;
   - stopped tasks and how to restart each;
   - open questions and pending decisions;
   - git state when in a repository: branch, `git rev-parse --short HEAD`, `git status --short`.

   If the harness keeps a todo list, bring it in line with the checkpoint.
4. **Make the resume cheap.** The prompt cache expires after minutes (an hour at most), so the first turn after
   a long pause re-reads the whole context at full price. Compacting now, while the cache is warm, costs little
   and shrinks what the resume re-reads. If the context is large and the harness has `/compact`, give the user
   the line to run, since an agent cannot run it itself:

   ```text
   /compact Work paused: the state is in <absolute path of pause-checkpoint.md>. Keep the goal, the decisions and the next steps.
   ```

   If the context is still small, say that compacting is not needed.
5. **Report** in a few lines: what was stopped, the checkpoint path, the `/compact` line if any, and that saying
   "resume" (in any language) picks the work up again. Then stop: do no further work until the user returns.

## Resume

1. **Read the checkpoint**, from the path in the conversation or in the compact summary. If it cannot be found,
   ask for it; do not rebuild the state from memory.
2. **Check what changed.** Compare branch, HEAD and `git status --short` with the checkpoint and report any
   difference: the user may have edited, committed or switched branches meanwhile. Read the output of tasks
   that finished before the stop.
3. **Restart what was stopped**: resume workflows, rerun stopped commands. Re-create loops, crons and other
   scheduled tasks only after the user confirms, since they spend tokens on their own.
4. **Continue** from the first next step. Leave the checkpoint where it is: it is a temporary file, removed when
   the session is cleaned up.
