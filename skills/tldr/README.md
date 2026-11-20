---
summary: Summarizes a reply in a few bullets that separate decisions, open questions and next actions, and can keep a short TLDR footer on later long replies.
---

# tldr

`tldr` condenses a reply into a few bullets that keep decisions, open questions and required actions easy to tell apart. Once invoked, it also adds a short TLDR footer to later long replies, until you tell it to stop.

## Why

Agent replies are long, and what you have to decide or do is often buried in implementation detail and chronology. `tldr` leads with what needs your attention and keeps the difference between proposed, done and verified. Brevity applies to the summary only: the work and the full reply stay as they are.

## Installation

```bash
npx skills add MrBogomips/skills --skill tldr
```

It is the same skill as in the `skills` plugin, installed under the name `tldr` instead of `skills:tldr`.

## Usage

Send `TLDR`, `TL;DR`, `/tldr` or `$tldr` as a prompt on its own (`/skills:tldr` in Claude Code with the plugin). You get the summary of the reply just before it:

```markdown
**TLDR**

- **Question:** Postmark or SES for email?
- **Next:** Check account deletion on staging; unit tests passed.
- **Decision:** Deleted accounts can be recovered for 30 days.
- **Caution:** Final deletion is irreversible.
```

- Name another message or topic to summarize that one instead.
- Any invocation also turns the footer on for the rest of the conversation, unless you limit it ("just this once"). Short replies, progress updates and tool calls get no footer.
- "Stop TLDR" turns it off.
