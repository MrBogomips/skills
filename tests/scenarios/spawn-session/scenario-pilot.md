# Scenario: pilot per environment

Run once per environment, with a fresh fixture. In the master, ask:

> For T-1, start a session in the backend to add a `/ping` endpoint and one in the frontend for a Ping button
> that calls it. I want to talk to each one, and they report to you.

## Start

- [ ] Two children start, one per repository, each with the repository as its working directory
- [ ] Names follow `t-1-backend` and `t-1-frontend`
- [ ] The hub's Confidentiality rule is not in the handoffs, and the report says it was left out and offers it
- [ ] Without a `## Child sessions` section, the master offers the template and writes nothing without a yes
- [ ] No file is written in the hub or the repositories apart from what the children do; handoff files sit in a
      temporary directory

## Per child

- [ ] (a) Asked "which skills and agents do you have from this repository?", the child names `hello-<repo>` and
      `<repo>-reviewer`, and not the other repository's
- [ ] (b) The child reports to the master with the `[T-1 <repo>]` prefix, and the master receives it
- [ ] (c) A `SendMessage` from the master (or `herdr agent prompt "[master] …"` for a non-Claude child) reaches
      the child
- [ ] (d) The user types to the child directly, in its tab, sidebar row or `claude attach`, and the child
      answers; an instruction from the user that contradicts the master wins

## First run in a repository

- [ ] Desktop app, repository never opened there: the master reports that the app refused the worktree, asks the
      user to open the folder once, and does not retry on its own
- [ ] `claude --bg`, untrusted repository: the master reports `Workspace not trusted` and offers the fix or
      another environment
- [ ] Herdr, tmux: the master tells the user which window shows the trust prompt and never answers it itself

## Duplicates

- [ ] Asking again for "T-1 in the backend" sends the request to `t-1-backend` instead of starting a new child

## Environment-specific

- [ ] Desktop app: both children appear as linked sessions; the master is woken when a child ends a turn
- [ ] Herdr: one tab per child, opened without moving focus; the handoff is passed as a file, not inline
- [ ] tmux: one window per child, opened with `-d`; the handoff is passed as a file; `tmux list-panes -a` finds the
      child for the duplicates check
- [ ] Terminal: `claude agents` lists both children; `claude attach t-1-backend` opens it
- [ ] Manual: the master prints, per child, the commands and the handoff file path, and starts nothing
- [ ] Desktop master with a `--bg` child: the child appears in the master's `ListAgents` and messages flow both
      ways (record the Claude Code version)
