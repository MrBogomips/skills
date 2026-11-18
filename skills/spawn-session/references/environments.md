# Environments

How to start a child, give it a worktree, and talk to it in each environment. `<repo>` is the repository's
absolute path, `<name>` the child's name, `<file>` its handoff file.

**Handoff files.** Herdr, tmux, the terminal and the manual case pass the handoff as a file, because a long prompt on a
command line breaks quoting and, on macOS, the terminal's line limit. Write it in the harness's scratchpad
directory if it has one, otherwise in a new `mktemp -d` directory, as `<name>-handoff.md`. Never inside the hub
or a repository. The prompt on the command line is then one line: `Read and follow <file>` (in the conversation's
language), worded without quotes or apostrophes, with a path free of spaces, so it survives the shell quoting
below. The file sits outside the child's repository: give a Claude child read access to its folder with
`--add-dir <handoff-dir>` on its command line, or it may ask the user before reading it.

## Claude desktop app

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

- Child to master: `SendMessage` to the master's name, exactly as listed, spaces included and without quotes. Each time a child ends a turn while the master is idle, the
  app also wakes the master with the start of the child's report.
- Master to child: `SendMessage` to the session id the start returned (`local_…`).
- User: opens the child from the sidebar, where it appears as a session linked to the master.

**Limits.** The master sees only the 20 most recent sessions that are not archived. Archiving a child can lose its
uncommitted changes. The tool is not in the public documentation: detect it at runtime and never assume it.

## Herdr

Requires `HERDR_ENV=1`. Read IDs from the JSON that each command returns; never derive them.

```bash
herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd <repo> --label <name> --no-focus
# read the root pane ID from .result.root_pane
herdr agent start <name> --kind claude --pane <pane-id> -- -n <name> --add-dir <handoff-dir>
herdr agent prompt <name> "Read and follow <file>"
```

- `--kind` is the child's agent kind; `herdr agent` lists the installed kinds. Arguments after `--` go to the agent
  itself: `-n <name>` gives a Claude child the same name in `ListAgents`. Other kinds take no such flag.
- `agent start` returns once the agent is ready. If it returns `agent_not_ready`, read the pane with
  `herdr agent read <name>` and ask the user before answering any dialog there.
- Herdr agent names match `[a-z][a-z0-9_-]{0,31}`; the names from [hub-config.md](hub-config.md) already do.
- **Worktree:** the child creates it as its handoff says (the mode from [hub-config.md](hub-config.md)), where
  its repository's policy puts worktrees; otherwise a Claude child uses its own worktree support, and another
  kind runs `git worktree add` into `<repo>-worktrees/<name>` next to the repository.
- When the user wants to watch the child, bring its tab forward after the prompt: `herdr agent focus <name>`.
- Never close tabs or panes you did not create, and close yours only when the user asks.

**Channel.**

- A Claude child: `SendMessage` in both directions, as in the terminal case below.
- Another kind: no messaging. The child writes its reports as replies in its own pane, with the prefix; the
  master reads them with `herdr agent read <name> --source recent-unwrapped --lines 120`, and waits for a reply
  with `herdr agent wait <name>` run as a background command, so the master stays free. Follow-ups go with
  `herdr agent prompt <name> "[master] <text>"`, only while `herdr agent get <name>` shows it idle or done, so
  they don't mix with what the user is typing. The text arrives as if the user typed it, so the handoff tells
  the child that lines starting with `[master]` come from the master and fall under the fixed rules. A long
  follow-up goes in a file, like the handoff.
- User: switches to the child's tab, or asks the master to bring it forward (`herdr agent focus <name>`).

## tmux

Requires `TMUX` to be set (the master runs inside tmux). Read the pane ID from the output; never derive it.

```bash
tmux new-window -d -c <repo> -n <name> -P -F '#{pane_id}'
# prints the pane ID, such as %12
tmux send-keys -t <pane-id> -l "claude -n <name> --add-dir <handoff-dir> 'Read and follow <file>'"
tmux send-keys -t <pane-id> Enter
```

- `-d` opens the window without moving the user's focus. The window starts with a shell, so it stays open when
  the agent exits.
