# personal-voice

Text an assistant writes for people often reads impersonal next to its author's
own writing: it carries LLM habits and lacks the author's tone, lexicon and
recurring expressions. Most people fix this by hand every time, and nothing
learns from the fixes.

`personal-voice` keeps a profile of how you write, fills it from your revisions
of drafts and from texts you wrote yourself, and applies it when Claude writes
documents, emails and messages for you. It works in any language you write in.

The profile changes only with your approval: learning records observations,
and an observation becomes a rule only after it shows up in two independent
texts and you accept it.

## Skills

| Skill | What it does |
|---|---|
| `personal-voice:voice-write` | Applies your profile when Claude writes text meant for people |
| `personal-voice:voice-learn` | Records observations from your revisions and from your own texts |
| `personal-voice:voice-maintain` | Turns observations into rules and keeps the profile small, with per-item approval |

### voice-write

Claude uses it on its own when it writes something you will send, publish or
use as your own — documents, reports, emails, messages, posts — in any
language. You can also ask for it: "write this in my voice".

Before writing, it works out the language, up to two topics and the audience
from your request. When the topic or audience is unclear, it asks you one short
question. It then reads, in order: `core.md`, the language file, the topic
files, the project glossary and document-type conventions, and up to two of
your own texts on the topic in that language. When two rules disagree, the more
specific wins: project over topic, topic over language, language over core.

It applies only rules you have approved, never pending observations. With an
empty store it writes normally and does not pretend to know your style.

When another skill or template already fixes the structure, register or terms
of the text (a client deliverable with its own style guide, a statement of
work, a corporate template), those win: your profile applies only where they
leave room, such as word choice within a sentence.

It never touches code, code comments, commit messages or configuration files,
unless you ask for your voice on that specific text. It only reads the store.

While it is loaded, it also notices when you revise something it wrote or when
you close the session, and hands over to `voice-learn`.

### voice-learn

It learns from:

- **your revisions** of text Claude wrote in the session: the version you
  actually sent, pasted back; a file Claude wrote that you edited (say so, or
  Claude Code will report the change); corrections you state, such as "I never
  write 'inoltre'";
- **texts you wrote without AI**, pasted or given as files. Short excerpts are
  kept as exemplars, at most five per topic and language, and only passages
  without client or project names: exemplars are global and guide texts in
  every project.

It records only style: tone, words, punctuation, structure, and LLM habits you
remove. It never records corrected facts, figures, dates, names or scope, and
never treats Claude's own edits of your text (a proofread, a rewrite) as your
preferences. Without the draft it does not compare anything: from a later
session, give it both versions.

It records without asking and never changes a rule. After recording you see
one line:

```
Voice profile: recorded 2 observations — global › languages/it.md (new), project › glossary.md (+1 evidence).
```

When 10 observations are pending, or the last maintenance is 30 days old, a
second line suggests running `voice-maintain`. When you close the session, it
records any revision it missed and gives a two-line recap.

The first time a project term comes up in a project, it offers to create the
project store and explains what keeping it personal or versioning it implies.

### voice-maintain

Runs only when you ask ("review my voice profile") or accept the suggestion
from `voice-learn`. It reads both stores and proposes, as a numbered list with the
evidence for each item:

- **promotions**: observations seen in two independent texts become rules; you
  can accept, reject, edit, or change their scope (global or project, file,
  language, audience). A single observation can be promoted on your explicit
  request;
- **merges** of overlapping rules, and **conflicts** between contradictory
  ones, which you settle or qualify by audience, topic or language;
- **removals** of rules that only restate what Claude does anyway;
- **reviews** of rules not reinforced for six months (a rule you keep is not
  asked about again for another six months), and deletion of single
  observations older than three months;
- **size limits**: at most 50 rules per file, five exemplars per topic and
  language, 300 words each;
- **scope moves** between the project and the global store (personal material
  never moves into a project store).

Nothing changes until you name the items to apply (`1, 3 remove, 2 keep A`). A
reply like "ok" is not an approval: it asks you for the numbers. At the end it
records the date of the run.

It also switches a project store between personal and versioned when you ask
("share the project glossary with the team"), after explaining the
implications again.

