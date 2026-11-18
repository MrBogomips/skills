# tmux

Requires `TMUX` to be set (the master runs inside tmux). Read the pane ID from the output; never derive it.

Make the child's pane with the layout from [hub-config.md](../hub-config.md); each command prints the pane ID,
such as `%12`:

```bash
# tabs: a window per child
tmux new-window -d -c <repo> -n <name> -P -F '#{pane_id}'
# panes: the first child to the right of the master's pane
tmux split-window -h -d -t "$TMUX_PANE" -c <repo> -P -F '#{pane_id}'
# panes: child k of n (k >= 2) below the last child's pane, sized so the stack has equal heights
tmux split-window -v -d -t <last-child-pane-id> -l "$(( 100 * (n - k + 1) / (n - k + 2) ))%" -c <repo> -P -F '#{pane_id}'
```

Then label the pane and start the agent in it:

```bash
tmux select-pane -t <pane-id> -T <name>
tmux send-keys -t <pane-id> -l "claude -n <name> --add-dir <handoff-dir> 'Read and follow <file>'"
tmux send-keys -t <pane-id> Enter
```

- `-d` keeps the user's focus where it is. The pane starts with a shell, so it stays open when the agent exits.
- The pane title (`select-pane -T`) names the child in `tmux list-panes -a -F '#{pane_title}'`, for the
  duplicates check, and on the pane border when `pane-border-status` is on.
- Type the start command of the child's agent kind. `-n <name>` is for a Claude child; other kinds take their own
  command, such as `codex 'Read and follow <file>'`.
- **Worktree:** the child creates it as its handoff says (the mode from [hub-config.md](../hub-config.md)), where
  its repository's policy puts worktrees; otherwise a Claude child uses its own worktree support, and another
  kind runs `git worktree add` into `<repo>-worktrees/<name>` next to the repository.
- With `tabs`, when the user wants to watch a child, bring its window forward: `tmux select-window -t <pane-id>`.
- Never kill windows or panes you did not create, and kill yours only when the user asks.

**Channel.**

- A Claude child: `SendMessage` in both directions: child to the master's name, master to `<name>`. To hear
  when a child finishes its turn, the master sends `SendMessage` with `notify_when_idle` once: one notice
  arrives. Never poll `ListAgents` or ask "are you done?" in a loop.
- Another kind: no messaging. The child writes its reports as replies in its own pane, with the prefix; the
  master reads them with `tmux capture-pane -p -J -t <pane-id> -S -120`. Follow-ups go as one line,
  `tmux send-keys -t <pane-id> -l "[master] <text>"` then `tmux send-keys -t <pane-id> Enter`, only when the
  agent waits for input: its input box is at the bottom of the capture and two captures a few seconds apart are
  the same. The text arrives as if the user typed it, so the handoff tells the child that lines starting with
  `[master]` come from the master and fall under the fixed rules. A long follow-up goes in a file, like the handoff.
- tmux has no wake-up for such a child: capture its pane when the user asks or when the master needs its answer,
  never in a polling loop.
- User: types in the child's pane, or switches to its window (`prefix` then `w` lists them).
