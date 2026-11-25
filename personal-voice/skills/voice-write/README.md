---
summary: Applies the tone and lexicon rules you approved in your voice profile when Claude writes documents, emails, messages and posts you will send as your own.
---

# voice-write

`voice-write` applies your voice profile—your approved tone and lexicon rules, plus excerpts of your own writing—when Claude writes text you will send, publish, or hand over as your own, such as documents, reports, emails, messages, or posts. It works in any language you write in and reads the profile without modifying it.

## Why

Drafts written for you carry LLM habits instead of your own phrasing, so you end up fixing the same things by hand every time. `voice-write` applies those fixes before you see the draft.

- It applies only rules you have approved, never observations still waiting for review.
- When the profile has no entries for the language and topic, Claude writes normally and does not present the text as your voice.
- Terms from the current project override your general ones.
- Content comes from your request: the profile changes how the text sounds, never the facts.

## Use cases

### Write to colleagues the way you do

**Context:** Your profile records how you address colleagues and the software terms you use.

**Action:** Ask Claude: "Write a short email to the team: version 2.4 is in the test environment as of today, and the deploy is planned for Friday."

**Result:** An email using your form of address, closing, and terminology, with no facts beyond your request.

### Use a client's terms in that client's project

**Context:** Your profile uses "deploy", while the client project's glossary specifies "release".

**Action:** Ask for the email from inside that project.

**Result:** The email uses "release"; the same request outside the project uses "deploy".

## Usage

Claude loads `personal-voice:voice-write` automatically when you ask for text meant for people. You can also request it directly (for example, "write this in my voice"). The skill takes no arguments; language, topic, and audience come from your request.

```text
Draft an email to our client explaining that the delivery moves to next Tuesday.
```

Claude returns the email in the tone your profile defines for clients. If the topic or audience is unclear, it asks one short question first.

After Claude produces a draft, revising the text or closing the session starts [`voice-learn`](../voice-learn/README.md).

## Inputs and outputs

`voice-write` reads the global store in your `store_dir` directory and, if present, the project store in `.personal-voice/` at the project root. It writes to neither. See [the store format](../../shared/store-format.md) for details on these files.

## Requirements

The `personal-voice` plugin with `store_dir` configured. Until you set `store_dir`, `voice-write` tells you once how to configure it and writes the text normally.

## Limitations

- `voice-write` does not apply to code, code comments, commit messages, or configuration files unless you ask for your voice on that specific text.
- When another skill, a template, or project conventions define the structure, register, or terminology of a text, they take precedence; your profile applies only where they leave room, such as word choice within a sentence.
- A habit appears in drafts only after [`voice-maintain`](../voice-maintain/README.md) has turned it into a rule.
- Claude's own replies to you in chat are not written in your voice.