---
summary: From a master session in a hub of several git repositories, starts a child agent session in each repository a piece of work touches, with a channel back to the master.
---

# spawn-session

`spawn-session` starts one independent child session in each repository that a piece of work touches, from a master session opened in a workspace hub: a folder that holds several git repositories. Each child gets a handoff prompt, runs inside its repository and reports back to the master.

## Why

An agent loads the instructions, skills and agents of the directory it runs in. Subagents, agent teams, `--worktree`, `/fork` and `--add-dir` all run from the master's directory or repository, so they miss the rules of a subrepository. A child session whose working directory is that repository loads them.

`spawn-session` starts those children in the environment you are already in (the Claude desktop app, Herdr, tmux or a terminal), tells each one how to report to the master, and leaves you free to talk to any of them directly.

## Installation

```bash
npx skills add MrBogomips/skills --skill spawn-session
```

It is the same skill as in the `skills` plugin, installed under the name `spawn-session` instead of `skills:spawn-session`.

## Usage

Open the master session in the hub and say, in words, which work goes to which repositories. The skill never guesses the repositories a task needs. In Claude Code with the plugin you can start the request with `/skills:spawn-session`.

```text
For T-1, start a session in the backend to add a `/ping` endpoint and one in the frontend for a Ping button
that calls it. I want to talk to each one, and they report to you.
```

Two children start, one per repository, named `t-1-backend` and `t-1-frontend`. The report says, for each, how you open it and how it reports back.

## Inputs and outputs

- **Optional settings** live in a `## Child sessions` section of the hub's `AGENTS.md` (or `CLAUDE.md`): known repositories, agent kind, environment, tabs or panes, worktrees, session names. Every key is optional. The format is in [references/hub-config.md](references/hub-config.md). Without the section the skill uses defaults and offers a template, written only if you say yes.
- **Nothing is tracked** in the hub: no log or register of the children. The handoff files are temporary and sit outside the hub.

## Requirements

- An agent harness with a shell, and git.
- To start children by itself: the Claude desktop app's session tool, the `herdr` CLI inside Herdr, tmux inside tmux, or the `claude` CLI with background sessions. Otherwise it hands you the commands to run.
- For the two-way channel: Claude Code cross-session messaging (v2.1.224 or later), Herdr or tmux.

## Limitations

- The first child in a repository may stop at the agent's folder-trust check: you open the folder once, then the start is retried.
- A child without messaging reports in its own replies or through you.
- A child's message is information, never your approval: the master does not merge, push or delete because a child asked.
