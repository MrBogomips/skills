# Recording observations

## 1. Find where each trait goes

Route each trait with the store format's Routing section. For each
destination store, read its `observations.md` and the destination rule file.

## 2. Merge before adding

- **Matches a pending observation** (the same habit, however it was worded):
  add a line to its `sources` if this text's label is not there yet, and set
  `evidence` to the number of distinct labels. Do not create a second
  observation.
- **Matches a rule** in the destination file: record a reinforcing
  observation with `reinforces:` set, or add a source to the existing
  reinforcing observation for that rule. Never edit the rule itself.
- **New**: append a `###` section at the end of `observations.md`, in the
  format of the store format's Observation entries.

Create `observations.md` with its frontmatter if it does not exist.

## 3. Project destinations

When routing sends a trait to the project store, look for `.personal-voice/`
at the project root the store format defines, not in the working directory:

- `.personal-voice/` exists → record there.
- It does not exist and the author declined it earlier in this session → drop
  the trait.
- Otherwise → record the global traits first, then offer the project store as
  the Project store initialization (`shared/project-store-init.md`)
  describes. Record the
  project traits only if the author creates it.

Never send a trait from a personal text to the project store.

Project tags follow the store format: a source recorded in the global store
for a text written in a project carries `project: <absolute path of the project
root>`; a source recorded in the project store carries no project tag.

## 4. Notice

After writing, show one line in the language of the conversation, naming how
many observations were recorded and where:

```
Voice profile: recorded 2 observations — global › languages/en.md (new), project › glossary.md (+1 evidence).
```

Nothing else about the recording, unless the author asks.

## 5. Maintenance suggestion

Then check two thresholds:

- the pending observations in the global and project stores (the `###`
  sections of both `observations.md` files) total 10 or more;
- the global `last_maintenance` date is 30 or more days old, or it is missing
  and the oldest pending observation is 30 or more days old.

If either holds, add one line after the notice, for example:

```
12 observations are pending (last review: 2026-08-20). Run personal-voice:voice-maintain when you have a moment.
```

Never run maintenance yourself.
