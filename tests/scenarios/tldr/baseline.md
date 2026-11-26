# tldr baseline — 2026-11-26

**Value gate: go, as a shortcut skill** (DESIGN.md, Shortcut skills). A plain "TLDR" does not give the standard format; getting it every time takes a long instruction. Human-invoked by name or by the exact words TLDR, TL;DR, "in short"; thin body holding only the format and the footer rule.

Fixture: fixture-conversation.md (Italian on purpose, to test the reply language) (Italian, ~400-word status reply). Run A = session model, run B = sonnet. No skill.
Turn 1 "TLDR"; turn 2 "keep the TLDR at the end from now on" + long how-to; turn 3 short question.

| Check (skill standard) | Run A | Run B |
|---|---|---|
| Standalone: `**TLDR**` header, 1-4 bullets, ~60 words | ✗ ~210 words, nested list | ✗ "In breve", ~260 words, 4 bullets + 5-item list |
| Leads with what needs attention (decisions first) | ✗ chronological, decisions last | ✗ chronological, actions last |
| Language of the conversation | ✗ answered in English | ✓ |
| Footer format (`---`, header, bullets, labels) | ✗ one prose line "TLDR: ..." | ✗ bullets, no separator, no labels |
| Footer only when reply ≥ 2x its TLDR | ✗ footer on a 3-line reply | ✓ |
| Proposed / done / verified kept apart | ✓ | ✓ |

Failures: the standard format is not produced by a plain "TLDR" (2/2), the footer format drifts (2/2), length and ordering off (2/2).
