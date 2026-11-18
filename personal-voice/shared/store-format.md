# Voice store format

The single definition of where the voice profile lives, what each file holds,
how entries are written, and where each observation or rule goes. The voice-write,
voice-learn and voice-maintain skills all follow this file.

## Stores

| Store | Location | Holds |
|---|---|---|
| Global | The directory set in the plugin's `store_dir` option. The skill that sent you here gives you the path | The author's tone, lexicon and exemplars. Personal to the author |
| Project | `.personal-voice/` at the project root (see below) | Project material only: client and project terms, document-type conventions |

**Project root**: the directory `git rev-parse --show-toplevel` prints, or the
working directory outside git. The skills pre-approve `git rev-parse`, so this
asks for no permission. A session started in a subdirectory of the repository
uses the same root, so it finds the existing store and never creates a second
one in the subdirectory.

If the global path is empty, or still contains the text
`user_config.store_dir` (the placeholder was not replaced), the store is not
configured: tell the user to set **Voice store directory** in `/config` (or
when enabling the plugin) and write nothing.

The global store never lives inside the plugin's installation or data
directory. Uninstalling the plugin leaves it in place.

## Layout

```
<global store>/
├── core.md                  tone for every language and topic
├── languages/<code>.md      tone for one language, cross-topic expressions
├── topics/<slug>.md         lexicon for one topic
├── exemplars/<slug>.<code>.<nn>.md   texts the author wrote without AI
└── observations.md          pending observations; last maintenance date

<project root>/.personal-voice/
├── glossary.md              client and project terms
├── content-types/<slug>.md  conventions for this project's document types
└── observations.md          pending project observations
```

Create a file or folder only when the first entry for it is written. Recording
an observation creates `observations.md` at most; a rule file is created when
maintenance promotes its first rule.

## Naming and language

- **Language codes**: ISO 639-1, lowercase (`en`, `it`, `de`).
- **Topic slugs**: kebab-case English nouns (`software-engineering`, `cycling`,
  `family`). Reuse an existing slug before creating a new one.
- **Dates**: `YYYY-MM-DD`.
- **Store language**: frontmatter, headings and rule text are in English.
  Quoted expressions and exemplars stay verbatim in their original language,
  inside double quotes.

## Files

Every file starts with a small YAML frontmatter. Rules are the `- ` bullets
under the headings listed for the file; each bullet is one rule.

### `core.md`

```markdown
---
kind: core
---
## Tone
## Audiences
## Avoid
## Expressions
```

`Tone`: register, rhythm, sentence length, punctuation habits that hold in
every language. `Expressions`: words or phrases the author uses in every
language and topic (rare). `Audiences`: tone for a specific audience. `Avoid`: LLM habits
the author removes in any language (stock openers, rule-of-three lists, forced
contrasts, closing summaries).

### `languages/<code>.md`

```markdown
---
kind: language
language: it
---
## Tone
## Audiences
## Avoid
## Signature expressions
```

`Tone` and `Audiences`: punctuation, register and address forms for this
language. `Avoid`: LLM habits typical of this language. `Signature
expressions`: words and phrases the author uses across topics in this language.

### `topics/<slug>.md`

```markdown
---
kind: topic
topic: software-engineering
personal: false
description: Professional texts about building and running software
---
## Glossary
## Preferred expressions
## Borrowed expressions
```

`Glossary`: the topic's most used terms and the author's choice among
synonyms. `Preferred expressions`: technical and jargon phrasing. `Borrowed
expressions`: expressions from other languages the author uses as a quirk or
identity. `personal: true` marks a personal topic (family, friends, private
life); nothing from a personal topic ever enters a project store.

### `exemplars/<slug>.<code>.<nn>.md`

```markdown
---
kind: exemplar
topic: software-engineering
language: it
audience: colleagues
source: status email to the team
added: 2026-01-15
words: 180
---
<verbatim excerpt, at most 300 words>
```

Only texts the author wrote without AI. At most five per topic and language.
`nn` is a two-digit sequence number within the topic and language.

### `observations.md` (global and project)

```markdown
---
kind: observations
store: global
last_maintenance: 2026-08-30
---
```

`store` is `global` or `project`. `last_maintenance` appears only in the
global file; maintenance writes it at the end of each run. Each observation is
one `###` section (see Observation entries). The number of `###` sections is
the pending count.

### `.personal-voice/glossary.md`

```markdown
---
kind: glossary
---
## Terms
```

### `.personal-voice/content-types/<slug>.md`

```markdown
---
kind: content-type
content_type: status-report
---
## Conventions
```

Use the slug `general` for conventions that hold for every document in the
project.

## Rule entries

```
- [qualifiers] Rule text in English, quoting "verbatim expressions". (evidence: N, reinforced: YYYY-MM-DD)
- [qualifiers] A rule the author kept at a stale review. (evidence: N, reinforced: YYYY-MM-DD, reviewed: YYYY-MM-DD)
```

Qualifiers, in this order, each only when the rule depends on it:

| Qualifier | Form | Example |
|---|---|---|
| Language | `[<code>]` | `[it]` |
| Audience | `[to <audience>]` | `[to clients]`, `[to family]` |
| Topic (tone rules only) | `[topic: <slug>]` | `[topic: cycling]` |

