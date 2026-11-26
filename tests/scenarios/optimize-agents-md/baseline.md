# optimize-agents-md: value gate

**Outcome: Reshape, pending baseline.** Desk review against DESIGN.md, 2026-11-26: a read-only reviewer checked the skill against current Claude Code docs, official Anthropic skills and plugins, and Codex; no run without the skill yet.

- Test 1, not native: unclear. For Claude Code, `/doctor` proposes CLAUDE.md trims and moves guidance to skills and nested files, and `/doctor prompt-audit` finds stale or conflicting instructions. Nothing native covers an AGENTS.md shared with Codex.
- Test 2, durable: pass for the discipline (safety rules versus style, no-loss check, approval per diff).
- Test 3: hand Claude Code-only trimming to `/doctor` and prompt-audit.
- Minimum model: Sonnet class, effort high.

Baseline to run: A 350-line CLAUDE.md linked to AGENTS.md and shared with Codex, mixing safety rules, history and path-specific blocks: `/doctor` plus prompt-audit against the skill, scored on lost lines and moved safety rules.
