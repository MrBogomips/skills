# Herdr

Requires `HERDR_ENV=1`. Read IDs from the JSON that each command returns; never derive them.

Make the child's pane with the layout from [hub-config.md](../hub-config.md):

```bash
# tabs: a tab per child; read the pane ID from .result.root_pane
herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd <repo> --label <name> --no-focus [--env KEY=VALUE …]
# panes: the first child to the right of the master (--current is the calling pane, not the focused one);
# read the pane ID from .result.pane
herdr pane split --current --direction right --cwd <repo> --no-focus [--env KEY=VALUE …]
# panes: each next child below the last child's pane
herdr pane split <last-child-pane-id> --direction down --cwd <repo> --no-focus [--env KEY=VALUE …]
```

Then, in that pane:

```bash
herdr agent start <name> --kind claude --pane <pane-id> -- <carried flags> -n <name> --permission-mode <mode> --add-dir <handoff-dir>
herdr agent prompt <name> "Read and follow <file>"
```

- *Launch command* in [environments.md](../environments.md) gives the identity variables and the carried flags.
  `agent start` runs the agent's own executable, so the variables go on the pane, one `--env` per variable, and
  the carried flags after `--`.
- `--kind` is the child's agent kind; `herdr agent` lists the installed kinds. Arguments after `--` go to the agent
  itself: `-n <name>` gives a Claude child the same name in `ListAgents`, and `--permission-mode <mode>`
  sets the mode the children inherit (see [hub-config.md](../hub-config.md)). Other kinds take their own flags.
- `agent start` returns once the agent is ready. If it returns `agent_not_ready`, read the pane with
  `herdr agent read <name>` and ask the user before answering any dialog there.
- Herdr agent names match `[a-z][a-z0-9_-]{0,31}`; the names from [hub-config.md](../hub-config.md) already do.
- **Worktree:** the child creates it as its handoff says (the mode from [hub-config.md](../hub-config.md)), where
  its repository's policy puts worktrees; otherwise a Claude child uses its own worktree support, and another
  kind runs `git worktree add` into `<repo>-worktrees/<name>` next to the repository.
- With `panes`, label the pane so the user can tell the children apart: `herdr pane rename <pane-id> <name>`.
- With `tabs`, when the user wants to watch a child, bring its tab forward after the prompt:
  `herdr agent focus <name>`.
- Never close tabs or panes you did not create, and close yours only when the user asks.

**Channel.**

- A Claude child: `SendMessage` in both directions: child to the master's name, master to `<name>`. To hear
  when a child finishes its turn, the master sends `SendMessage` with `notify_when_idle` once: one notice
  arrives. Never poll `ListAgents` or ask "are you done?" in a loop.
- Another kind: no messaging. The child writes its reports as replies in its own pane, with the prefix; the
  master reads them with `herdr agent read <name> --source recent-unwrapped --lines 120`, and waits for a reply
  with `herdr agent wait <name>` run as a background command, so the master stays free. Follow-ups go with
  `herdr agent prompt <name> "[master] <text>"`, only while `herdr agent get <name>` shows it idle or done, so
  they don't mix with what the user is typing. The text arrives as if the user typed it, so the handoff tells
  the child that lines starting with `[master]` come from the master and fall under the fixed rules. A long
  follow-up goes in a file, like the handoff.
- User: types in the child's pane, or switches to its tab, or asks the master to bring it forward
  (`herdr agent focus <name>`).
