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

## Permission mode

- [ ] Master not in bypass mode: the children start in its mode and nothing is asked about it
- [ ] Master in bypass mode: at every start it asks to confirm the children's mode, its own first and recommended,
      in the same ask as the layout when that is asked too; a second spawn in the same conversation asks again
- [ ] Children started in the master's mode exchange messages with it in both directions with no approval prompt
      (record the master's mode and the Claude Code version)
- [ ] The child's command line carries `--permission-mode <mode>` (Herdr, tmux, `claude --bg`, manual)
- [ ] Master in bypass mode, user picks a mode without bypass: the report warns that messages wait for approval

## Launch command

Start the master through a wrapper that sets `CLAUDE_CONFIG_DIR` (and `HOME`) to a second profile and adds a
configuration flag, for example
`env CLAUDE_CONFIG_DIR=<profile>/.claude claude --setting-sources user,project --dangerously-skip-permissions`.

- [ ] Herdr: each child pane gets `--env CLAUDE_CONFIG_DIR=…` (and `HOME` when it differs); tmux and manual: the
      command starts with `env CLAUDE_CONFIG_DIR=…`; `claude --bg`: no variables on the command line
- [ ] The child's command carries `--setting-sources user,project` and not the master's `-n`, `--resume`, prompt
      or `--dangerously-skip-permissions`
- [ ] In the child, `printenv CLAUDE_CONFIG_DIR` matches the master and `/status` shows the master's account
- [ ] The master and the child exchange messages in both directions
- [ ] No token or other variable from the master's environment appears on a command line or in a pane
- [ ] Desktop app: the report says the child may use the app's account and may not reach the master

## Layout

- [ ] Desktop app, Herdr and tmux: without a *Layout* key, the master asks once, in the same ask as the permission
      mode when that is asked, for the layout (tabs or stacked panes) and whether to save it as the hub's default; `claude --bg` and
      manual skip the layout question
- [ ] On "save", `- Layout: <value>` appears in the hub's `## Child sessions` section (created if missing); on "don't
      save", the hub is unchanged and a second spawn in the same conversation does not ask again
- [ ] `panes` in Herdr and tmux: the first child to the right of the master, the next ones stacked below it, the
      master keeps focus, each pane labelled with the child's name; in tmux the stack has equal heights
- [ ] `panes` in the desktop app: each child opens in split view beside the master
- [ ] `tabs`: one tab or window per child, focus unchanged; in the desktop app the children stay in the sidebar

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
