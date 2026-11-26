---
name: tldr
description: >-
  Summarizes a reply in a fixed TLDR format and can keep it as a footer on later replies. Use only when the user
  invokes /tldr or $tldr, or types TLDR, TL;DR or "in short" as their message or as an instruction for the
  session; also on later replies while the mode is on. Not for summaries asked for in other words.
license: MIT
compatibility: Any agent harness. Needs no tools.
---

# TLDR

A fixed format for summaries. The summarizing is yours; this skill only sets the shape.

## Activation

- `TLDR`, `TL;DR`, "in short", `/tldr` or `$tldr` on its own summarizes the reply just before it, or the message
  or topic the user names. Output only the TLDR.
- Any invocation turns the mode on for the rest of the conversation unless the user limits it. While it is on,
  answer normally and add the TLDR as a footer to a final reply only when the reply is at least twice as long as
  its TLDR. Progress updates and short replies get none. "Stop TLDR" turns it off.
- A mention inside quoted text or code, or a discussion of this skill, is not an invocation.

## Format

- Start with `**TLDR**`, a blank line, then 1 to 4 bullets, about 60 words in all. A footer is the same block
  after `---`, with a blank line on each side.
- Lead with what needs the user's attention: decisions, questions, actions, risks. Then the outcome.
- One idea per bullet, flat (no nested lists), with a bold label where it helps: **Decision**, **Question**,
  **Next**, **Caution**, **Done**.
- Keep proposed, done and verified apart. Keep a link or command the user needs to act.
- Write in the language of the conversation. No preamble, no closing offer.

Example footer:

---

**TLDR**

- **Question:** Postmark or SES for email?
- **Next:** Check account deletion on staging; unit tests passed.
- **Caution:** Final deletion is irreversible.
