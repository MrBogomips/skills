# Hub configuration

The hub keeps its rules for child sessions in a `## Child sessions` section of its instruction file: `AGENTS.md`
at the hub root, or `CLAUDE.md` when there is no `AGENTS.md`. The keys are Markdown bullets; read them leniently
(case, wording and order may vary). Every key is optional.

The invocation, not this section, says which repositories a piece of work touches. What the user asks in the
conversation prevails over these keys, and these keys over the defaults.

## Keys

| Key | Content | Default when missing |
|---|---|---|
| Repositories | known repositories: relative path, a one-line role, optionally the base branch. Used to resolve the names the user gives | the hub's child folders holding `.git`, plus the paths in `.gitmodules` |
| Task IDs | the form of a task ID and where tasks live (a file, a tracker) | the task ID the user gives, if any; otherwise the work is named by a short slug |
| Propagate | hub rules, or sections of the hub's instruction file, to carry into every handoff | none |
| Agent | the child's agent kind: `claude`, `codex`, … | `claude` |
| Environment | `auto`, `desktop`, `herdr`, `tmux`, `cli` or `manual` | `auto` |
| Layout | `tabs`, `panes` or `ask` | `ask` |
| Worktrees | `repo`, `always` or `never`, for children that edit files | `repo` |
| Session name | a pattern for children's names, such as `<task>-<repo>` | `<task>-<repo>`, or `<slug>-<repo>` without a task ID |

## Propagate

The hub's rules are the hub's own, and a child does not load them. Carry a rule into a handoff only when
*Propagate* lists it or the user asks for it in the conversation; quote it word for word and cite the file and
section it comes from. Without either, the handoff carries no hub rules.

Hub files and other material that the work needs (specs, designs, a task's text) are different: the handoff cites
them as references by absolute path, as for any input.

## Layout

Where the children appear, in the environments that offer a choice:

| Environment | `tabs` | `panes` |
|---|---|---|
| Desktop app | the children stay in the sidebar | each child also opened in split view beside the master |
| Herdr | one tab per child | the first child in a pane to the right of the master, the next ones stacked below it |
| tmux | one window per child | as in Herdr, in the master's window |

`claude --bg` and the manual case have no layout: skip the question there.

**Asking.** With `ask`, or with no *Layout* key, and no layout in the user's request, ask before starting the
children, in one ask with two questions:

1. Layout, worded for the environment: separate tabs or stacked panes (Herdr, tmux); sidebar only or split view
   (desktop app).
2. Save it as this hub's default: yes or no.

On "save", set `- Layout: <tabs or panes>` in the hub's `## Child sessions` section: replace an existing *Layout*
line, otherwise add the line after the section's last key; create the section from the template below if it is
missing. That answer is the explicit yes this file asks for. Don't commit the change; the report says the file
changed, and committing it follows the hub's own rules. Without "save", use the layout for this conversation
only, and don't ask again in it. A saved value applies in every environment, with the meaning in the table
above.

**Many children.** A stack of panes gets short fast, and in Herdr each split halves the pane it splits. With more
than four children in the stack, open the rest as tabs and say so.

## Names

Build each child's name from the *Session name* pattern, then normalize it: lowercase, characters outside
`a-z0-9_-` replaced by `-`, starting with a letter, at most 24 characters (the desktop app's limit; Herdr allows
32). Add `-2`, `-3`… if a live session already has the name. The repository part is the folder name.

## Worktrees

A child that only reads (investigates, reviews, answers) works in the repository's checkout. A child that edits:

- `repo`: follows the worktree policy in the repository's own instructions (`AGENTS.md`, `CLAUDE.md`). If they
  say nothing readable on worktrees, it works in a worktree.
- `always`: always in a worktree.
- `never`: in the repository's checkout, on a topic branch.

How each environment gets the worktree is in [environments.md](environments.md).

## Template

Offer this when the hub has no `## Child sessions` section, filled with what the hub shows (its repositories, any
task file). Write it into the hub's instruction file only on an explicit yes.

```markdown
## Child sessions

Settings for the spawn-session skill. The invocation says which repositories a piece of work touches.

- Repositories:
  - `frontend/`: web client, base branch `main`
  - `backend/`: API service, base branch `develop`
  - `docs/`: design documents
- Task IDs: `T-123`, listed in `backlog/tasks.md`
- Propagate: none
- Agent: claude
- Environment: auto
- Layout: ask
- Worktrees: repo
- Session name: `<task>-<repo>`
```
