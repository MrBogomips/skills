---
name: kaizen
description: "Retrospective of the current Claude Code session: links the errors, reworks, corrections and ambiguities met in it to the skills, agents, rules, CLAUDE.md, memory, hooks, MCP tools and settings behind them, proposes small reviewed edits with options to the project's own files, and gives advice only for user, plugin or managed assets. Use when the user runs /kaizen, accepts the kaizen offer, or asks what to fix in the project's skills, rules or settings after this session. Not for static audits of instruction files, pruning memory or CLAUDE.md, cross-session reports, or writing new skills."
---

# kaizen

Turn this session's friction into small, reviewed fixes to the project's own assets.

## Hard rules — they override everything below

1. **Run only at the user's request**: they ran `/kaizen`, accepted the kaizen offer, or asked for this
   retrospective. Never start it on your own.
2. **Read-only until the user names item IDs** (`references/proposals.md` §Authorization).
3. **Every item cites an incident of this session** and the asset text it links to. "Could be clearer"
   is not an incident. Zero findings is a valid result.
4. **Edit only project assets** (`references/assets.md` §Origin); everything else gets advice.
5. **Never create a skill or agent file** (an incident that needs one becomes advice), **never edit auto
   memory, never commit, stash or check out.**
6. **What a harness command or another available tool owns becomes one pointer line**
   (`references/assets.md` §Owned elsewhere).
7. **Chat only**: no report files, no state files.
8. **References must be readable.** If a file under `references/` cannot be read, stop and name it.

## Workflow

### 1. Inventory (read-only)

List for yourself the assets active in this session: instruction files loaded (CLAUDE.md, rules,
memory), skills invoked, subagents dispatched, MCP tools called, hooks that ran or gave feedback,
settings and permission rules met. Take them from the conversation; search the transcript only for what
compaction removed (`references/assets.md` §Evidence). This session's id is `${CLAUDE_SESSION_ID}`.

Classify each asset by origin (§Origin). Do not print the inventory: `/context` already shows it.

### 2. Incidents

List the incidents: tool errors, reworks, user corrections, ambiguities you resolved by guessing or
asking, skills that misfired or did not fire, unusable subagent output, contradictory instructions you
met, hook interruptions. Link each to the asset and the line or section behind it (§Incidents). Drop the
incidents no asset explains, such as a typo in the request or a network failure.

Nothing left: reply "kaizen: nothing to review in this session." and stop.

### 3. Route

For each incident:

- owned by a harness command or another tool → pointer (group C);
- asset not editable → advice with its owner route (group B);
- editable project asset, or a project file that should hold a memory fact that mattered → proposal
  (group A).

### 4. Draft

Write the A items as in `references/proposals.md` §Item format.

### 5. Review

If any A item edits model-facing text, dispatch one reviewer for all of them as in §Review, then apply
its verdicts.

### 6. Recap, then stop

Present the recap as in §Recap, end with its closing line and **end your turn**.

### 7. Authorize and apply

Parse the reply as in §Authorization, echo the authorized set, and apply as in §Apply.

### 8. Report

Close with the final report (§Final report).
