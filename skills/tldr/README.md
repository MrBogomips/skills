---
summary: Summarizes a reply in one fixed format, attention first, and can keep it as a footer on later long replies.
---

# tldr

`tldr` condenses a reply into a few labelled bullets, always in the same format. Once invoked, it also adds the same footer to later long replies until you tell it to stop.

## Why

Any model can summarize when asked, but a bare "TLDR" gets a different shape each time: two to four times too long, in chronological order, sometimes in another language, and a footer that drifts from a prose line to a list. Getting the same format every time takes a long instruction. `tldr` stands for that instruction: a few labelled bullets, what needs your attention first, proposed, done and verified kept apart, in the language of the conversation. The work and the full reply stay unchanged.

## Installation

```bash
npx skills add MrBogomips/skills --skill tldr
```

This installs the same skill included in the `skills` plugin, under the name `tldr` instead of `skills:tldr`.

## Usage

Send `TLDR`, `TL;DR`, "in short", `/tldr` or `$tldr` as a standalone prompt (or `/skills:tldr` when using the plugin in Claude Code). This summarizes the preceding reply:

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
- Other ways of asking for a summary ("summarize this") do not trigger it: the agent answers them in its own way.