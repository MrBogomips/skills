# gemini-editorial-review: value gate

**Outcome: Go (keep).** Desk review against DESIGN.md, 2026-11-26: a read-only reviewer checked the skill against current Claude Code docs, official Anthropic skills and plugins, and Codex; no run without the skill yet.

- Test 1, not native: unclear on quality alone; passes as an integration: a review by a second model without the writer's habits, with checks that code, links and placeholders are unchanged.
- Test 2, durable: pass.
- Test 4: the profile mapping in SKILL.md can shrink.
- Minimum model: Sonnet class (it judges which instruction-file rules are about writing).

Baseline to run: An agent-written Italian README with house rules in AGENTS.md: a plain revision request against the skill, scored on a blind count of machine-writing tells and broken invariants.
