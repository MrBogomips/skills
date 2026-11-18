# Environments

How to start a child, give it a worktree, and talk to it in each environment. `<repo>` is the repository's
absolute path, `<name>` the child's name, `<file>` its handoff file.

Read this file, then only the file of the environment chosen in step 4:

| Environment | File |
|---|---|
| Claude desktop app | [environments/desktop-app.md](environments/desktop-app.md) |
| Herdr | [environments/herdr.md](environments/herdr.md) |
| tmux | [environments/tmux.md](environments/tmux.md) |
| Terminal, Claude Code | [environments/terminal.md](environments/terminal.md) |
| Manual | [environments/manual.md](environments/manual.md) |

**Handoff files.** Herdr, tmux, the terminal and the manual case pass the handoff as a file, because a long prompt on a
command line breaks quoting and, on macOS, the terminal's line limit. Write it in the harness's scratchpad
directory if it has one, otherwise in a new `mktemp -d` directory, as `<name>-handoff.md`. Never inside the hub
or a repository. The prompt on the command line is then one line: `Read and follow <file>` (in the conversation's
language), worded without quotes or apostrophes, with a path free of spaces, so it survives the shell quoting
in the environment's commands. The file sits outside the child's repository: give a Claude child read access to its folder with
`--add-dir <handoff-dir>` on its command line, or it may ask the user before reading it.

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

Say the ones that apply in the report of step 10. Change no setting yourself: the choice is the user's.

- Cross-session messaging needs Claude Code 2.1.224 or later on macOS and Linux, 2.1.234 or later on Windows.
- A message is plain text. It cannot approve a permission prompt, change configuration or run a command.
- By default a message is delivered at once. When the sender and the receiver differ on bypassing permission
  prompts, the receiver holds it for the user's approval and may let it expire (five minutes by default). The
  `crossSessionInbound` setting (`accept`, `hold`, `refuse`) overrides this; for one background child, the user
  can choose `--settings '{"crossSessionInbound":"accept"}'`.
- A send to a desktop app session reports nothing back when the message is held: silence is not an answer.