`evidence` is the number of independent texts or sessions that showed the
trait. `reinforced` is the date of the most recent one. `reviewed` appears only
after the author kept the rule at a stale review, and is the date of that
review; the stale check measures age from the later of `reinforced` and
`reviewed`. Entries in `languages/<code>.md` always carry that language's
qualifier.

Glossary entries use the same form, stating the preferred term, the terms to
avoid and the meaning:

```
- [it] Use "rilascio", not "deploy", for a production release; the client's term. (evidence: 2, reinforced: 2026-09-10)
```

## Observation entries

```markdown
### Avoid "inoltre"
- kind: lexicon
- language: it
- topic: software-engineering
- audience: colleagues
- destination: languages/it.md › Avoid
- evidence: 1
- sources:
  - 2026-09-29 · revision · text: status email to the team · project: /path/to/example-portal · "Inoltre, il rilascio è pronto." → "E il rilascio è pronto."
```

- **Heading**: the trait in a few English words.
- **kind**: `tone` or `lexicon`.
- **language**: a code, or `any` when the trait holds across languages.
- **topic**: a slug, or `any`.
- **audience**: who the text was for, or `unknown`.
- **destination**: the file and heading routing selects; maintenance writes the
  rule there.
- **sources**: one line per independent text: date, source kind (`revision`,
  `spoken correction` or `own text`), a short label for the text, the project
  tag when the global store records a text written in a project, and
  either `"before" → "after"` excerpts or the quoted trait. Give each text a label
  that tells it apart from other texts (what it is, for whom, when). Two lines
  with the same text label count as one piece of evidence.
- **evidence**: the number of distinct text labels in `sources`.
- **reinforces**: only when the trait matches a rule already in the store: the
  rule's file, heading and first words, such as
  `languages/it.md › Avoid › "Inoltre" at the start`. Maintenance then adds
  this evidence to the rule and updates its `reinforced` date, instead of
  proposing a new rule. `destination` is the same file and heading.

A trait that matches a pending observation adds a line to that observation's
`sources`; it never creates a second observation.

**Project tag**: `project: <absolute path of the project root>`, written exactly
as `git rev-parse --show-toplevel` prints it (the working directory outside
git), for example `project: /path/to/example-portal`. Only sources in the global store carry
it; there it tells projects apart even when two repositories share a folder
name (`backend`, `docs`). Sources in a project store carry no project tag: the
store itself identifies the project, and a personal absolute path must never
land in a store that may be versioned. When an entry moves into a project
store, drop the tag from its sources.

## Routing

Answer these questions in order for every observation and rule. The same entry
gets the same destination every time.

0. **Personal?** If it comes from a personal text (a personal topic, or an
   audience such as family or friends), it goes to the global store. Skip
   question 1.
1. **Project?** Would it hold in another project? If not, or if uncertain, it
   goes to the project store: lexicon to `glossary.md`, tone and structure to
   `content-types/<slug>.md`. Stop here.
2. **Tone or lexicon?** Tone is how the text sounds: register, address forms,
   greetings and closings, rhythm, punctuation, structure, LLM habits. Lexicon
   is which words it uses: terms, jargon, expressions, borrowings.
3. **What does it depend on?**

| Kind | Depends on | Destination |
|---|---|---|
| Tone | neither | `core.md` |
| Tone | language | `languages/<code>.md` |
| Tone | topic | `core.md`, or the language file if also language-dependent, with `[topic: <slug>]` |
| Lexicon | topic | `topics/<slug>.md`, with `[<code>]` when it depends on the language |
| Lexicon | language only | `languages/<code>.md` › Signature expressions |
| Lexicon | neither | `core.md` › Expressions (rare: words usually belong to a language) |

Audience never selects a file: it becomes a `[to <audience>]` qualifier.

When the destination is the project store and none exists, the voice-learn skill
offers to create one (see `project-store-init.md`, next to this file). If the user declined
it in this session, do not record project observations.

### Worked examples

| Case | Answers | Destination |
|---|---|---|
| First observation for a topic with no file | — | `observations.md`, `topic:` set; no topic file until a rule is promoted |
| How the author addresses clients | 2 tone; 3 neither, audience | `core.md` › Audiences, `[to clients]` |
| Terms the author uses in software engineering | 2 lexicon; 3 topic | `topics/software-engineering.md` |
| Writes "deploy", not "rilascio", in Italian software texts | 2 lexicon; 3 topic and language | `topics/software-engineering.md`, `[it]` |
| A literary Italian expression used on several topics | 2 lexicon; 3 language only | `languages/it.md` › Signature expressions |
| Replaces a term with the client's own, in that client's project | 1 no | `.personal-voice/glossary.md` |
| A message to a family member, written inside a project | 0 personal | global store, never `.personal-voice/` |
| Closing informal Italian emails to colleagues | 2 tone; 3 language, audience | `languages/it.md` › Audiences |

The last rule, once promoted, reads:

```
- [it] [to colleagues] Close informal emails with "Un saluto e a presto", never "Cordiali saluti". (evidence: 3, reinforced: 2026-09-12)
```

## Limits

- At most 50 rules per rule file. Maintenance keeps every file at or below it.
- At most five exemplars per topic and language, each at most 300 words.
