# gemini-web-research: value gate

**Outcome: Reshape, pending baseline.** Desk review against DESIGN.md, 2026-11-26: a read-only reviewer checked the skill against current Claude Code docs, official Anthropic skills and plugins, and Codex; no run without the skill yet.

- Test 1, not native: largely fails in Claude Code. The bundled `/deep-research` workflow searches from several angles, cross-checks sources and filters claims that do not survive.
- Not covered natively: the deterministic check that each quote is on a page the worker read, spending agy quota instead of Claude usage, and other harnesses.
- Test 3: in Claude Code, ordinary research should go to `/deep-research`.
- Minimum model: Sonnet class, effort medium.

Baseline to run: One hard question through `/deep-research` and through the skill, counting claims whose quote is not on the cited page.
