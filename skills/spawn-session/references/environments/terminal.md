# Terminal, Claude Code

```bash
cd <repo> && claude --bg <carried flags> -n <name> --permission-mode <mode> --add-dir <handoff-dir> "Read and follow <file>"
```

- The command prints the child's id. The user opens the child with `claude attach <name or id>` and lists
  background sessions with `claude agents`.
- `<carried flags>` come from *Launch command* in [environments.md](../environments.md). The identity variables
  need nothing: the child inherits them from your shell.
- `<mode>` is the permission mode the children inherit (see [hub-config.md](../hub-config.md)).
- **Worktree:** a background session moves into a worktree under `<repo>/.claude/worktrees/` before its first
  edit, unless the repository sets `worktree.bgIsolation` to `"none"`. For a child that must work in the
  checkout, add `--settings '{"worktree":{"bgIsolation":"none"}}'`.

**Channel.**

- `SendMessage` in both directions: child to the master's name, master to `<name>`.
- To hear when a child finishes its turn, the master sends `SendMessage` with `notify_when_idle` once: one notice
  arrives. Never poll `ListAgents` or ask "are you done?" in a loop.
