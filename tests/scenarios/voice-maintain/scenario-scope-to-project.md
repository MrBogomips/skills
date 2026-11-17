# Scenario: Scope to project, only for the current project's path

## Setup
Fixture created. `$F` must be an absolute path without symlinks, because
`git rev-parse --show-toplevel` prints the resolved path: on macOS use `/private/tmp/…` rather than
`/tmp/…`. Append three observations to the global `observations.md` before taking the `before`
fingerprint. Global sources carry the absolute path of
the project root, so the fixture's project is tagged `project: $F/project`. The second observation
comes from a different repository with the same folder name, `$F/other/project`.

```bash
cat >> "$F/store/observations.md" <<MD

### "Ordine di lavoro", not "ticket"
- kind: lexicon
- language: it
- topic: software-engineering
- audience: clients
- destination: topics/software-engineering.md › Glossary
- evidence: 2
- sources:
  - 2026-09-10 · revision · text: kickoff recap to the client · project: $F/project · "il ticket" → "l'ordine di lavoro"
  - 2026-09-24 · revision · text: weekly update to the client · project: $F/project · "i ticket aperti" → "gli ordini di lavoro aperti"

### "Pratica", not "richiesta"
- kind: lexicon
- language: it
- topic: software-engineering
- audience: clients
- destination: topics/software-engineering.md › Glossary
- evidence: 2
- sources:
  - 2026-09-11 · revision · text: status note to another client · project: $F/other/project · "la richiesta" → "la pratica"
  - 2026-09-23 · revision · text: meeting follow-up to that client · project: $F/other/project · "le richieste" → "le pratiche"

### "termine-01-scelto" in the client project
- kind: lexicon
- language: it
- topic: software-engineering
- audience: clients
- destination: topics/software-engineering.md › Glossary
- reinforces: topics/software-engineering.md › Glossary › "termine-01-scelto"
- evidence: 2
- sources:
  - 2026-09-12 · revision · text: release note to the client · project: $F/project · "termine-01-evitato" → "termine-01-scelto"
  - 2026-09-26 · revision · text: go-live email to the client · project: $F/project · "termine-01-evitato" → "termine-01-scelto"
MD
```

Working directory: `$F/project`.

## Invocation
Run the recap; then approve the scope item by its number.

## Expected Behavior
- "Ordine di lavoro": every source carries the current project root's path and it reinforces
  nothing, so it is proposed as a MOVE to the current project's store (`.personal-voice/glossary.md`)
- "Pratica": every source carries `$F/other/project`, a different repository with the same folder
  name, so no MOVE; the recap adds a one-line note naming that path, and the promotion is proposed
  as usual
- The reinforcing observation: no MOVE, because the rule's earlier evidence has no project
  provenance; a note, and a REINFORCE item as usual

## Acceptance Criteria
- [ ] One MOVE (scope to project) item for "Ordine di lavoro", with destination `project › glossary.md`
- [ ] No MOVE item for "Pratica", although its tag ends in the same folder name `project`
- [ ] No MOVE item names any store other than `$F/project/.personal-voice/`
- [ ] The recap has a note for "Pratica" naming `$F/other/project`, and a note for the reinforcing observation
- [ ] The reinforcing observation is a REINFORCE item, not a MOVE
- [ ] After approving the MOVE: `.personal-voice/glossary.md` gains an `[it]` rule about "ordine di lavoro" with `evidence: 2`; the observation is gone from the global `observations.md`; no global rule file gains it
- [ ] `grep -rn "$F" "$F/project/.personal-voice"` prints nothing: no absolute path reaches the project store
- [ ] No file is created outside `$F/store` and `$F/project/.personal-voice/`
