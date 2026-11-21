---
summary: Summarizes a reply in a few bullets that separate decisions, open questions and next actions, and can keep a short TLDR footer on later long replies.
---

# tldr

`tldr` condenses a reply into a few bullets that separate decisions, open questions and next actions. Once invoked, it also adds a short TLDR footer to later long replies until you tell it to stop.

## Why

Long agent replies often bury what you need to decide or do in implementation detail and chronology. `tldr` leads with what needs your attention and distinguishes what is proposed, done and verified. The work and the full reply stay unchanged; only the summary is kept brief.

## Installation

```bash
npx skills add MrBogomips/skills --skill tldr
```

This installs the same skill included in the `skills` plugin, under the name `tldr` instead of `skills:tldr`.

## Usage

Send `TLDR`, `TL;DR`, `/tldr` or `$tldr` as a standalone prompt (or `/skills:tldr` when using the plugin in Claude Code). This summarizes the preceding reply:

```markdown
**TLDR**

- **Question:** Postmark or SES for email?
- **Next:** Check account deletion on staging; unit tests passed.
- **Decision:** Deleted accounts can be recovered for 30 days.
- **Caution:** Final deletion is irreversible.
```

- Name another message or topic to summarize it instead.
- Any invocation also turns on the TLDR footer for the rest of the conversation unless you limit it (for example, "just this once"). Short replies, progress updates and tool calls get no footer.
- Send "Stop TLDR" to turn the footer off.