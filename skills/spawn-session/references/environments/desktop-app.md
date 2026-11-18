# Claude desktop app

**Start.** Use the app's session-starting tool (`start_session`; in the desktop app it may be deferred, so load
it with the tool search first). If its description or parameters differ from these, follow the tool.

| Parameter | Value |
|---|---|
| `cwd` | `<repo>` |
| `context` | `"fresh"` |
| `initiation` | `"user_asked"` when the user asked for this work |
| `title` | a short title for the session row |
| `name` | `<name>` |
| `prompt` | the handoff |
| `background` | the overall work, the user's decisions, and how this child fits among its siblings (at least 80 characters) |
| `use_worktree` | `true` for a child that edits in a worktree; `false` for a read-only child or one that works in the checkout |
| `source_branch` | the base branch, for a child with a worktree, when the tool takes it |

- The tool accepts `cwd` only for a place the user named: the user's request naming the repository, or the hub
  configuration listing it, is that naming. The app may ask the user to confirm or trust the folder.
- When the tool asks for a known place first, call its listing tool (`list_start_targets`).

**Channel.**

- Child to master: `SendMessage` to the master's name, exactly as listed, spaces included and without quotes.
  Each time a child ends a turn while the master is idle, the app also wakes the master with the start of the
  child's report.
- Master to child: `SendMessage` to the session id the start returned (`local_…`).
- User: opens the child from the sidebar, where it appears as a session linked to the master.

**Layout.** With `panes`, open each child beside the master right after its start, with the app's window tool
(`open_session_in`, target `split`, the session id the start returned), then check with its layout tool
(`get_window_layout`) that the child shows in the split. The tool acts only while the master is on screen; for a
child that does not show, tell the user to drag it from the sidebar into the split. With `tabs`, leave the
children in the sidebar.

**Limits.** The master sees only the 20 most recent sessions that are not archived. Archiving a child can lose its
uncommitted changes. The tool is not in the public documentation: detect it at runtime and never assume it.
