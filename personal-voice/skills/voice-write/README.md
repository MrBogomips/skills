---
summary: Applies the tone and lexicon rules you approved in your voice profile when Claude writes documents, emails, messages and posts you will send as your own.
---

# voice-write

When Claude writes text you will send, publish or hand over as your own (documents, reports, emails,
messages, posts), `voice-write` applies your voice profile: the tone and lexicon rules you approved
and excerpts of your own writing. It works in any language you write in, and it only reads the
profile.

## Why

A draft written for you carries LLM habits and misses your words, so you fix the same things by hand
every time. `voice-write` applies those fixes before you see the draft.

- It applies only rules you approved, never observations still waiting for review.
- Where the profile holds nothing for the language and topic, it writes normally and does not present
  the text as your voice.
- A term of the project you are in wins over your general one.
- The content comes from your request: the profile changes how the text sounds, never the facts.

## Use cases

### Write to colleagues the way you do

**Context:** Your profile holds how you address colleagues in Italian and the terms you use about software.

**Action:** Ask "Scrivi una mail breve ai colleghi: la versione 2.4 è in ambiente di test da oggi, il deploy è previsto venerdì."

**Result:** An email with your address form, your closing and your terms, and no fact beyond those of the request.

### Use a client's terms in that client's project

**Context:** Your profile says "deploy", and the glossary of the client's project says "rilascio".

**Action:** Ask for the email from inside that project.

**Result:** The email says "rilascio"; the same request outside the project gives "deploy".

## Usage

Claude loads `personal-voice:voice-write` on its own when you ask for text meant for people. You can
also ask for it: "write this in my voice". It takes no arguments: language, topic and audience come
from your request.

```text
Draft an email to our client explaining that the delivery moves to next Tuesday.
```

You get the email, in the tone your profile records for clients. When the topic or the audience is
unclear, it asks you one short question first.

After it has written for you, revising its text or closing the session starts
[`voice-learn`](../voice-learn/README.md).

## Inputs and outputs

It reads the global store in your `store_dir` directory and, when the project has one, the project
store in `.personal-voice/` at the project root. It writes to neither. The files are described in
[the store format](../../shared/store-format.md).

## Requirements

The `personal-voice` plugin, with its `store_dir` setting. Until `store_dir` is set, it tells you
once how to set it and writes the text normally.

## Limitations

- It does not apply to code, code comments, commit messages or configuration files, unless you ask
  for your voice on that specific text.
- When another skill, a template or the project's conventions fix the structure, register or terms
  of a text, those win: your profile applies only where they leave room, such as word choice within
  a sentence.
- A habit shows up in drafts only after [`voice-maintain`](../voice-maintain/README.md) made it a
  rule.
- Claude's own replies to you in the chat are not written in your voice.
