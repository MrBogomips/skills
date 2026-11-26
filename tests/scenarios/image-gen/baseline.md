# image-gen: value gate

**Outcome: Go (merged).** Desk review against DESIGN.md, 2026-11-26: a read-only reviewer checked the skill against current Claude Code docs, official Anthropic skills and plugins, and Codex; no run without the skill yet.

- Test 1, not native: pass. Claude Code has no image tool and no official skill generates images.
- Test 2, durable: pass. An integration on the user's Codex quota or Gemini key.
- AGENTS.md "Backends, not copies": `codex-image-gen` and `google-image-gen` shared 124 identical lines and the same options; merged into this skill with a `codex` (default) and an `api` backend.
- Test 4: generic image-prompt advice cut to two lines.

No baseline needed: the outcome does not depend on it.
