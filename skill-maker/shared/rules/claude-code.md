# Rules for agents, hooks and commands (Claude Code)

When plugin-dev is installed, use it to write agents, hooks and commands. These rules are what
`skill-check` verifies afterwards.

### C1. An agent file is a contract

An agent has a `name` and a `description` that says when to dispatch it. Its body states the role, the
inputs it receives, the format of its output and a "done when" that can be checked. The caller's
procedure stays in the caller.

Official source: docs-sub-agents, plugin-dev · Checked by: both (the validator checks the two keys)

### C2. Read-only means read-only tools

An agent that must not change files gets only read tools (`tools: Read, Grep, Glob`). An instruction
not to edit is a request; a tool list is a guarantee.

Official source: docs-sub-agents · Checked by: reviewer

### C3. Reviewers start fresh

A reviewer agent receives the files to review, never the author's own assessment of them, so that its
reading is independent.

Checked by: reviewer

### C4. Effort fits the role

Judgment roles (review, design) get a high effort; collection roles (search, inventory) a low or medium
one. The model is inherited unless there is a reason to fix it.

Official source: docs-sub-agents · Checked by: reviewer

### C5. Hooks: command for facts, prompt for judgment

Use a command hook for a deterministic check: it can be scripted and tested with sample event JSON. Use
a prompt hook when the decision needs judgment. In command hooks, quote variables, validate paths and set
a timeout.

Official source: docs-hooks, plugin-dev · Checked by: reviewer

### C6. A rule that keeps being skipped becomes a hook

When agents keep skipping a step a skill asks for, enforce it with a hook instead of louder wording.

Official source: hookify · Checked by: reviewer

### C7. Commands speak to the agent

A command file is an instruction to the agent, not a message to the user.

Official source: plugin-dev · Checked by: reviewer

### C8. Hand-off for authoring

skill-maker does not write agents, hooks or commands: plugin-dev does, when installed. Without it, write
them from these rules and the official pages, then run `skill-check`.

Official source: plugin-dev · Checked by: reviewer
