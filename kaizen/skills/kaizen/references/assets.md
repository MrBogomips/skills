# Assets

## Origin

Classify every asset linked to an incident. Only `project` is editable.

| Origin | How to recognize it | Route |
|---|---|---|
| project | Inside this repository, tracked (`git ls-files --error-unmatch FILE` succeeds), not generated | Proposal |
| local | Inside the repository but untracked or ignored, e.g. `CLAUDE.local.md`, `.claude/settings.local.json` | Advice: the user edits it |
| generated | Says it is generated or must not be edited, or the project's CLAUDE.md names the tool that writes it | Advice: change it through that tool |
| user | Under the user configuration directory (`$CLAUDE_CONFIG_DIR`, else `~/.claude/`): CLAUDE.md, rules, skills, agents, settings | Advice: the user |
| auto memory | `<config>/projects/<project>/memory/` | Advice, or a promotion proposal (proposals.md §Item format) |
| plugin | Inside the plugin cache or a `--plugin-dir`; skills and agents named `plugin:…`; tools named `mcp__plugin_…` | Advice: the `repository` or `homepage` URL in the plugin's `plugin.json` |
| managed | Managed policy settings or CLAUDE.md set by an administrator | Advice: the administrator |
| bundled | Built into Claude Code, no file (bundled skills, built-in agents and tools) | Advice: `/feedback` |

Outside a git repository every asset is advice.

## Evidence

Take evidence from the conversation first: the instruction files listed as loaded, Skill and Agent
calls, MCP tool calls, hook feedback, permission prompts and denials, the user's corrections.

The transcript holds what compaction removed. Find it with
`find "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects" -name "<session id>.jsonl"` (the id is in SKILL.md
§1). Never read it whole; count or extract with `grep -c` / `grep -oE`:

| Evidence | Pattern |
|---|---|
| Skill calls | `"name":"Skill","input":\{"skill":"[^"]*"` |
| Subagent dispatches | `"subagent_type":"[^"]*"` |
| MCP calls | `"name":"mcp__[^"]*"` |
| Instruction files loaded | `"nested_memory"`, `"type":"Project"`, `"type":"User"`, `"type":"AutoMem"` |
| Tool errors | `.{0,200}"is_error":true` |
| User interruptions | `\[Request interrupted by user` |
| Hook runs | `"type":"hook_[a-z_]*"` |

The transcript format is internal to Claude Code. If a pattern finds nothing, rely on the conversation
and say that the transcript could not be read.

## Incidents

| Incident | Look first at |
|---|---|
| A command, path or name from the instructions failed | The CLAUDE.md, rule or skill line that names it |
| The user corrected the same thing more than once | The instruction that should cover it, or its absence |
| A skill fired on an unrelated request, or did not fire when it should | That skill's `description` |
| Following a skill's steps caused rework | The step in the skill body or its references |
| A subagent returned unusable output | Its agent file (prompt, tools) or the prompt that dispatched it |
| An MCP tool was misused or its result misread | The skill that calls it, or the tool's description: a project asset only when the server's source is in this repository |
| Two loaded instructions pulled in opposite directions | Both files; change the one with less authority |
| A hook blocked or nagged without reason | The hook's command or matcher |
| A memory fact prevented or caused an error | The memory file |

## Owned elsewhere

These findings become one pointer line, and only if the feature or skill is available in this session.

| Finding | Pointer |
|---|---|
| Instruction files that are stale, bloated, written for older models, or contradict each other, without this session acting on them | `/doctor prompt-audit [path]`; for memory, a context pruning skill such as context-hygiene |
| Unused or costly skills, MCP servers or plugins; slow hooks | `/doctor`, `/skill-doctor` |
| Patterns across many sessions | `/insights` |
| Routine commands that keep asking for permission | `/fewer-permission-prompts` |
| Corrections and preferences to remember | Auto memory already records them: nothing to do |