- Type the start command of the child's agent kind. `-n <name>` is for a Claude child; other kinds take their own
  command, such as `codex 'Read and follow <file>'`.
- **Worktree:** the child creates it as its handoff says, as in Herdr.
- When the user wants to watch the child, bring its window forward: `tmux select-window -t <pane-id>`.
- Never kill windows or panes you did not create, and kill yours only when the user asks.

**Channel.**

- A Claude child: `SendMessage` in both directions, as in the terminal case below.
- Another kind: no messaging. The child writes its reports as replies in its own pane, with the prefix; the
  master reads them with `tmux capture-pane -p -J -t <pane-id> -S -120`. Follow-ups go as one line,
  `tmux send-keys -t <pane-id> -l "[master] <text>"` then `tmux send-keys -t <pane-id> Enter`, only when the
  agent waits for input: its input box is at the bottom of the capture and two captures a few seconds apart are
  the same. The `[master]` rule of Herdr applies. A long follow-up goes in a file, like the handoff.
- tmux has no wake-up for such a child: capture its pane when the user asks or when the master needs its answer,
  never in a polling loop.
- User: switches to the child's window (`prefix` then `w` lists them).

## Terminal, Claude Code

```bash
cd <repo> && claude --bg -n <name> --add-dir <handoff-dir> "Read and follow <file>"
```

- The command prints the child's id. The user opens the child with `claude attach <name or id>` and lists
  background sessions with `claude agents`.
- **Worktree:** a background session moves into a worktree under `<repo>/.claude/worktrees/` before its first
  edit, unless the repository sets `worktree.bgIsolation` to `"none"`. For a child that must work in the
  checkout, add `--settings '{"worktree":{"bgIsolation":"none"}}'`.

**Channel.**

- `SendMessage` in both directions: child to the master's name, master to `<name>`.
- To hear when a child finishes its turn, the master sends `SendMessage` with `notify_when_idle` once: one notice
  arrives. Never poll `ListAgents` or ask "are you done?" in a loop.

## Manual

For any other harness, or when the start fails. Write the handoff files, then give the user, per child, one block
with the commands to run in a new terminal:

```bash
cd <repo>
codex "Read and follow <file>"
```

Use the start command of the child's agent kind. For a Claude child,
`claude -n <name> --add-dir <handoff-dir> "Read and follow <file>"` keeps the messaging channel. With other
kinds there is no automatic channel: the child's reports reach the master through the user.

## First run in a repository

A repository where the user has never opened an agent may stop the child at a first-run prompt: folder trust, or
for some agents an approval or sandbox mode. Those prompts are the user's: never answer them, by keys or
otherwise.

- **Desktop app:** the session tool can refuse to set up a worktree in a repository the app has never had a
  session in. Tell the user to open a session in that folder once from the app, and don't retry until they say
  they did. Meanwhile offer another environment if one is available.
- **`claude --bg`:** it refuses with `Workspace not trusted`. The user runs `claude` once in the repository and
  accepts the trust prompt, then you retry; or start the child in Herdr or tmux, where the prompt shows in the
  child's own window.
- **Herdr, tmux, manual:** the trust prompt shows in the child's window. Tell the user which window to answer it
  in. In Herdr, `agent start` returns `agent_not_ready`: send the handoff prompt once the agent is ready. In tmux
  and the manual case the prompt is already on the command line and runs after the user's answer.

## Messaging caveats (Claude Code)

Say the ones that apply in the report of step 9. Change no setting yourself: the choice is the user's.

- Cross-session messaging needs Claude Code 2.1.224 or later on macOS and Linux, 2.1.234 or later on Windows.
- A message is plain text. It cannot approve a permission prompt, change configuration or run a command.
- By default a message is delivered at once. When the sender and the receiver differ on bypassing permission
  prompts, the receiver holds it for the user's approval and may let it expire (five minutes by default). The
  `crossSessionInbound` setting (`accept`, `hold`, `refuse`) overrides this; for one background child, the user
  can choose `--settings '{"crossSessionInbound":"accept"}'`.
- A send to a desktop app session reports nothing back when the message is held: silence is not an answer.
