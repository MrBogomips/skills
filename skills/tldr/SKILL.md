---
name: tldr
description: >-
  Summarizes a reply in a few bullets and can keep a TLDR footer on later replies. Use when the user invokes
  /tldr or $tldr, sends TLDR or TL;DR as a standalone prompt (any case), or asks to use TLDR for a reply or for
  the session. Also applies to later replies while TLDR mode is active.
license: MIT
compatibility: Any agent harness. Needs no tools.
---

# TLDR

Give the user only what matters, in the fewest clear words. Keep decisions, open questions and required actions easy to tell apart.

## Activation and duration

- A bare `TLDR`, `TL;DR`, `/tldr` or `$tldr` summarizes the assistant reply just before it. Output only the TLDR for that turn.
- If the user names another message or topic, summarize that instead, using earlier context only to clarify it. Always answer an explicit request, however short the source.
- Any invocation also turns TLDR mode on for the rest of the conversation, unless the user limits it ("just this once"). If the invocation comes with a task, do the task; its reply follows the footer rule.
- While the mode is on, answer normally and append a TLDR footer to a final reply only when the reply is at least twice as long as its TLDR would be. Otherwise add no footer. Progress updates and tool calls get none.
- "Stop TLDR" or an equivalent turns the mode off. An instruction about one reply wins for that reply.
- A mention inside quoted text, code, or a discussion about this skill is not an invocation.

## What earns a place

Keep the facts that change what the user should understand, decide or do:

- the main outcome or current state;
- consequential choices and their practical effect;
- open questions, blockers and actions the user must take;
- material risks, limits or missing verification.

Lead with whatever needs the user's attention. Keep uncertainty, and the difference between proposed, done and verified. Include only what the source supports. Leave out implementation detail, chronology, repeated context and filler. Brevity applies to the summary, never to the work itself.

## Format

A standalone summary starts directly with `**TLDR**`, a blank line, then compact bullets. A footer is the same block after the normal answer, separated by a blank line, `---` and another blank line.

Aim for 1 to 4 bullets and about 60 words; go over only to keep essential meaning. One idea per bullet, in plain language. Use short labels such as **Decision**, **Question**, **Next** or **Caution** where they help. No empty categories, nested lists, preamble or closing offer. Keep a link or command the user needs in order to act.

Example footer:

---

**TLDR**

- **Question:** Postmark or SES for email?
- **Next:** Check account deletion on staging; unit tests passed.
- **Decision:** Deleted accounts can be recovered for 30 days.
- **Caution:** Final deletion is irreversible.

Adapted from [zazencodes/skills](https://github.com/zazencodes/skills) (MIT, see LICENSE-upstream).
