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

## Launch command

A Claude child starts as the master was started, so it gets the same account, the same configuration directory
(without which the two sessions can't message each other) and the same settings. Users often start Claude through
an alias or a wrapper that sets variables and adds flags. Its name can't be seen from inside the session, but its
effect can, and that is what the child replicates:

1. **Master's arguments.** Walk up from the shell's parent process (`ps -o ppid=,command= -p <pid>`) to the first
   whose command runs `claude` (`claude …` or `node …/claude …`), and read its arguments.
2. **Flags to carry**: those that configure the session, such as `--settings`, `--mcp-config`,
   `--strict-mcp-config`, `--plugin-dir`, `--setting-sources`, `--model`, `--agent`, `--append-system-prompt`.
   Leave out the ones that belong to the master's own session (`-n`/`--name`, `-r`/`--resume`,
   `-c`/`--continue`, `--session-id`, `--fork-session`, `-p`/`--print`, `--bg`, `-w`/`--worktree`, `--add-dir`,
   a prompt) and the permission flags (`--dangerously-skip-permissions`, `--permission-mode`): the child takes
   the inherited mode instead. `ps` can't tell where an argument with spaces ends: if one has spaces, ask the user
   for the master's command.
3. **Identity variables**, read with `printenv` in your own shell, which inherits them: `CLAUDE_CONFIG_DIR` when
   set, and `HOME` when it differs from the account's home (`dscl . -read /Users/$USER NFSHomeDirectory` on macOS,
   `getent passwd $USER` on Linux). Other variables only when the user names them. Never dump or copy the
   environment: it holds tokens, which would end up on command lines and in pane scrollback, and values that
   belong to the master's pane or terminal.
4. **Command**: `env HOME=<home> CLAUDE_CONFIG_DIR=<dir> claude <carried flags>`, followed by the flags each
   environment's file adds. Drop `env` and the variables when there are none to set. Each environment's file says
   where the variables go.

For another agent kind, carry only the variables and flags the user names.

## First run in a repository

A repository where the user has never opened an agent may stop the child at a first-run prompt: folder trust, or
for some agents an approval or sandbox mode, or the warning shown the first time a session starts in bypass
mode. Those prompts are the user's: never answer them, by keys or
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
  prompts, the receiver holds it for the user's approval and may let it expire (five minutes by default): the
  reason children start in the master's permission mode by default (see [hub-config.md](hub-config.md)). The
  `crossSessionInbound` setting (`accept`, `hold`, `refuse`) overrides this; for one background child, the user
  can choose `--settings '{"crossSessionInbound":"accept"}'`.
- A send to a desktop app session reports nothing back when the message is held: silence is not an answer.
