# gemini-translate: value gate

**Outcome: Go (keep), as an integration.** Desk review against DESIGN.md, 2026-11-26: a read-only reviewer checked the skill against current Claude Code docs, official Anthropic skills and plugins, and Codex; no run without the skill yet.

- Test 1, not native: fails on translation quality alone (a frontier model translates well); passes as an integration used only when the user asks for Gemini, with the invariant check and chunking.
- Test 2: the README's Why leans on a gap that is closing (Gemini as a stronger translator); rewrite it around the integration and the invariant check.
- Test 4: the register mapping in SKILL.md can go.

Baseline to run: Translate README.md to Italian, technical register, keeping code intact: a plain request against the skill.
