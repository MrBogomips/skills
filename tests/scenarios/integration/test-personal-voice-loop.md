# Integration Test: personal-voice learning loop

## Objective
Verify the whole loop live, with the plugin loaded from the repository: a draft
with the voice-write skill, the author's revisions, observations, a repeat in a
second text, the wrap-up, maintenance, and a promoted rule that changes the
next draft.

## Setup
1. Create a scratch directory `E` with an empty `E/store` and a git project `E/proj`.
2. Set the plugin option for the session-only plugin in your user settings
   (`~/.claude/settings.json`), after backing the file up:
   `"pluginConfigs": {"personal-voice@inline": {"options": {"store_dir": "<E>/store"}}}`.
   Remove it when the test ends.
3. Run each turn from `E/proj` as a headless session, resuming the previous one
   within a phase:
   ```bash
   claude -p "<turn>" --plugin-dir <repo>/personal-voice --permission-mode default \
     --settings '{"permissions":{"allow":["Read(/<E>/store/**)","Edit(/<E>/store/**)","Edit(**/.personal-voice/**)"]}}' \
     --output-format stream-json --verbose [--resume <session id>]
   ```
   The allow rules are the ones the plugin README documents (`//` absolute paths).

## Test Cases

### Phase 1 — one session
1. "Scrivi una mail breve ai colleghi: la demo è spostata a giovedì alle 15."
2. Paste back the draft with the opener dropped and the closing changed to "Alla prossima,".
3. "Ora un'altra mail ai colleghi: la retrospettiva è confermata per venerdì alle 11."
4. "Mandata, ho solo cambiato la chiusura: 'Alla prossima,' invece di '<the draft's closing>'."
5. "Ok, per oggi chiudiamo qui. Grazie!"

**Verify**:
- [ ] Turn 1 invokes `personal-voice:voice-write`; the reply does not attribute traits to the author
- [ ] Turn 2 invokes `personal-voice:voice-learn`; `store/observations.md` gains style observations, none about the date; one notice line
- [ ] Turn 3 does not apply the pending observations
- [ ] Turn 4 raises the closing observation's evidence from 1 to 2, with two distinct text labels
- [ ] Turn 5 gives a recap of at most two lines and does not offer maintenance (thresholds not reached)
- [ ] No permission denial in any turn

### Phase 2 — new session
6. "Rivediamo il mio profilo di voce: fai la manutenzione."
7. "ok"
8. "<the promotion's item number>"

**Verify**:
- [ ] Turn 6 invokes `personal-voice:voice-maintain` and lists the closing as a PROMOTE item with both pieces of evidence; no file changes
- [ ] Turn 7 asks for item numbers; no file changes
- [ ] Turn 8 creates `store/languages/it.md` with `[it] [to colleagues]` and the closing under `## Audiences`, `evidence: 2`; the observation is removed; `last_maintenance` is today

### Phase 3 — new session
9. "Scrivi due righe ai colleghi: il server di test torna online domattina."

**Verify**:
- [ ] The draft closes with "Alla prossima,"
- [ ] Single-evidence observations are still not applied

Result on 2026-09-29: all checks passed.