## Setup

### Store directory (`store_dir`)

The global profile lives in a directory you choose. Claude Code asks for it
when you enable the plugin; you can change it later in `/config`. Pick a place
you back up. Uninstalling the plugin never deletes it.

Until `store_dir` is set, the skills tell you how to set it and write nothing.

### Permissions

The skills write to the store with Claude Code's file tools. In manual mode,
each write asks for permission; in `acceptEdits` mode, writes outside the
project (the global store) do. To remove these prompts, add these allow rules
to your user settings (`~/.claude/settings.json`), with your own store path:

```json
{
  "permissions": {
    "allow": [
      "Read(//absolute/path/to/voice-store/**)",
      "Edit(//absolute/path/to/voice-store/**)",
      "Edit(**/.personal-voice/**)"
    ]
  }
}
```

`//` starts an absolute path; for a store under your home directory you can
write `~/path/to/voice-store/**` instead. The `Read` rule lets the skills read
the global store, which sits outside your projects; the `Edit` rules cover
writes to the global store and to project stores.

Creating a project store in a git repository edits `.git/info/exclude`. Claude
Code protects `.git/`, so that one edit asks for permission whatever your rules.

The one shell command the skills run without asking is `git rev-parse`: it
finds the project root, so a session started in a subdirectory uses the same
project store, and the exclude file's path in a linked worktree. Each skill
pre-approves it, so it asks for no permission. `git rm --cached` runs only when
you ask maintenance to stop tracking a versioned project store, with a
permission prompt.

## What the stores hold

**Global store** (the `store_dir` directory), personal to you:

- `core.md` — tone that holds in every language and topic, including tone for
  specific audiences, and LLM habits to avoid
- `languages/<code>.md` — tone for one language, and expressions you use across
  topics in that language
- `topics/<slug>.md` — lexicon for one topic (professional, hobby or personal)
- `exemplars/` — short excerpts of texts you wrote without AI
- `observations.md` — observations waiting for review

**Project store** (`.personal-voice/` in a project, optional), created only after
you confirm:

- `glossary.md` — client and project terms
- `content-types/<slug>.md` — conventions for this project's document types
- `observations.md` — project observations waiting for review

Files are Markdown. You can read and edit them yourself.

### Privacy

The global store holds excerpts of your own writing and notes on how you write.
It stays in the directory you chose and is never sent anywhere by the plugin.
Its pending observations note the path of the project a text was written in,
so that maintenance can tell projects apart; that path is never written into a
project store.

The project store holds only project material: never exemplars, and never
anything learned from personal texts. Exemplars in the global store are chosen
without client or project names; a text that has no such passage gives
observations but no exemplar. In a git repository, you choose whether
to keep it personal (the default: listed in `.git/info/exclude`, so git ignores
it) or to version it with the project. Before you choose, the skill explains
what versioning implies, including that anyone who can read the repository can
read the client terms in it.

## What to expect

Studies of style personalization report modest gains, and informal registers
are the hardest to match. The profile starts empty and fills slowly; giving the
voice-learn skill a few texts you wrote yourself is the quickest start.

The plugin learns only within a Claude Code session. Revisions you make after
the session, such as edits to an email you already sent, are not captured
unless you provide both versions.

## Installation

As a Claude Code plugin, from the `mrbogomips` marketplace:

```bash
claude plugin marketplace add MrBogomips/claude-plugins
claude plugin install personal-voice@mrbogomips
```

**Standalone skills: no, plugin only.** Install the plugin as a whole. The three skills share the store
format in `shared/store-format.md` and read the global store location from the plugin's `store_dir`
setting; installed alone, for example with `npx skills add`, they find neither, and `voice-learn` and
`voice-maintain` write nothing.

Earlier versions were published as `personal-voice@mrbogomips-tools` from `MrBogomips/claude-code`, with
the skills named `write`, `learn` and `maintain`. Version 1.0.0 renames them `voice-write`,
`voice-learn` and `voice-maintain`. Installations cannot move between marketplaces: uninstall the old
plugin and install `personal-voice@mrbogomips`. Your voice store is not touched.

## License

MIT
