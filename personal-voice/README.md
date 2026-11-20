---
summary: Keeps a profile of how you write, learns it from your revisions and your own texts, and applies it when Claude writes documents, emails and messages for you.
---

# personal-voice

`personal-voice` keeps a profile of how you write, fills it from your revisions of drafts and from
texts you wrote yourself, and applies it when Claude writes documents, emails and messages for you.
It works in any language you write in, and the profile changes only with your approval.

## Why

Text an assistant writes for people often reads impersonal next to its author's own writing: it
carries LLM habits and lacks the author's tone, lexicon and recurring expressions. Most people fix
this by hand every time, and nothing learns from the fixes.

- Your fixes are recorded while you work, without questions.
- An observation becomes a rule only after it shows up in two independent texts and you accept it.
- The profile is Markdown files in a directory you choose: you can read and edit them yourself.
- Client and project terms stay in a store of their project, apart from your personal profile.

## Included components

| Skill | What it does |
|---|---|
| [`voice-write`](skills/voice-write/README.md) | Applies your profile when Claude writes text meant for people |
| [`voice-learn`](skills/voice-learn/README.md) | Records observations from your revisions and from your own texts |
| [`voice-maintain`](skills/voice-maintain/README.md) | Turns observations into rules and keeps the profile small, with per-item approval |

## Installation

As a Claude Code plugin, from the `mrbogomips` marketplace:

```bash
claude plugin marketplace add MrBogomips/claude-plugins
claude plugin install personal-voice@mrbogomips
```

**Standalone skills: no, plugin only.** Install the plugin as a whole. The three skills share the
store format in `shared/store-format.md` and read the global store location from the plugin's
`store_dir` setting; installed alone, for example with `npx skills add`, they find neither, and
`voice-learn` and `voice-maintain` write nothing.

If you installed `personal-voice@mrbogomips-tools`, where the skills were named `write`, `learn` and
`maintain`: installations cannot move between marketplaces, so uninstall the old plugin and install
`personal-voice@mrbogomips`. Your voice store is not touched.

## Quick start

Set the voice store directory when Claude Code asks for it, then give Claude a few texts you wrote
yourself:

```text
Here are three emails I wrote to clients myself, no AI involved. Learn my style from them.
```

`voice-learn` answers with one line that says how many observations it recorded and where.

## Configuration

`store_dir` (**Voice store directory**, required, no default): the directory of your global profile.
Claude Code asks for it when you enable the plugin; you can change it later in `/config`. Pick a
place you back up. Uninstalling the plugin never deletes it.

Until `store_dir` is set, the skills tell you how to set it and write nothing to the profile.

To remove the permission prompts on the store, see [Permissions](#permissions).

## Limitations

- Studies of style personalization report modest gains, and informal registers are the hardest to
  match.
- The profile starts empty and fills slowly; giving `voice-learn` a few texts you wrote yourself is
  the quickest start.

## Permissions

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

## Privacy

The global store holds excerpts of your own writing and notes on how you write.
It stays in the directory you chose and is never sent anywhere by the plugin.
Its pending observations note the path of the project a text was written in,
so that maintenance can tell projects apart; that path is never written into a
project store.

The project store holds only project material, never excerpts of personal
texts. In a git repository you choose whether to keep it personal (the default)
or to version it with the project, where anyone who can read the repository can
read its client terms.

## License

MIT
