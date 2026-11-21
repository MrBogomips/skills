---
summary: Keeps a profile of how you write, learns it from your revisions and your own texts, and applies it when Claude writes documents, emails and messages for you.
---

# personal-voice

`personal-voice` keeps a profile of how you write, builds it from your draft revisions and your
own texts, and applies it when Claude writes documents, emails and messages for you. It works in
any language, and the profile changes only with your approval.

## Why

Assistant-written text often sounds impersonal next to your own writing: it carries LLM habits and
misses your tone, vocabulary and recurring expressions. You end up fixing drafts by hand every
time, and nothing learns from those revisions.

- The plugin records your revisions while you work, without asking questions.
- An observation becomes a rule only after it appears in two independent texts and you approve it.
- The profile is stored as Markdown files in a directory you choose, so you can read and edit them
  yourself.
- Client and project terms stay in a project store, separate from your personal profile.

## Included components

| Skill | What it does |
|---|---|
| [`voice-write`](skills/voice-write/README.md) | Applies your profile when Claude writes text for human readers |
| [`voice-learn`](skills/voice-learn/README.md) | Records observations from your revisions and your own texts |
| [`voice-maintain`](skills/voice-maintain/README.md) | Turns observations into rules and keeps the profile small, with per-item approval |

## Installation

Install `personal-voice` as a Claude Code plugin from the `mrbogomips` marketplace:

```bash
claude plugin marketplace add MrBogomips/claude-plugins
claude plugin install personal-voice@mrbogomips
```

The skills do not work standalone; install the plugin as a whole. They share the store format in
`shared/store-format.md` and read the global store location from the plugin's `store_dir` setting.
If you install them individually (for example, with `npx skills add`), they find neither, and
`voice-learn` and `voice-maintain` write nothing.

If you previously installed `personal-voice@mrbogomips-tools` (where the skills were named `write`,
`learn` and `maintain`), uninstall it and install `personal-voice@mrbogomips`, because
installations cannot move between marketplaces. Your voice store remains untouched.

## Quick start

Set the voice store directory when Claude Code prompts you for it, then give Claude a few texts
you wrote yourself:

```text
Here are three emails I wrote to clients myself, no AI involved. Learn my style from them.
```

`voice-learn` replies with a single line reporting how many observations it recorded and where.

## Configuration

`store_dir` (**Voice store directory**, required, no default): the directory that holds your global
profile. Claude Code prompts you for it when you enable the plugin, and you can change it later in
`/config`. Pick a location you back up; uninstalling the plugin never deletes it.

Until `store_dir` is set, the skills explain how to configure it and write nothing to the profile.

To avoid permission prompts for the store, see [Permissions](#permissions).

## Limitations

- Studies of style personalization report modest gains, and informal registers are the hardest to
  match.
- The profile starts empty and grows slowly; giving `voice-learn` a few texts you wrote yourself
  is the quickest way to get started.

## Permissions

The skills write to the store using Claude Code's file tools. In manual mode, every write prompts
for permission; in `acceptEdits` mode, writes outside the project (to the global store) still do.
To stop these prompts, add the following allow rules to your user settings
(`~/.claude/settings.json`), replacing the example path with your own store path:

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

`//` denotes an absolute path; for a store under your home directory, you can use
`~/path/to/voice-store/**` instead. The `Read` rule lets the skills read the global store outside
your projects, and the `Edit` rules cover writes to both the global store and project stores.

Creating a project store in a git repository edits `.git/info/exclude`. Because Claude Code
protects `.git/`, that edit always prompts for permission regardless of your allow rules.

## Privacy

The global store holds excerpts of your own writing and notes on how you write. It stays in the
directory you choose, and the plugin never sends it anywhere. Its pending observations record the
path of the project where a text was written, so maintenance can tell projects apart; that path is
never written to a project store.

The project store holds only project material, never excerpts of personal texts. In a git
repository, you choose whether to keep it local (the default) or track it with the project, where
anyone with read access to the repository can see its client terms.

## License

MIT
